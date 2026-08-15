import re
from datetime import date
from pathlib import Path

from mcp.server.mcpserver import MCPServer

mcp = MCPServer("project-memory")


def _find_table(markdown: str, columns: list[str]) -> tuple[list[str], list[list[str]]]:
    """Locate the first GFM table whose header matches `columns` and parse it into rows."""
    lines = markdown.splitlines()
    for i, line in enumerate(lines):
        if not line.strip().startswith("|"):
            continue
        header = [c.strip() for c in line.strip().strip("|").split("|")]
        if header != columns:
            continue
        # next line must be the separator row (---|---|...)
        if i + 1 >= len(lines) or not re.match(r"^\|?[\s:-]+\|", lines[i + 1]):
            continue
        rows = []
        for row_line in lines[i + 2 :]:
            if not row_line.strip().startswith("|"):
                break
            cells = [c.strip() for c in row_line.strip().strip("|").split("|")]
            rows.append(cells)
        return header, rows
    raise ValueError(f"No table with header {columns} found")


@mcp.tool()
def list_pending_decisions(repo_path: str) -> list[dict[str, str]]:
    """List the open decisions tracked in a repo's memory/pending_decisions.md."""
    path = Path(repo_path) / "memory" / "pending_decisions.md"
    if not path.exists():
        raise FileNotFoundError(f"No memory/pending_decisions.md at {repo_path}")
    header, rows = _find_table(
        path.read_text(),
        ["Decision", "Current setting", "Trigger to act", "Direction"],
    )
    return [dict(zip(header, row)) for row in rows]


@mcp.tool()
def log_experiment(
    repo_path: str,
    slug: str,
    branch: str,
    hypothesis: str,
    ctr_target: str = "",
    avd_target: str = "",
) -> str:
    """Append a new pre-registered experiment row to a repo's memory/experiments.md."""
    path = Path(repo_path) / "memory" / "experiments.md"
    if not path.exists():
        raise FileNotFoundError(f"No memory/experiments.md at {repo_path}")

    text = path.read_text()
    header, rows = _find_table(
        text,
        [
            "#",
            "Slug",
            "Branch",
            "Publish date",
            "Hypothesis",
            "CTR target",
            "AVD target",
            "Actual CTR",
            "Actual AVD",
            "30d views",
            "vs. median",
            "Verdict",
        ],
    )
    next_num = str(len(rows) + 1)
    new_row = (
        f"| {next_num} | {slug} | {branch} | {date.today().isoformat()} "
        f"| {hypothesis} | {ctr_target} | {avd_target} | — | — | — | — | pending |"
    )

    lines = text.splitlines()
    # find the last row of this table and insert after it
    for i, line in enumerate(lines):
        if line.strip().startswith("| #"):
            insert_at = i + 2 + len(rows)
            lines.insert(insert_at, new_row)
            break
    path.write_text("\n".join(lines) + "\n")
    return f"Logged experiment #{next_num} ({slug}) to {path}"


if __name__ == "__main__":
    mcp.run()
