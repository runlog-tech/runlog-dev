# House rules for RUNLOG narration (round 2; same file given to every arm)

Channel: RUNLOG (@runlog_dev), solo and senior devs, production-grade agentic engineering with Claude Code. Voice: first person, measured, receipts over hype.

## Narration (spoken, read aloud by a local TTS voice)
- Write for the ear. Short sentences. Once a proper noun is introduced, use a pronoun. Read every line aloud in your head before keeping it.
- No developer jargon where a plain word works ("image generation", not "image gen"). Do not re-introduce an acronym right after spelling it out.
- Name sources on first mention. Explain what a technical result means before citing it.
- Any "I tested X" must name the actual thing tested: the setups, the model, the task.
- On a finding worth emphasis, dwell: say it, react, repeat it in plain words.
- Do not narrate our own corrections or research stumbles.
- Numbers: only ones in the facts files, copied exactly. Say them the way a person would speak them.
- generate_tts.py lints banned vocabulary; if it rejects a word, rewrite the sentence.

## Frames
Design the frames however you judge best. The channel's usual design rules do not apply to this exercise. fb.py and the other sections are available as optional reference; you may use them or build your own HyperFrames HTML. Render with render_section.py.
