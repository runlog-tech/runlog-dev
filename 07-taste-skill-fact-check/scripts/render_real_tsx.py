#!/usr/bin/env python3
"""
render_real_tsx.py - Renders the ACTUAL LLM-generated .tsx files (not hand-mocked
HTML) via headless Chrome, using native ES module imports (esm.sh) + Babel standalone
for JSX/TS stripping only (imports are left intact for the browser to resolve).

This replaces render_ui_screenshots.py, which contained hand-typed HTML mockups that
did not match the real generated code at all -- confirmed by diffing against
benchmark_results/full/*.tsx (2026-09-23 validator pass).

Usage: python3 render_real_tsx.py <path/to/real_file.tsx> <output.png>
"""

import sys
import re
import subprocess
import tempfile
from pathlib import Path

CHROME = "/usr/bin/google-chrome-stable"


def extract_code(raw: str) -> str:
    """Strip markdown fence + any prose the model added before/after the code block.

    Some real generations open with a short untagged ``` block (a "reading this
    as..." planning preamble, e.g. `DEALS_VARIANCE: 6 | MOTION_INTENSITY: 4 ...`)
    before the real ```tsx code fence -- picking the FIRST fenced block (the old
    behavior) grabbed that preamble instead of the component. Real code is always
    the largest fenced block in the file, so pick the longest match instead of
    the first one.
    """
    matches = re.findall(r"```(?:tsx|jsx|ts|js)?\n(.*?)```", raw, re.DOTALL)
    code = max(matches, key=len) if matches else raw  # no fence found -- assume whole file is code
    return _patch_phosphor_imports(code)


def _patch_phosphor_imports(code: str) -> str:
    """Real generations repeatedly named-import icons that don't exist in
    @phosphor-icons/react (e.g. ChevronRight, which is CaretRight in Phosphor) --
    a genuine model mistake, not a rendering-pipeline bug. A missing named export
    is a hard ESM link error the browser can't recover from, so rewrite the import
    to a namespace import with a null-component fallback per name. This only
    prevents a crash for preview purposes; it doesn't touch the model's actual
    design/layout code."""
    pattern = re.compile(r'import\s*\{([^}]+)\}\s*from\s*["\']@phosphor-icons/react["\'];?', re.DOTALL)

    def repl(match):
        names = [n.strip().split(" as ")[-1].strip() for n in match.group(1).split(",") if n.strip()]
        orig_names = [n.strip() for n in match.group(1).split(",") if n.strip()]
        lines = ['import * as __PhosphorIcons from "@phosphor-icons/react";']
        for orig, local in zip(orig_names, names):
            source_name = orig.split(" as ")[0].strip()
            lines.append(f'const {local} = __PhosphorIcons.{source_name} || (() => null);')
        return "\n".join(lines)

    return pattern.sub(repl, code)


def build_html(code: str) -> str:
    # Real files use bare-specifier imports (react, motion/react, @phosphor-icons/react).
    # Native browser ES modules + an import map resolve these against esm.sh, so Babel
    # only needs to strip JSX/TypeScript syntax -- NOT touch the import statements.
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Real generation render</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <script src="https://unpkg.com/@babel/standalone@7/babel.min.js"></script>
  <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=Geist:wght@400;500;600;700&display=swap" rel="stylesheet">
  <style>body {{ font-family: 'Plus Jakarta Sans', sans-serif; background: #030712; }}</style>
  <script type="importmap">
  {{
    "imports": {{
      "react": "https://esm.sh/react@18",
      "react/jsx-runtime": "https://esm.sh/react@18/jsx-runtime",
      "react-dom": "https://esm.sh/react-dom@18",
      "react-dom/client": "https://esm.sh/react-dom@18/client",
      "motion/react": "https://esm.sh/motion@11/react?deps=react@18,react-dom@18",
      "framer-motion": "https://esm.sh/framer-motion@11?deps=react@18,react-dom@18",
      "@phosphor-icons/react": "https://esm.sh/@phosphor-icons/react@2?deps=react@18,react-dom@18",
      "lucide-react": "https://esm.sh/lucide-react@0.400?deps=react@18,react-dom@18",
      "next/font/google": "data:text/javascript,export function Geist()%7Breturn%7BclassName:'',style:%7B%7D%7D%7D%0Aexport function Geist_Mono()%7Breturn%7BclassName:'',style:%7B%7D%7D%7D%0Aexport function Inter()%7Breturn%7BclassName:'',style:%7B%7D%7D%7D%0Aexport default %7B%7D",
      "next/link": "data:text/javascript,import React from 'https://esm.sh/react@18';export default function Link(props)%7Breturn React.createElement('a', props, props.children)%7D",
      "next/image": "data:text/javascript,import React from 'https://esm.sh/react@18';export default function Image(props)%7Breturn React.createElement('img', props)%7D"
    }}
  }}
  </script>
</head>
<body>
  <div id="root">Loading&hellip;</div>
  <div id="debug-error" style="position:fixed;inset:0;background:#000;color:#f87171;font-family:monospace;font-size:16px;padding:24px;white-space:pre-wrap;display:none;z-index:999;"></div>
  <script id="raw-source" type="text/plain">{code}</script>
  <script type="module">
    function showError(e) {{
      const box = document.getElementById('debug-error');
      box.style.display = 'block';
      box.textContent = (e && e.stack) ? e.stack : String(e);
    }}
    window.addEventListener('error', (e) => showError(e.error || e.message));
    window.addEventListener('unhandledrejection', (e) => showError(e.reason));

    try {{
      const raw = document.getElementById('raw-source').textContent;
      const transformed = Babel.transform(raw, {{
        presets: [['react', {{ runtime: 'automatic' }}], 'typescript'],
        filename: 'component.tsx',
        sourceType: 'module',
      }}).code;

      const blob = new Blob([transformed], {{ type: 'text/javascript' }});
      const url = URL.createObjectURL(blob);
      const mod = await import(url);
      const Component = mod.default;
      if (!Component) throw new Error('No default export found in transformed module');

      const React = (await import('react')).default;
      const {{ createRoot }} = await import('react-dom/client');
      createRoot(document.getElementById('root')).render(React.createElement(Component));

      // Signal readiness for the screenshot script (after paint + any mount effects).
      window.__renderDone = true;
    }} catch (e) {{
      showError(e);
    }}
  </script>
</body>
</html>
"""


def main():
    if len(sys.argv) != 3:
        print("Usage: python3 render_real_tsx.py <input.tsx> <output.png>")
        sys.exit(1)

    in_path, out_path = Path(sys.argv[1]), Path(sys.argv[2])
    raw = in_path.read_text(encoding="utf-8")
    code = extract_code(raw)

    html = build_html(code)
    with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False) as f:
        f.write(html)
        html_path = f.name

    cmd = [
        CHROME,
        "--headless=new",
        "--disable-gpu",
        "--no-sandbox",
        "--window-size=1920,1080",
        "--virtual-time-budget=6000",  # allow time for ESM fetch + React mount
        f"--screenshot={out_path.resolve()}",
        html_path,
    ]
    print(f"Rendering {in_path.name} -> {out_path}")
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    if result.returncode != 0:
        print("Chrome stderr:", result.stderr[-2000:])
        sys.exit(1)
    print(f"Saved {out_path}")


if __name__ == "__main__":
    main()
