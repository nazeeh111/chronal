# Final core and terminal review

Reviewed locally on 2026-10-22. Runtime fingerprint:
`27fdf2032fb776674dcf72a3641b098470a2abb615df27581260c2cb2c5f9b04`.

## Reproduced defects and corrections

The core specialist reproduced `strict_json('{"x":1e309}')` returning infinity, despite rejection of literal NaN/Infinity. The shared parser now rejects floating-point exponent overflow at the decoding boundary. Regression cases include positive/negative and nested overflows, extreme finite values and large integers. Existing finite example records decode identically. This is input integrity, not a demonstrated bypass of full financial replay.

The terminal specialist reproduced tiny signed fills becoming displayed zero through fixed-decimal formatting, and event/fold tables collapsing intraday timestamps to dates. Detailed quantities, prices, commissions and intent fields now retain up to eight significant digits, with scientific notation when needed. Nonzero values such as -1e-12 remain nonzero on screen. Event and fold rows show full timestamps when needed to distinguish same-day sessions. Session metrics now say session, with the assumed 252 sessions/year annualization exposed. Financial arithmetic was not changed by these display corrections.

Browser inspection found mobile header links shifting the page during horizontal navigation. An explicit same-hash link handler alone did not resolve the mobile behavior. At widths up to 600 px the final design replaces that row with a native section picker populated from the actual section links. Selection resets to the placeholder, so repeating a destination triggers navigation again. Desktop links use explicit scrolling on each activation. Native hrefs remain present.

## Useful additions

The execution finder searches actual simulator-authored requests across the evaluated region, intersecting asset, outcome and recorded reason. It paginates 12 attempts and jumps by global session index to the linked account/model/execution context. Counts are attempts, not round trips or a cross-asset share ratio. Exact partial residuals include numerical rounding; recorded reasons and quantity magnitude remain visible. Finder criteria and fill-ledger criteria are separately labeled.

The command palette searches described supported commands. Native result buttons copy the command into the input and focus it; Enter runs it. No selection executes automatically. History retains at most 100 submitted commands in memory, deduplicates consecutive repeats and restores the draft. Alt+Up/Down is scoped to the command input and excludes composition or other modifiers. It does not write browser storage. Native datalist completion was replaced after it failed to visibly open in the tested embedded browser.

## Independent review and verification

The core specialist read current data, specs, fitting, sizing, simulator, evaluation, artifact, CLI, study and ledger paths. Its refreshed 100-case accounting/causality/ridge perturbation probe passed. These are 80 randomized accounting/prefix cases and 20 future-OHLC perturbation cases, not 100 independent real-market experiments. No additional consequential financial defect was reproduced in that bounded scope.

The independent terminal reviewer extended the actual-function Node checker for tiny values, signed fill rendering, intraday labels, finder intersections/empty states/pagination/clamping/session jumps, history limits/deduplication/draft restoration, palette filtering/copy-without-execution/focus, repeated native link scrolling and repeated mobile selection/reset. Both final region reports pass. Small DOM stubs do not establish browser layout or event wiring.

Separate actual browser checks passed on final source: 1280x720 desktop, 390x844 mobile and 320x740 narrow layout; mobile Finder/Account/Finder/Finder targets consistently landed at about82 px below the top, and document width matched each mobile viewport. Repeated desktop Finder links landed at about124 px. Palette query ridge returned one command and choosing it did not change the inspected strategy until Enter. Finder constrained search showed seven ridge attempts, then four after asset/reason intersection; a request jump selected its exact account and recorded fit. Holdout constrained search was explicitly empty; reset restored27 attempts and next page showed13–24. History restored an unfinished draft without executing it.

Screenshots: [finder](assets/execution-finder.png), [mobile navigation](assets/finder-mobile.png), [palette](assets/command-palette.png), [mobile palette](assets/palette-mobile.png). Earlier review notes remain task-local in work/final_core_review.md and work/final-terminal-review.md; durable regressions are distributed in tests and tools/check_report.cjs.

No universal correctness, exhaustive security, investment edge or measured10x improvement is established by these checks. Full intent replay, independent accounting, unsigned manifest checks and UI inspection remain different guarantees.
