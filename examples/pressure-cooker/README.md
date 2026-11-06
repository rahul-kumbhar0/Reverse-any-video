# Example: "Why does a pressure cooker whistle?" (45 s, full pipeline)

The first full-length video made end to end by the agent in the photoreal-tech-explainer
style, with Indian-English narration and the Kai presenter.

| Step | Command / file |
|---|---|
| Script | `script.json` (13 lines, `{id, text, gap}`) |
| Voice | Kokoro `hm_omega` per sentence (English text, Hindi voice → Indian-English accent) |
| Word timing | `align_words.py` per sentence with each sentence's start offset (PocketSphinx) |
| Lip-sync | `lipsync.py vo.wav lipsync.json --engine rhubarb --dialog "<full script>"` |
| 3D | `scene_cooker.py --shot hero|cutaway|weight|safety|pullback` (≈7 s/frame, ~25 min total) |
| Composite | `CookerReel.tsx` (Remotion): shots + gauge/thermometer graphics + tracked labels + captions + Kai + audio |

Facts used: Indian cookers run ≈1 bar (15 psi) above atmospheric pressure, raising water's
boiling point to ≈120 °C; the weight valve lifts to vent steam (the whistle); a fusible
metal safety plug melts open if the vent blocks.
