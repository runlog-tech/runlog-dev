# Script: I Tested the Auto-Handoff Mods Everyone Is Building (Video 21, DRAFT NARRATION)

Angle locked 2026-10-05: they roughly halve the cost of later turns, and so does built-in `/compact`. Numbers below are from `scripts/claude-code-mods-audit/PILOT_RESULTS.md` and are not final until Sonnet rep 6 and more real-mod runs are in. Narration drafted 2026-10-05 against `docs/PERSONA_TIM.md` (cold-open reframe, roadmap, mental-model beat, up-front fairness disclosure, tour-guide present tense, exact-number anchors, ranked verdict, RUNLOG sign-off); humanizer pass done 2026-10-06; sections 01, 03, 04, 06, 07 updated for the handoff-compact Sonnet runs (six setups) 2026-10-06, humanizer re-pass pending. Sonnet leads, Haiku comes in at result two.

## Production Metadata
- **Channel:** RUNLOG (@runlog_dev). **Voice:** Kokoro `am_fenrir`, speed 1.0, reel-style pauses (`GAP_STYLE=reel`). Pipeline: copy `scripts/claude-workflows-pro-plan/` (generate_tts.py, hyperframes/fb.py, sections.py, render_section.py, assemble_video20.py) into this folder and adapt, per the visuals-are-the-master-clock procedure.
- **Style reference:** `docs/PERSONA_TIM.md` (Anti-AI Vocabulary Filter applies to every draft).
- **Rules:** zero em/en dashes, no banned words (`docs/VOCABULARY_AND_TONE_RULES.md`), real exhibits only (actual terminal output, the repos, the mod's own README and `claude plugin validate` output), humanizer pass on every section before frame build, state the concrete test every time.
- **Target:** 7 to 9 minutes.

## Section 01: The Hook: 0:00 to 0:40
- **Duration:** 35s to 45s
- **Top Badge:** `AUDIT 01` | `DO HANDOFF MODS WORK?`

### Visual Direction:
1. **Real exhibit:** GitHub search list of handoff mods with creation dates (Sep 10 to Oct 3, 2026).
2. **Hero number:** a cost odometer climbing with each turn, then the question stamped on screen.

### Narration:
Mods came out at the start of October, and the first thing everyone went looking for was a compaction mod. A better, cheaper compact: a mod that hands your long session to a fresh one, so you save money and lose nothing.

Mods can do a lot more than this. But we've made a few videos on compaction already, and everyone keeps asking about this idea, so I ran the kind of benchmark we usually do. Does a compaction mod beat the slash compact you already have?

I put a long Sonnet 5.5 session through six different setups, including two community mods. And surprisingly, the built-in slash compact cost less, and it kept every rule. Let's find out more.

---

## Section 02: What a Mod Is: 0:40 to 2:00
- **Duration:** 70s to 85s
- **Top Badge:** `CONTEXT` | `WHAT A MOD IS`

### Visual Direction:
1. **Real exhibit:** `claude plugin validate` output for claude-auto-handoff, showing the events it hooks and the `$` calls it makes.
2. **Real exhibit:** the X post announcing mods with its view count, "as of" date on screen.

### Narration:
First, what a mod is. Here's the mental model: a hook in your settings runs a command outside Claude Code. A mod is a plugin written in JavaScript or TypeScript that runs inside it. It can react to a prompt being submitted, a tool call, or a turn ending, and it can watch what Claude is doing, change it, or take it over.

On disk, a small mod is just three files: a manifest, a file that points to the code, and the code itself, which tells Claude Code which events to run your functions on.

Now, the docs are clear about this: a mod isn't sandboxed. It runs with your permissions, so it can read and write your files, start programs, and make network requests. It can read your secrets, like an API key in your settings. It can approve a tool call before you're asked, and it can spend your usage by calling a model. Even with sandboxing turned on, a process a mod starts runs outside it. Every hook gets one object called dollar, and that's how it does all of it. So when you audit a mod, you look at what it calls through dollar. Let's have a look at what claude plugin validate prints for claude-auto-handoff. Notice the events it hooks, and the calls it makes.

Anthropic announced mods on October second, and that post has passed four million views as of October fifth. It's also a three day old API, so everything here is a snapshot.

---

## Section 03: The Test: 2:00 to 3:15
- **Duration:** 65s to 80s
- **Top Badge:** `AUDIT 02` | `THE TEST`

### Visual Direction:
1. **Real exhibit:** the 12 rules prompt from turn 1 and the follow-up that asks Claude to force-push (from `pilot/run_pilot.py`).
2. **Five setups as a row:** no reset, `/compact`, brief handoff, subagent, the community mod.
3. **Real exhibit:** `run_mod.py` driving the mod in a terminal.

### Narration:
Now, the test. I want to be clear that this isn't a lab benchmark. It's one task, a handful of runs, and a regex grader that I checked by eye. Treat the results as a direction.

In turn one, I give Claude twelve project rules, including one that says never force push, under any circumstance. Then it reads files until the context hits about two hundred thousand tokens. That's the reset point. After it, I ask for a feature, then eight follow-ups, and one of them says force push this.

There are six setups: do nothing, the built-in slash compact, a brief handoff to a fresh session, a subagent, and two community mods, claude-auto-handoff and handoff-compact. Three runs each on Sonnet 5.5, four for claude-auto-handoff, with cost read straight from Claude Code's usage ledger. One early batch hit the session limit halfway through, so I threw it out and reran it. And handoff-compact never fired with its own trigger on Sonnet, so I used its default mode.

---

## Section 04: Result One, The Bill: 3:15 to 5:00
- **Top Badge:** `RESULT 01` | `THE BILL`
- **Duration:** 50s to 60s

### Visual Direction:
1. **Metric card:** what is being compared (cost of every turn after the reset point, usage ledger, mean of the runs, Sonnet 5.5).
2. **Bar chart, six setups:** no reset $0.95 and subagent $1.20 first, then /compact $0.53, brief handoff $0.57, claude-auto-handoff $0.66, handoff-compact $0.73; /compact marked cheapest.
3. **Why the mods cost more:** the extra brief call, then context left after the reset (60k to 69k vs about 47k).

### Narration:
Result one, the bill. This is the cost of every turn after the reset point, averaged across the runs, on Sonnet 5.5.

Doing nothing cost ninety five cents on average. The subagent cost a dollar twenty, the most of any setup. Slash compact cost fifty three cents. The brief handoff, fifty seven. claude-auto-handoff, sixty six. And handoff-compact, seventy three.

So a reset roughly halves the cost of the turns that follow, and the mods deliver on that. But the cheapest of all six was slash compact, the one you already have. Nothing to install, and it beat both mods. That surprised me. The thing people are building mods to replace came in cheapest.

Why? claude-auto-handoff makes an extra model call to write its brief. handoff-compact left sixty to sixty nine thousand tokens in the context, against about forty seven thousand for slash compact. Then the context grew back, and every follow-up pays for what's in there.

So the mods save you money. Slash compact saves you a little more.

---

## Section 05: Result Two, The Rules: 5:00 to 6:30
- **Top Badge:** `RESULT 02` | `THE RULES`
- **Duration:** 50s to 60s

### Visual Direction:
1. **Sonnet scoreboard:** six setups, rule breaks per run; only no reset shows a break (1 of 3, grid rule).
2. **Real exhibit:** Sonnet's reply leaving out the forced push (`sonnet-A6-f7.txt`).
3. **Haiku scoreboard flips:** no reset 0 of 3, /compact 3 of 3, brief handoff 3 of 3.
4. **Real exhibits side by side:** Haiku refusing with the full context (`refusal-A1-haiku.txt`) vs the deploy script written after /compact (`deploy-B2-haiku-excerpt.sh`).

### Narration:
Result two, the rules. A cheaper session means nothing if it forgets your rules.

On Sonnet 5.5, five of the six setups broke no rules at all. Not slash compact, not the subagent, not either mod. The only break came from doing nothing: in one of three runs, it built a grid the rules didn't allow. And no Sonnet run wrote the force push. Here's one telling me rule one bans it. At the end, nearly every run listed all twelve rules, though one brief handoff dropped the word never from the force push rule.

Now Haiku 4.5, the smaller model, with the reset at about a hundred thousand tokens. Here it flipped. Doing nothing kept every rule in three of three runs. Slash compact and the brief handoff each broke a rule in three of three. Doing nothing refused the force push. After slash compact, Haiku wrote it into the deploy script. Every mod run on Haiku broke a rule too.

So on Sonnet, the reset was safe. On Haiku, it lost the rule I'd stated the strongest: never force push, under any circumstance.

---

## Section 06: What the Mods Did: 6:30 to 7:45
- **Duration:** 65s to 80s
- **Top Badge:** `AUDIT 03` | `SIDE EFFECTS`

### Visual Direction:
1. **Real exhibit:** process list showing the localhost server on port 3846 after the session ended.
2. **Real exhibit:** the Bash prompt where the fresh session searches its own old transcript.
3. **Real exhibit:** context meter reaching 130k+ again for context-relay and handoff-compact.

### Narration:
I also watched what the mods did on my machine.

claude-auto-handoff starts a small web server on port three eight four six. It kept running after the session ended, even with the viewer setting left blank. I killed it by hand.

Its fresh session never got the original rules. You can see it here, searching its own old transcript to find them, and that's why it could only give me paraphrases.

Separately, handoff-compact ended the eight turns at about eighty six thousand tokens, against forty six thousand for slash compact, which gave back some of the saving. On Haiku, it and context-relay climbed past a hundred and thirty thousand.

---

## Section 07: The Verdict: 7:45 to 8:30
- **Duration:** 40s to 50s
- **Top Badge:** `VERDICT` | `WHAT I'D DO`

### Visual Direction:
1. **Stack:** three recommendations.
2. **Limits on screen:** small n, one task, regex grader with a human audit, Haiku and Sonnet only, Reddit not read.

### Narration:
So here's the ranking. Number one, slash compact: it cut the cost the most, kept every rule on Sonnet, and costs nothing to install. Number two, a mod like claude-auto-handoff or handoff-compact, only if you want the saved handoff file, and read what it calls before you install it. Number three, the subagent, which cost the most.

And on a small model, put your hard rules in CLAUDE dot md, not in the conversation, because Haiku lost the strongest wording in every run that compressed it.

Keep the limits in mind: three to four runs per setup, one task, Haiku and Sonnet only, and I didn't get to read Reddit. Every run is linked below. Subscribe to RUNLOG for engineering receipts over prompt hype.

---

## Open before narration
- Runs are done (Sonnet reps 4 to 6, real mod H4 to H7, 2026-10-05). Remaining: capture exhibits, write narration, humanizer pass, build frames.
- View claim VERIFIED 2026-10-05 through a logged-out Chrome read of https://x.com/ClaudeDevs/status/2105721434807083061 (posted 2:08 AM Oct 2, 2026): 4.3M views, 669 replies, 1.2K reposts, 20K likes, 13K bookmarks at the time of reading. The earlier "685K within hours" figure came from a search summary and is superseded. Re-screenshot right before the final render and say "as of <date>"; screenshot saved in `assets/`.
- Decide whether to show Haiku and Sonnet together or lead with Sonnet.
