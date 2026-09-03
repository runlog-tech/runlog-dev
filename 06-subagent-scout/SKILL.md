---
name: subagent-scout
description: Scans a project's real Claude Code session history for repeated tool-call patterns still running inline, judges whether each is worth a dedicated subagent (and which model tier) via a 4-question checklist, interviews the user one candidate at a time, and drafts the .claude/agents/*.md file on confirmation. Use when a session feels repetitive, when starting work in a project that's had a lot of history, or when the user asks "do I need a subagent for this" / "find candidates for subagents" / "am I wasting tokens on repeated work."
---

# subagent-scout

Detects candidates for new subagents from a project's own history, then interviews the user before doing anything irreversible. Never invents a candidate — every flagged pattern must trace back to real, counted tool-call repetition in real session transcripts.

## Step 1: Run the detector

```
python3 ~/.claude/skills/subagent-scout/scripts/detect_patterns.py --repo-path <target project dir>
```

This is real, inspectable code — not an LLM guess. It scans the project's main-thread session transcripts (`~/.claude/projects/<encoded-path>/*.jsonl`, never the per-session `subagents/` subfolders — those are already-delegated work, not candidates) for tool-call sequences (enriched with a light content shape: `Bash:<command>`, `Read:<ext>`, `Agent:<subagent_type>`) that repeat at least 3 times, and reports two distinct signals per candidate:

- `cross_session_count` — how many separate sessions the pattern recurs in. Evidence of a durable, recurring workflow.
- `max_single_session_count` — the heaviest repeat count seen inside any one session. Evidence that a single session's context got bloated by this loop, even if it never recurred elsewhere.

It automatically skips any signature already recorded in `.claude/subagent-scout-log.md` in the target repo (built or explicitly declined before) so a decline stays sticky.

If it returns no candidates, say so plainly and stop — do not lower the bar or invent a marginal one to have something to report.

## Step 2: Judge each candidate against the checklist

For each candidate, read the actual repeated tool calls (open the relevant slice of the session transcript(s) named in `cross_session_names` if you need real content, not just the shape) and score it against the same 4-question checklist used for existing subagents on this channel:

1. **Retrieval vs. judgment** — is this a lookup/mechanical task, or does it need interactive reasoning?
2. **Stateless vs. needs context** — can it run with a fresh context each time, or does it depend on accumulated session state?
3. **Cheap to verify vs. not** — can a human or a script cheaply confirm the output is right?
4. **Low vs. high blast radius** — if it's wrong, is the damage small and local, or large/hard to undo?

Retrieval + stateless + cheap-to-verify + low-blast-radius points toward **Haiku**. Needs judgment or context but is still bounded and one-shot points toward **Opus**. Needs iterative back-and-forth (the pattern only looks repetitive because a human keeps steering it differently each time) means it's **not a good subagent candidate at all** — say so, don't force a tier onto it.

State the verdict plainly before moving on: which tier, or "not a good fit," and why, citing the real counts from Step 1 (e.g. "repeated 5x across 2 sessions, stateless, cheaply verified by re-running it → Haiku").

## Step 3: Interview before acting

Ask only what the user's prior answers have actually unblocked — each of the 3 questions below depends on the one before it (no point asking for a subagent name before confirming the user wants to proceed, or asking about model tier before confirming the pattern is real), so they go one at a time, in order:

1. Confirm the user recognizes this pattern as real recurring work (not a detector false positive).
2. Confirm or adjust the recommended model tier.
3. Ask for a name for the subagent if proceeding.

Do not draft or write anything until the user has explicitly said to proceed.

## Step 4: Act on the decision

**If the user says build:**
Draft `.claude/agents/<name>.md` in the target project directly (frontmatter: `name`, `description`, `tools`, `model`; body: a system prompt synthesized from the real repeated task, not a generic template) and write it via the Write tool. Tell the user to review it before trusting it — this is AI-drafted, human-approved, not auto-committed blindly.

**If the user says skip:**
Append a row to `.claude/subagent-scout-log.md` in the target project (create it with a header row if it doesn't exist) recording: the signature (backtick-quoted, exactly as printed by the detector, so future runs can match and skip it), the checklist verdict, the decision (skipped), and the date. This makes the decline sticky — the same candidate won't be re-flagged on a future run. **Copy the signature string verbatim from the detector's JSON output — never paraphrase or summarize it.** Dedup is an exact string match against `.claude/subagent-scout-log.md`; a shorthand like `` `some-tool` (repeated) `` instead of the literal `` `some-tool -> some-tool -> some-tool -> some-tool` `` will silently fail to match on the next run, and the same candidate will get re-flagged. (Caught live 2026-08-26: exactly this mistake happened during testing.)

```
| Signature | Verdict | Decision | Date |
|---|---|---|---|
| `Bash:cd -> Read:png -> Read:png` | Haiku candidate (stateless, cheap-to-verify) | skipped | 2026-08-26 |
```

## Honest limits to state plainly, not paper over

- The detector is mechanical pattern-matching on tool-call shape, not intent — it can flag coincidentally-similar work that isn't actually the same task, and it can miss a real repeated task if the tool-call shape varies each time even though the underlying intent is identical. Always sanity-check a flagged candidate against the real transcript content before trusting the count alone.
- A pattern that's heavily repeated within a single session but never recurs across others is weaker evidence of a durable habit worth a permanent subagent — say so explicitly rather than treating both signals as equivalent.
- This finds candidates for *new* subagents. It says nothing about whether your *existing* subagents are tiered correctly — that's `audit_subagent_models.py` from video 5, a separate tool.
- **Session history is keyed by working directory, not by session identity.** If a session changes cwd mid-session (entering a git worktree, `cd`-ing into a subdirectory Claude Code treats as its own project root), its transcript can split across two different `~/.claude/projects/<encoded-path>/` directories. Scanning only one directory can silently undercount a real repeated pattern whose later occurrences got logged under the other path. Discovered live while building this skill: entering a worktree mid-session moved the active session's own `.jsonl` to a new project key, dropping `sessions_scanned` and erasing what had been the single strongest candidate. If a scan's candidate list looks suspiciously thin compared to what the user expects, check whether related project-key directories exist under `~/.claude/projects/` (matching path prefixes/suffixes) before concluding there's nothing there.
