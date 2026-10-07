# House rules for RUNLOG narration and frames (distilled from the channel's standing notes; same file given to both arms)

Channel: RUNLOG (@runlog_dev), solo and senior devs, production-grade agentic engineering with Claude Code. Voice: first person, measured, receipts over hype.

## Narration (spoken, read aloud by a local TTS voice)
- Write for the ear. Short sentences. Once a proper noun is introduced, use a pronoun. Read every line aloud in your head before keeping it.
- No developer jargon where a plain word works ("image generation", not "image gen"). Do not re-introduce an acronym right after spelling it out.
- Name sources on first mention. Explain what a technical result means before citing it ("zero rule losses" needs "it checked whether the model still followed each rule").
- Any "I tested X" must name the actual thing tested: the setups, the model, the task.
- On a finding worth emphasis, dwell: say it, react, repeat it in plain words. Do not state it once and move on.
- Do not narrate our own corrections or research stumbles.
- Numbers: only ones in the facts files, copied exactly. Say them the way a person would speak them.
- generate_tts.py lints banned vocabulary; if it rejects a word, rewrite the sentence.

## Frames
- Every claim on screen needs a visible real exhibit (the actual numbers, rows or text), not only an abstracted conclusion.
- Labels at least 40px, hero numbers at least 84px. Never muted gray text on the dark background: white or near-white, vary hierarchy by size and weight.
- Fill the canvas; no large empty margins. Never leave a visual static for more than about 10 seconds under narration: split it into sub-beats tied to spoken words (word indices from the alignment json).
- Quantified claims get an animated device (bars, count-up), not static text.
- Terminal-typing visuals are only for real commands.
- Render with render_section.py as-is. Never use screenshot capture or low-memory mode.
