# Brief for round 3b (identical for every arm)

Channel: RUNLOG (@runlog_dev), solo and senior devs, production-grade agentic engineering with Claude Code. The audience watches this as a YouTube video, much of it on a phone, so the frame has to carry the story while the narration plays.

You are building ONE frame: Section 04 of the video, 1920x1080, as a HyperFrames composition. The narration audio and its word timings are fixed (hyperframes/audio/). No helper library and no previous frames are provided. Write your own HyperFrames HTML composition at hyperframes/compositions/frames/04-result-one-the-bill.html.

DESIGN: docs/DESIGN_SYSTEM.md is the channel's design system. Read all of it first and follow it: palette, type scale, the borderless rule, single focus per stage with stage swaps, a visual event every 3 to 5 seconds, ranked vertical layouts, no em or en dashes in viewer-facing text. Where the document and the visual direction in script.md differ on layout, the design system wins.
Use the narration text and word timings to time what appears; use the real exhibits in assets/exhibits/ and the facts in facts/ for any number you show (numbers only from there, copied exactly).
Check, snapshot and render with hyperframes/render_section.py. Never use screenshot capture or low-memory render modes.
