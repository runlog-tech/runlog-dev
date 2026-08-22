---
description: Classify session learnings and route them to the right memory file, not CLAUDE.md by default
allowed-tools: Read, Edit, Glob, Grep
---

Review this session for anything worth remembering — a fact, a decision, a bug fix, a new lesson. For each candidate, classify it before writing anything, and never default to appending to `CLAUDE.md`.

## Step 1: Classify each candidate

Ask, for every candidate item, in order:

1. **Is it true right now, and would a fresh session need it immediately** (a config value, a threshold, a locked palette hex, a repo layout fact, a standing rule)? → **standing fact**.
2. **Is it a decision that isn't fully settled, or has a real trigger to revisit it later**? → **open decision**.
3. **Is it a decision that's settled, with a "why" worth keeping** (verification trail, rejected alternatives, the reasoning that led here)? → **decision record**.
4. **Is it just "what happened"** — a bug found and fixed, a build step completed, a status update with no standing consequence once read? → **changelog entry**, and ask whether it's worth keeping at all once the underlying work is committed. Git history and commit messages already cover most of this — don't duplicate them into a memory file by default.

If an item doesn't fit any of these, it likely isn't worth saving — say so instead of forcing it in somewhere.

## Step 2: Route by classification

- **Standing fact** → `memory/current_state.md`. Edit the existing line in place if it updates something already there; add a new line under the right section if it's genuinely new. Never let a standing fact carry a "why" or a date — that belongs in the decision record, not here.
- **Open decision** → `memory/pending_decisions.md`. One row: current setting, the trigger to act, the direction. No narrative trail.
- **Decision record** → a dated entry in `memory/video_ideas.md` (if it's about a specific video) or a new dated section in the relevant memory file. This is the one place narrative and rationale genuinely belong.
- **Changelog entry** → `memory/session_history.md`, and only if it's not already fully recoverable from `git log`. Default to *not* saving these unless there's a real reason a future session would need the summary rather than the commit.
- **CLAUDE.md itself** → only touch it if a *pointer* needs to change (a new memory file was created, a non-negotiable rule changed, a file this repo relies on moved). Never write a fact or a "why" directly into `CLAUDE.md` — if you're about to, it belongs in one of the files above instead.

## Step 3: Show the routing table before writing anything

```
| Item | Classification | Destination |
|------|----------------|-------------|
| ... | standing fact / open decision / decision record / changelog / not worth saving | memory/current_state.md / pending_decisions.md / video_ideas.md / session_history.md / CLAUDE.md / (skip) |
```

## Step 4: Apply with approval

Ask before writing. Apply only what's approved, to the files decided in Step 2 — never collapse everything into a single `CLAUDE.md` edit for convenience.
