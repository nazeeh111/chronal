# Research terminal

This is an offline browser interface to one evaluated region. It renders data from that region and uses no external scripts, fonts, market feeds, model calls or account connection. The visible simulation label and synthetic-data notice are factual; no live or authenticated-verification badge is shown.

## Controls

- `/` focuses the command bar when outside editable controls. `Escape` leaves it. `help` or Commands opens the searchable keyboard-accessible palette and reference; Escape closes it.
- `strategy NAME` accepts registered result names only. It changes inspection, never the frozen selection.
- `view equity` and `view drawdown` change the chart. The session cursor accounts for the prepended initial-capital point.
- `session YYYY-MM-DD` selects a unique available UTC date. Missing, malformed or cleared dates retain the prior selection and restore the date field. If multiple sessions share that date, use the slider or `session #N`, where N is the 1-based position within this evaluated region. Readouts then include the full timestamp. The date control and native range slider provide the same session context; arrow keys step the slider.
- `goto performance|risk|interval|episodes|account|model|execution|finder|method|ledger|provenance` navigates sections. Unknown commands, including buy/sell or code text, produce explicit errors.
- Asset, side and selected-session filters operate together on actual fills. The counts/pagination describe matching fills. CSV downloads export the entire accompanying region ledger, not a filtered subset.

## Meaning of the data

Monthly returns compound the complete net portfolio path. Boundary months may be partial. A dash means no evaluated sessions in that month; 0.00% is a measured result rounded for display. Signed numbers accompany colors.

Account figures correspond to the selected chart session. Cash/invested weights use marked NAV. Holdings are share inventory, not asset valuations or concentration. Fill count and absolute filled notional measure observed activity, not round-trip trades. Fees are explicit commissions; adverse spread/slippage remains in fill prices. Nothing in this view establishes historical publication authenticity or investable performance.

## Verification

```sh
python -m chronal verify examples/demo --replay
node tools/check_report.cjs examples/demo/development/report.html
node tools/check_report.cjs examples/demo/holdout/report.html
```

The optional Node 22+ checker has no npm dependencies. It executes selected functions extracted from a trusted, locally generated report with small dependency stubs to test command/filter logic. It does not test browser layout, event wiring or accessibility. Do not run it on untrusted HTML. Actual desktop/mobile inspection is recorded in [VALIDATION.md](VALIDATION.md), with the independent [terminal review](TERMINAL_REVIEW.md).

## Linked interval and drawdown inspection

Chart click/tap selects the nearest evaluated session using the SVG screen transform; it accounts for CSS scaling, letterboxing and the initial-capital anchor. The slider is the keyboard alternative. Secondary pointer buttons do not change context.

Each observed monthly return is a native button with the month and return in its accessible name. It selects that month's actual available sessions for comparison. Missing months remain noninteractive dashes. `range START END` accepts unique UTC dates or `#N` positions, and Full region / `reset` restores the interval. Reversed, ambiguous and unavailable endpoints fail without partially applying a range. The shaded chart interval is a highlight of the full path, not a rebased chart or a refit.

The inclusive interval L..R starts from initial cash when L=0, otherwise equity[L−1]. Candidate and baseline use identical sessions. Local drawdown resets its peak at that starting NAV, so it differs from full-path drawdown. Fees and notional include fills at both endpoints. Excess total return is a difference in percentage points, not the return of a tradable long-short portfolio. All interval inspection is post hoc, and repeated selection creates additional bias.

The eight worst observed drawdown episodes show their full-region peak, trough, recovery or unrecovered state, depth and underwater-session duration. Inspect trough updates the linked chart cursor and account, without changing the comparison interval or frozen strategy. All-flat regions display an explicit empty state. Native anchors and command/month/episode navigation also work when the target hash is already selected.

## Model and execution inspection

`fit #N` selects a recorded evaluation window by its one-based ordinal and moves the shared cursor to its first session. The native refit selector does the same. Moving the session cursor automatically selects its recorded window. A model inspector reports the registered specification, evaluation dates, training boundary (exclusive source-session index) and first decision. For ridge it also shows the exact recorded information cutoff, sample count, regularization strength, intercept, training means/scales and standardized coefficients. A coefficient applies to one training-standardized feature unit, not causal importance. Rule strategies explicitly have no regression coefficients. Holdout inspection offers the recorded chronological windows for the frozen candidate and fixed baseline; scheduled expanding refits follow the frozen recipe and never search for a new candidate. No fitting runs in the browser.

`next-event` and `previous-event`, or the equivalent native buttons, move strictly to the next/previous session containing a recorded event. End buttons disable when no event is available. Event navigation is about recorded capacity, cash, risk and publication events; a fill without an event is still visible through normal session inspection. The frozen development winner stays fixed.

