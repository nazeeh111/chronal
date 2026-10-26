# Figure sources and visual checks

These are original editable SVG figures, with raster PNG previews. They contain text and vector objects with stable node/edge IDs; no raster image is embedded in the SVG. The generating code is [make_figures.py](../../tools/make_figures.py).

| Figure | Source facts and elements | Caption and scope |
|---|---|---|
| `research-lifecycle` | `data.py`/`spec.py` → input contract; `artifacts.make_plan` → lock; `evaluation.region_targets`/`engine.simulate` → fit/decision/ledger; `run_development` → evidence and AI packet; `validated_selection`/`run_holdout` → frozen specification and separate holdout; `verify_bundle` → integrity, exports and replay | Solid path evaluates the registered experiment. Dashed path revises hypotheses using development evidence only. Both stages preserve full evidence. It does not depict an automated LLM call or live broker. |
| `causal-timing` | `ResearchConfig` defaults and `folds` → train `[0,252)`, gap 252/253, first test `[254,317)`, final holdout `[630,756)` for 756 sessions; `strategies._fit` → label endpoint; `generate_targets` → availability; `engine.simulate` → eligible open, marking and publication-aware risk | Illustrative schematic with nonproportional widths. A delayed fill is followed by its own session's close. An unavailable bar cannot retroactively create a decision. Opening prices and daily capacity remain declared approximations. |
| `synthetic-selection` | `examples/selection-study/results.json` → every seed, selected name, development excess and holdout excess; summary positive count/mean checked against the rows | All 12 replications retained on common zero-centered scales. Percentage points, not risk-adjusted alpha. No invented confidence bars, significance or real-market inference. |

Numeric values are read directly from the JSON. The generator checks unique seeds, observation count, finite points, summary mean/positive count and an automatically expanded shared axis. There are no manually retyped plot values. SVG coordinate generation preserves the recorded values and units.

Recreate editable masters into a fresh directory:

```sh
python tools/make_figures.py --out fresh-figures
```

SVG files remain the editable vector masters; PNG previews are raster exports. Rendering is not a runtime dependency of Chronal.
