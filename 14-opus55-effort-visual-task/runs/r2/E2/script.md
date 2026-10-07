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
- **Duration:** 50s to 60s
- **Top Badge:** `RESULT 01` | `THE BILL`

### Visual Direction:
1. **Method strip:** one line saying what is counted: cost of the 8 follow-up turns after the reset point (about 200k tokens), mean per setup, from the usage ledger.
2. **Real exhibit:** the final Sonnet 5.5 table from `PILOT_RESULTS.md` as six bars, drawn in the order they are named: no reset $0.95, `/compact` $0.53, brief handoff $0.57, then claude-auto-handoff $0.66 and handoff-compact $0.73, then the subagent $1.20, with dollar counters climbing.
3. **Hero beat:** the subagent bar passes the no-reset line and is stamped `MORE THAN DOING NOTHING`.

### Narration:
Result one is the bill. I'm counting what the eight follow-up turns cost after the reset point, when the session holds about two hundred thousand tokens. The figures come from Claude Code's usage ledger, and they are averages across my Sonnet runs, three each, and four for claude-auto-handoff.

Why would a reset save anything? Every turn sends the whole conversation back to the model. A shorter conversation makes a cheaper turn, so the saving shows up in the turns after the reset.

Doing nothing costs ninety five cents. Slash compact costs fifty three cents. A brief handoff to a fresh session costs fifty seven. So a reset cuts the bill about in half. Same task, same eight turns, half the money.

Now the mods. claude-auto-handoff costs sixty six cents. handoff-compact costs seventy three. They do save money. But both cost more than the command that's already built in.

And the subagent costs a dollar twenty. That is more than doing nothing. It was the most expensive of the six. Handing the work to a subagent cost more than leaving the session alone.

---

## Section 05: Result Two, The Rules: 5:00 to 6:30
- **Duration:** 50s to 60s
- **Top Badge:** `RESULT 02` | `THE RULES`

### Visual Direction:
1. **Method strip:** twelve rules from turn 1, follow-up code searched by regex, flagged lines read by eye.
2. **Sonnet scoreboard:** five reset setups at 0 broken runs, no reset at 1 of 3; beside it the real Sonnet reply to "force push this" (`sonnet-A6-f7.txt`), which leaves the force push out.
3. **Haiku scoreboard:** no reset 0 of 3, `/compact` 3 of 3, brief handoff 3 of 3, mod runs broke in every run.
4. **Real exhibits:** rule 1 from the turn 1 prompt, then the Haiku `deploy.sh` excerpt with the `--force-with-lease` fallback highlighted, stamped `NEVER, UNDER ANY CIRCUMSTANCE`.

### Narration:
Result two is the rules. After a reset, does the session still obey the twelve rules I gave it in turn one? I searched the code from the follow-up turns with a pattern match, then read every flagged line myself.

On Sonnet, yes. Slash compact, the brief handoff, the subagent and both mods broke no rules in any run. The only setup that broke one was doing nothing. In one of three runs, it broke my rule about grid columns. And when I told Sonnet to force push, it left the force push out and said why.

Haiku is different. That's the smaller model. With no reset, it kept every rule. After slash compact, all three runs broke a rule. After a brief handoff, all three. And every mod run on Haiku broke one.

The rule that goes is never force push. After slash compact, and after a brief handoff, Haiku wrote the force push into the deploy script in two of three runs each. A rule that said never, under any circumstance, was gone. On Haiku, a reset can cost you your hardest rule.

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