The execution inspector joins simulator-authored intent rows, actual fills and events at the shared session. Signed quantities distinguish buys and sells. Capacity is the minimum known/realized daily-volume proxy times participation, not opening depth. Buy cash scaling follows sells and accounts for fill prices and commissions; it is marked **Not applied** for sells. Expired quantity equals requested minus filled and is never carried to another session. Risk retries have separate per-session intents. No intent is created for a zero delta, missing eligible target or unavailable decision; absence does not establish the strategy's motivation.

Adverse fill cost is signed quantity times (fill price minus reference open); commission is separate. Both are currency amounts recorded by this simulation, not a counterfactual NAV effect or return attribution. Cross-asset share quantities are not summed into a fill-rate ratio.

Select **Selected session only** in the fill ledger to intersect that session with the existing asset/side filters. Counts and pagination follow the intersection, including an explicit empty state. Changing the cursor refreshes it. Equity/fill CSV links still export complete canonical region data. Intent evidence lives in `results.json` and is checked by full numerical replay; lightweight accounting checks alone do not establish intent authenticity. Local hashes can be resealed and are not an independent authenticity service.

## Search commands and execution attempts

Commands opens a searchable native dialog. Search strategy names or verbs such as `find`, `goto`, `fit` and `view`. Each result describes its action. Selecting a result places the exact command in the input, closes the dialog and focuses the input; it does not execute. Press Enter to run. The collapsible syntax reference documents commands with arbitrary date/session arguments. A no-match search gives recovery suggestions. Escape closes the dialog. Alt+Up/Down in the command input browses at most 100 recent submitted commands and restores the draft after the newest entry. Consecutive duplicate submissions are stored once. No history is written to disk, localStorage or a server. Reloading clears it; recalling never runs it.

`find constrained` selects partial or blocked attempts in the **execution finder**, preserving its current asset and reason filters. `find all` or Reset finder clears all three finder filters. The native controls intersect shared asset focus, outcome and recorded reason. Their scope is the full currently inspected strategy/region; outcome/reason criteria remain separate from fill side/session criteria. Up to 12 requests appear per page. Counts refer to requests, not round-trip trades. Partial or blocked means the simulator recorded an exact nonzero residual; rounding residuals can count, so inspect reasons and magnitude. No aggregate cross-asset share rate is invented.

Inspect session selects the request's global session in the current region and updates chart, account, model and execution context. It never refits, changes strategy selection or alters exported evidence. Empty searches retain controls and show an explicit no-match count. Filter changes reset pagination; strategy changes retain filter criteria and reset pagination, so a previously meaningful filter can become empty.

Detailed shares, fill prices, commissions and intent quantities use up to eight significant digits, with scientific notation for very small values. A nonzero quantity is not rounded to displayed zero. These remain display approximations; canonical JSON/CSV retains full stored precision. Portfolio headline currency/percentage summaries are intentionally rounded. Intraday event and fit-boundary rows use full timestamps when multiple sessions share a date. Returns are per recorded session; annual volatility/Sharpe assume 252 sessions per year, which is unsuitable for intraday annualization unless that assumption fits the dataset. This is disclosed rather than silently inferring a market calendar.

## Mobile section navigation

At widths up to 600 px, the header uses a native Go to section picker instead of the horizontal link row. Its options come from the actual desktop section links. The picker resets after a jump, so selecting the same section again works. Fixed-header spacing keeps the target visible. Desktop links also explicitly scroll on repeated activation. Browser checks covered 320 px and 390 px widths; wide evidence tables remain internally scrollable.

## Shared asset focus and complete navigation

Use **Focus asset**, the requested-asset selector in Finder, or the asset selector in the fill ledger to set one shared focus. All three native controls synchronize exact string identifiers. `asset #N` selects a one-based asset from the recorded universe; bare `asset` clears focus. Positional syntax avoids treating a real name such as `all` as a command sentinel. Invalid commands preserve every control. Filtered holdings retain the original position column; they do not renumber the asset matrix.

Asset focus filters holdings, selected-session request rows, the full-region finder and fills. Portfolio headlines, account weights/position counts, session execution costs, events and frozen selection remain whole-portfolio figures. The execution inspector labels its all-session counts and scope. A focused asset can have no matching requests even when the portfolio traded. Changing strategy preserves focus. Finder reset clears shared asset focus plus finder outcome/reason; fill side/session criteria remain intact.

Drawdown Episodes is now present in desktop navigation and the mobile picker. Every section jump transfers keyboard focus to the destination after scrolling, without a second focus scroll. Tab proceeds into that evidence section. Timestamp labels count duplicate dates across the entire source chronology, so pre-region training cutoffs and first decisions retain their full intraday identity.
