# Figure sources and visual checks

These are original editable SVG figures, with raster PNG previews. They contain text and vector objects with stable node/edge IDs; no raster image is embedded in the SVG. The generating code is [make_figures.py](../../tools/make_figures.py).

The requested PaperBanana workflow was used through its installed Codex-native adaptation. That adaptation was renamed to **Flowcraft** during the build; its current instructions and provenance were read before rendering. The [PaperBanana upstream](https://github.com/dwzhu-pku/PaperBanana/tree/f1da3db8d5f4c3add947dfd3ddd93dddd3394dc3) is credited as a workflow foundation. No upstream API pipeline, model benchmark, downloaded example diagram, provider credential or paid generation call was used. Its artwork and source code are not incorporated in these figures.

The visual reference was this repository's actual architecture, method specification and results. Layout choices are original. White background, restrained semantic color, readable type, explicit solid/dashed relationships, source-grounded labels and iterative rendered-image critique follow the skill. These workflow choices do not establish visual superiority over the upstream pipeline.

| Figure | Source facts and elements | Caption and scope |
|---|---|---|
| `research-lifecycle` | `data.py`/`spec.py` → input contract; `artifacts.make_plan` → lock; `evaluation.region_targets`/`engine.simulate` → fit/decision/ledger; `run_development` → evidence and AI packet; `validated_selection`/`run_holdout` → frozen specification and separate holdout; `verify_bundle` → integrity, exports and replay | Solid path evaluates the registered experiment. Dashed path revises hypotheses using development evidence only. Both stages preserve full evidence. It does not depict an automated LLM call or live broker. |
| `causal-timing` | `ResearchConfig` defaults and `folds` → train `[0,252)`, gap 252/253, first test `[254,317)`, final holdout `[630,756)` for 756 sessions; `strategies._fit` → label endpoint; `generate_targets` → availability; `engine.simulate` → eligible open, marking and publication-aware risk | Illustrative schematic with nonproportional widths. A delayed fill is followed by its own session's close. An unavailable bar cannot retroactively create a decision. Opening prices and daily capacity remain declared approximations. |
| `synthetic-selection` | `examples/selection-study/results.json` → every seed, selected name, development excess and holdout excess; summary positive count/mean checked against the rows | All 12 replications retained on common zero-centered scales. Percentage points, not risk-adjusted alpha. No invented confidence bars, significance or real-market inference. |

Numeric values are read directly from the JSON. The generator checks unique seeds, observation count, finite points, summary mean/positive count and an automatically expanded shared axis. There are no manually retyped plot values. SVG coordinate generation preserves the recorded values and units.

The first plot draft deliberately failed when observations exceeded its initial scale; the scale was changed to encompass every actual value on both panels. Rendered review then removed an ambiguous crossing in the lifecycle feedback path and corrected “close t+1” to “fill-session close” for delayed execution. Current PNGs were opened and inspected against the sources for arrow direction, cutoff meaning, label completeness, clipping and numeric correspondence.

Recreate editable masters into a fresh directory:

```sh
python tools/make_figures.py --out fresh-figures
```

Open SVG directly in a suitable viewer or use the free renderer supplied by the installed Flowcraft skill. Rendering is not a runtime dependency of Chronal. No PDF is claimed delivered or checked. PNG previews are convenient raster exports; SVG files remain the editable vector masters.
