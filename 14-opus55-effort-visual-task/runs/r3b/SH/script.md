## Section 04: Result One, The Bill
- **Top Badge:** `RESULT 01` | `THE BILL`

### Visual Direction:
1. **Metric card:** what is being compared (cost of every turn after the reset point, usage ledger, mean of the runs, Sonnet 5.5).
2. **Bar chart, six setups:** no reset $0.95 and subagent $1.20 first, then /compact $0.53, brief handoff $0.57, claude-auto-handoff $0.66, handoff-compact $0.73; /compact marked cheapest.
3. **Why the mods cost more:** the extra brief call, then context left after the reset (60k to 69k vs about 47k).

### Narration:
Result one, the bill. This is the cost of every turn after the reset point, averaged across the runs, on Sonnet 5.5.

Doing nothing cost ninety five cents on average. The subagent cost a dollar twenty, the most of any setup. Slash compact cost fifty three cents. The brief handoff, fifty seven. claude-auto-handoff, sixty six. And handoff-compact, seventy three.

So a reset roughly halves the cost of the turns that follow, and the mods deliver on that. But the cheapest of all six was slash compact, the one you already have. Nothing to install, and it beat both mods.

Why? claude-auto-handoff makes an extra model call to write its brief. handoff-compact left sixty to sixty nine thousand tokens in the context, against about forty seven thousand for slash compact. Then the context grew back, and every follow-up pays for what's in there.

So the mods save you money. Slash compact saves you a little more.
