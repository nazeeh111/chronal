# Independent runtime review, terminal refinement

Date: 2026-10-22. Reviewer: independently delegated code-audit specialist.

## Result

No new consequential defect was reproduced in the reviewed financial implementation. This is a scoped source review with executable probes, not proof that every input or market convention is correct.

The current full test suite passed independently on Python 3.14: **73 tests and 117 subtests**, 4.79 seconds in one local observation. Tests were run from the live source tree while other specialists worked on report presentation and additional tests; a final release must be bound to the final complete source hash by the parent.

## Source scope

Read all runtime modules: data, spec, strategies, engine, evaluation, analytics, artifacts, study, CLI, initialization/entry points and current report; read METHOD/README/SECURITY/VALIDATION for claimed contracts. Report source is being revised concurrently, so the retained financial-module hash manifest intentionally excludes report.py. The manifest is in `work/terminal-code-audit/results.json`.

Reviewed train-only ridge scaling and label endpoints; publication availability; target-capping and covariance scaling; later-open execution; gaps/capacity; shared cash and fees; late-mark risk snapshots; fold continuity and fresh holdout capital; prospective refits within holdout; selection freezing and full replay; CSV/report derivation; monthly returns, tail conventions and drawdown episode semantics; CLI failure handling and inert proposal/report data.

## Additional independent probes

`work/terminal-code-audit/probe.py` completed **360 newly generated randomized paths** using fixed RNG seed 814, independently from prior retained review probes:

- One, two and four assets; execution delays zero, one and three sessions.
- Random gaps and intraday returns, zero/thin/deep capacity, randomized target allocations and no-decision rows, delayed bar publication, nonzero fees/spread/slippage and latched risk stops.
- Exact prefix equality for fills, events and NAV when all later observations are removed.
- Independent calculation of each fill price and fee, normal/risk volume eligibility and participation bound, cash, shares and marked account NAV.
- Independent month-by-month compounding and identical-book baseline excess identity.

All assertions passed. This adds evidence for implementation invariants, not market profitability or stress calibration. No live data, brokerage, credentials, external engine or separately billed API was used.

## Limits and follow-up

The report uses spread arguments in `Math.min(...all)` and `Math.max(...all)` when finding chart bounds. Very long accepted histories may exceed browser argument limits. The parent was informed to replace these with a streaming/reduce bound calculation during the terminal UI edit; this does not affect recorded financial results. Browser interaction and final presentation remain parent-owned verification.

Normal `verify` checks local integrity and ledger consistency; complete semantic recomputation requires `--replay`. Unsigned resealed bundles are not authentic preregistration. The documented realized daily-volume proxy, open-price sizing, fixed universe, lack of corporate actions/dividends, 252-session annualization and absence of real-market validation remain material scope limits rather than newly discovered defects.

I did not certify packaging, final source/hash binding, performance across arbitrary dataset sizes, exhaustive security, all operating systems or all possible float magnitudes. Parent should rerun required final checks after concurrent edits and retain the exact release source fingerprint.

## Final terminal and ledger integration addendum

Accepted runtime SHA-256: `a5aa4f40bcc80e3918d529ff00f675b7f1907b9f78383e4c6ee49486a29a4d88`.

Reviewed the new ledger diagnostics and terminal report integration after parent changes. The large-history spread-argument chart bound concern is corrected with reduction. New account values use the corresponding selected-session marked NAV and cash; holdings are labeled shares, not inferred asset weights. Monthly rows retain partial-month disclosure. Terminal commands are explicit allowlisted operations, with no evaluation, shell, model, trading or network execution. Inserted record metadata remains encoded JSON and DOM text; chart-generated HTML incorporates numeric values and normalized dates.

One concrete edge was discovered: `all` is a valid imported asset identifier, but conflicted with the fill selector's previous All assets sentinel. The parent changed the sentinel to the empty string, which cannot be a valid asset name. `work/terminal-code-audit/filter-probe.py` executes the actual extracted report `fills()` function under Node and verifies a named `all` asset independently from no filter, buy-only, sell-only and no-match disabled pagination states. All passed. This is retained task-local behavioral evidence, not an added test that mirrors implementation strings.

The same probe confirms byte-deterministic HTML rendering and round-trips hostile closing-script metadata through the encoded inert JSON record without permitting the literal executable script sequence. This does not constitute exhaustive browser security testing.

`work/terminal-code-audit/ledger-probe.py` independently recalculates session fill counts/notional/commission, cumulative fees, cash/invested weights and value, active share positions and terminal holdings across 360 paths. All passed. It also retains the financial causal/accounting checks from the original probe. Inputs cover zero/thin capacity, nonzero transaction costs, changing holdings, late publications, risk liquidation and varying delays/assets.

Command errors hidden on narrow screens and invalid-date input restoration were identified and corrected by the parent. I read those current changes; actual browser layout/interaction acceptance remains with the parent. No new unresolved consequential finding remained within this integration review scope. The earlier 73-test/117-subtest run predates this final report integration; the parent must run final suite and packaging checks on this exact source or superseding source.

## Final frozen-selection disclosure acceptance

Final accepted runtime SHA-256: `6ee5713642056a0e27733752fd529fd4a0be55ba43affc6b46334b0a69cdc8aa`.

Independently verified the only runtime change after the integration acceptance: one literal HTML badge, `<span class="badge">Frozen selection: __WINNER__</span>`, beside the strategy selector. Removing precisely that one occurrence reconstructs the previously accepted complete package hash `a5aa4f40bcc80e3918d529ff00f675b7f1907b9f78383e4c6ee49486a29a4d88`. No financial, ledger, command or filtering behavior changed. The existing HTML-escaped winner substitution applies to this additional disclosure. This narrow acceptance carries the prior review forward; it is not a fresh exhaustive review or a claim of repeated financial probes after the badge change.

## Retained command-logic regression tool

The task-local JavaScript behavior probe is now portable as `tools/check_report.cjs`. Run it with Node against a trusted current generated `report.html`; no npm dependencies are required. It extracts and executes the actual command and fill-filter functions, supplying small logic dependencies rather than pretending to implement a browser DOM. Assertions cover allowed/unknown/prototype-name commands, frozen selection, valid sessions and unavailable-date restoration, legitimate asset name `all`, buy/sell signs, no matching fills and 16-fill pagination boundaries. The checker passed against a fresh current render; `node --check` passed. CI now checks generated development and holdout reports with Node 22, and source-distribution rules include the helper. Runtime sources and the accepted runtime hash are unchanged. Existing checked-in reports must be regenerated before this tool can validate the terminal logic they are supposed to contain.
