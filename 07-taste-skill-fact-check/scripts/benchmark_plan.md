# Video 14 Benchmark Plan: Fact-Checking "Anti-Slop" Skills

**Execution status (2026-09-23): complete.** All 15 cells of the matrix below (5 arms x 3 briefs) were run for real via `run_full_benchmark.py` and graded via `eval_grader.py` — the plan as originally written was sound, only its execution was missing when this file was first drafted (only 3 of 15 cells had real data). See `memory/video_ideas.md` entry 18 for the full trail, `benchmark_results/full/` for raw output, and `script.md` Sections 03-05 for the narration built on these real numbers.

## 1. Core Objectives
Prove with deterministic receipts whether the viral 1,206-line `taste-skill` v2:
1. Actually prevents AI slop compared to naked Claude Code.
2. Respects its own 50+ negative micro-bans under real code-generation load.
3. Faithfully obeys the three 1–10 dials (`VARIANCE`, `MOTION_INTENSITY`, `VISUAL_DENSITY`).
4. Justifies its 21,780-token context tax versus a 50-token lean design guardrail.

---

## 2. Experimental Arms (5-Arm Matrix)

| Arm ID | Configuration | Prompt Injection Size | Target Dials |
|---|---|---|---|
| **Arm A (Naked)** | Standard model, zero design guidance | 0 tokens | N/A |
| **Arm B (Taste-v2 Default)** | Full 1,206-line `SKILL.md` | ~21,780 tokens | `8 / 6 / 4` (Default) |
| **Arm C (Taste-v2 Low)** | Full `SKILL.md` with low dials | ~21,780 tokens | `2 / 2 / 2` (Static/Predictable) |
| **Arm D (Taste-v2 Max)** | Full `SKILL.md` with max dials | ~21,780 tokens | `9 / 9 / 8` (Kinetic/Asymmetric) |
| **Arm E (Lean Directive)** | 3-line RUNLOG Anti-Slop Directive | ~52 tokens | N/A |

### The Lean Directive (Arm E):
```markdown
DESIGN RULES:
1. Theme: Dark zinc-950/charcoal (#09090b), single accent color, no purple mesh gradients.
2. Layout: Asymmetric 2-column or staggered layout. NEVER use 3 equal feature cards.
3. Content & Motion: Real technical terminology, no startup buzzwords (seamless, elevate). Micro-interactions via CSS transforms only.
```

---

## 3. Standardized Test Briefs

### Brief 1: B2B Developer Tool (The Slop Trap)
> "Build a responsive landing page component in React + Tailwind for 'Litestream-S3', a developer tool that streams SQLite database backups to S3 in real time. Include a hero section with primary action, an architecture/capabilities breakdown, a live replication metrics preview card, and a technical CTA."

*Why this brief:* Classic trigger for AI slop: models love adding 3 equal feature cards with icons, fake "99.99% uptime" stats, centered purple gradients, and div-based fake terminal mocks.

### Brief 2: Systems Engineer Portfolio
> "Build a personal portfolio landing page for an ex-Google distributed systems engineer who specializes in Raft consensus algorithms and high-throughput storage engines. Needs an intro, selected architecture papers, and contact section."

*Why this brief:* High risk for numbered section eyebrows (`001 / WORK`), middle-dot lists (`Raft · Go · Rust · Distributed`), and rotated text labels.

### Brief 3: Interactive Query Heatmap Component
> "Build an interactive query latency heatmap widget in React + Tailwind. Shows 24-hour P99 query latency buckets with hover inspection and animated filtering."

*Why this brief:* Specifically tests whether `MOTION_INTENSITY` produces real advanced motion (GSAP/physics) or generic `transition: all 300ms`.

---

## 4. Automated Grader Schema (`eval_grader.py`)

Each generated output is scored by an automated AST/regex inspection script verifying:

| Grader Rule | Source in `taste-skill` | Pass Condition |
|---|---|---|
| `no_em_dashes` | §9.G (Strict Ban) | Count of `—` is exactly 0 |
| `no_middle_dot_spam` | §9.F (Rationed) | No line contains >1 `·` |
| `no_numbered_eyebrows` | §9.F (Banned) | Zero matches for `(0\d\s*[/·]\|\b00\d\b)` in labels |
| `no_version_labels` | §9.F (Banned) | No `v0.`, `v1.`, `BETA`, `ALPHA` in hero eyebrows |
| `no_3_column_cards` | §9.C (Banned) | No `grid-cols-3` containing identical card children |
| `no_pure_black` | §9.A (Banned) | No `#000000` or `#000` in styles |
| `no_buzzwords` | §9.D (Banned) | Zero occurrences of `seamless`, `elevate`, `revolutionize` |
| `no_fake_terminal` | §9.E / §9.F (Banned) | No div-simulated terminal mockup with fake dots |
| `motion_dial_compliance`| §7 (Technical Ref) | High motion must use GSAP or spring animation; low motion must be static |
