# Wolfpack · "一张卡片的一生" (The Life of One Card) — 15s beat sheet

Concept: one Issue card is the whole film. It never gets replaced by a cut — it grows into the
detail view, its assignee morphs from a person into an agent, its own activity list becomes a
tool-call timeline, it collapses back down, and flies home to Done. Everything else (board,
picker, timeline rows) is dressing that appears and disappears around that one surviving rect.

Technique: **rebuild**, not recorded footage — the morph between the kanban-card rect and the
detail-panel rect must be an exact `morphRect`, which needs the same DOM node at both ends, not
video frames. Colors/type pulled from the real tokens (`--primary #0069ee`, `--success #097f23`,
`--warning #bd7400`, purple-400 `#c084fc` for agent, `--background #e8f1fc`, `--foreground #070e17`).

| t (s) | len | beat | moves | still / quiet | carries in |
|---|---|---|---|---|---|
| 0.00–1.00 | 1.00 | board hold — small card "Refactor API error handling middleware" sits in Todo among 4-5 other cards, cursor drifts toward it | `drift` (board), `cursor` spline | yes — establishing hold | — (opens the loop) |
| 1.00–1.35 | 0.35 | click | `impact` ring + `press` flash on card | no | the ring seeds the morph |
| 1.35–2.55 | 1.20 | **card → detail panel** | `morphRect` A(card rect)→B(panel rect), `zoomThrough`-style camera push | no — the big motion beat | the card rect itself |
| 2.55–3.55 | 1.00 | detail hold — title, AR avatar, status "Todo" | none but a slow `drift` | yes — hold | the assignee slot |
| 3.55–3.85 | 0.30 | picker opens at the assignee slot | `popIn` | no | anchored to the same slot |
| 3.85–4.15 | 0.30 | click "Claude" | `impact`/`press` on the row | no | click seeds the avatar morph |
| 4.15–4.65 | 0.50 | **AR avatar → Claude avatar** (initials circle → purple Bot circle), picker `liftOut` | `impact` + colour tween | no | avatar circle |
| 4.65–4.95 | 0.30 | status pill Todo → In Progress | `tick` snap | no | status pill |
| 4.95–6.55 | 1.60 | **near-silence #1** — camera drifts down, activity rows rise one at a time: "assigned to Claude" / "changed status" / a comment | `maskRise`/`wordRise` staggered, `drift` | yes — quiet reveal | the vertical list container |
| 6.55–7.05 | 0.50 | **activity list → tool-call timeline** (same container, rows dissolve/replace with thinking/tool_use/tool_result) | `morphRect` on the container + blur cross | no | the list container |
| 7.05–9.85 | 2.80 | **near-silence #2 — the work happens.** Tool rows tick in with green checks; task-history rows ("Set up error response types — completed 2m14s"…) settle; a small spinner pulses. | `tick` per row, subtle `ring`/spinner rotate, everything else `drift`-still | yes — the longest hold in the film | last row primed for the finishing impact |
| 9.85–10.15 | 0.30 | last row completes | `impact` ring, tick flips | no | seeds the status flip |
| 10.15–10.45 | 0.30 | status pill → **Done** (the emotional beat) | `impact` bounce, colour → info blue | no | status pill |
| 10.45–11.15 | 0.70 | **detail panel → small card** (reverse morph) | `morphRect` B→A′ | no | the same rect, shrinking |
| 11.15–12.35 | 1.20 | card arcs across the board to the Done column | `hop` | no | the card object |
| 12.35–13.15 | 0.80 | board hold, card sits in Done among other cards — rhymes with the opening shot | `drift` | yes — closing hold | the card's own check glyph |
| 13.15–13.45 | 0.30 | iris opens from the card's check glyph | `iris` | no | the check glyph seeds the stage |
| 13.45–14.30 | 0.85 | wordmark + WolfpackIcon asterisk drop in over deep ground | `letterDrop`/`wordRise`, icon spin | no | — |
| 14.30–15.00 | 0.70 | end-card hold: wordmark + tagline steady | none | yes — final hold | end card (exception) |

**Rhythm check.** Shot lengths run 0.30 s → 2.80 s, a 9.3× spread (≥4× required). Two genuine quiet
stretches (1.60 s reveal, 2.80 s work-happens hold) sit either side of the busiest run of cuts
(3.55–4.95, four beats in 1.4 s) — a burst next to a rest, not a metronome.

**Carry check.** Every boundary above names what survives it; the only cut with no surviving
object is the end-card hold, which is the explicit exception in the hard rules.

**Look.** `wolfpack` look (`/tmp/wolfpack_look.json` → applied via `look.py apply`): ground
`#eef3fa`, ink `#0b1622`, accent `#0069ee` (product primary), accent2 `#c084fc` (agent purple),
card white, line `#dbe4f0` — the product's own palette, not an invented one.
