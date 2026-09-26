# DESIGN.md — Query Latency Heatmap

## Palette
Data-first, not brand-first: use a real perceptually-uniform sequential
scale (viridis or magma-style, low-to-high latency), not a decorative
brand gradient. Chrome around the widget is dark neutral `#111214`,
gridlines `#2A2B2E`. The heatmap's own color scale is the only color
that carries meaning here.

## Layout
Widget-first: the heatmap itself takes ~70% of the frame, controls
(time range, bucket size) sit in a thin toolbar above it, not scattered
around the edges. No hero section — this is an embeddable component,
not a landing page, and should render correctly cropped to just itself.

## Motion
One real signature motion moment only: hovering a cell should smoothly
scale/highlight that cell and cross-reference its row/column labels.
Everything else static. No page-load entrance animations — this
component gets embedded and may mount mid-scroll.

## Voice
Minimal on-widget copy: axis labels and a tooltip, nothing else. Numbers
are the content here, not marketing language.

## Never
No fake "live" pulsing dot unless data is actually streaming. No
gradient-filled cells that ignore the real underlying value scale —
color must map to the real P99 number, not to an arbitrary decorative
gradient.
