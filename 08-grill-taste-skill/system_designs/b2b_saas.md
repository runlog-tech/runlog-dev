# DESIGN.md — Litestream-S3

## Palette
Brand accent is `#F97316` (the flame-orange in our actual logo, not a
generic pick). Ground is near-black `#0A0A0B`, cards `#141416`. No purple,
no blue-to-pink gradients anywhere — orange is the only accent color in
the entire page.

## Layout
This is a database ops tool for SREs, not a consumer landing page.
Structure it like our own `/dashboard` screenshot already in the repo:
a dense two-column layout, left column narrative/pitch, right column a
live-feeling metrics panel. Never a centered hero with feature cards
underneath — SREs bounce off that pattern immediately, it reads as
"toy," not infrastructure.

## Motion
No animation library. This audience distrusts motion on infra tools —
it reads as marketing over substance. CSS `transition` on hover states
only (button/link color shifts), nothing else moves.

## Voice
Talk like our own docs already do: precise, technical, no adjectives
that don't carry information. "Streams WAL segments to S3 every 10s,"
not "seamlessly syncs your data." Say the actual number, not a vague
superlative.

## Never
No "99.99% uptime" stat unless it's a real number we can back. No
div-based fake terminal window as decoration — if we show a terminal,
show one real command and its real output, nothing invented.
