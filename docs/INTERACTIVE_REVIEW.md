# Independent terminal usability audit

Reviewed current `chronal/report.py`, `tools/check_report.cjs`, `chronal/data.py`, `chronal/ledger.py`, generated-report contract and terminal documentation. This is source/logic review; no claim of fresh browser layout coverage.

## Findings for correction

1. **Malformed or cleared exact date loses synchronized display.** The date change handler sends `session ` after clearing the native input. Its generic error path leaves a blank date while cursor/account retain their previous session. Restore the prior valid display for every invalid session request, including blank/malformed arguments. The durable checker currently covers valid-but-unavailable dates only.
2. **Same-date sessions have ambiguous exact lookup.** Accepted synchronized panels require strictly ordered nonoverlapping timestamps, but permit multiple sessions on one UTC date. `dateAt` truncates timestamps to YYYY-MM-DD and the session command silently chooses `findIndex`. Detect multiple matches and request the slider rather than silently choosing the first. Timestamp-bearing cursor readout would make this input understandable. This is display inspection, not a financial simulation defect.

## Existing behavior that is sound

- Registered strategy lookup uses own-property checks and keeps development selection immutable.
- Signed fills and asset filters are actual-record based. The empty-string all-assets sentinel handles a legal asset named `all`.
- Equity cursor mapping correctly offsets the prepended initial-cash point.
- Calendar matrix distinguishes missing observations with a dash and zero with a signed/rounded numeric return.
- NAV/cash and inventory disclosures distinguish shares from asset value. The report does not invent concentration from share quantities.
- User-controlled names enter DOM through textContent; JSON escapes `<`, `>` and `&` before script embedding.
- Risk/uncertainty explicitly use the frozen development candidate rather than silently following inspection.
- Native slider and dropdowns provide keyboard operation. Current command allowlist cannot execute code or orders.

## Interaction acceptance needed for current upgrade

Parent is implementing selected-range comparison diagnostics and chart/month/episode links. Verify: click coordinates respect SVG letterboxing; left/right endpoints map to first/last sessions with prepended capital excluded; month range starts at the prior evaluated NAV (or initial cash at region start); same-session ranges remain valid; reversed/outside ranges reject without partial state updates; candidate switching updates range comparison while frozen selection stays unchanged; sparse/no-fill ranges display explicit empty state. Browser QA must cover narrow/desktop because Node function tests do not validate DOM event wiring, SVG geometry, keyboard focus, scroll or responsive layout.

No unrelated runtime edits made by this reviewer.

## Follow-up acceptance: interactive implementation

Reviewed the updated source and ran the extended durable checker against both `work/interactive-demo-v1/development/report.html` and its holdout report. Actual extracted helpers now tested: resolveSession, chooseSession, windowMetrics, setRange, applyRange, chartSessionFromX, runCommand, and existing fills/command status.

Both date findings are addressed: blank/malformed date requests restore the synchronized previous date; repeated UTC dates reject ambiguous date lookup and support exact 1-based #N positions, with timestamp-bearing contextual labels. New monthly/episode actions use native buttons. Pointer translation uses inverse SVG screen transformation, which correctly accounts for aspect-ratio scaling/letterboxing by construction; browser verification remains separate.

Independent hand calculation: selected sessions 1–2 of NAV [110,99,108] on initial cash 100 begin from prior NAV110, return108/110−1, drawdown−10%, commissions3+5=8, filled notional abs(−2)*12+abs(1)*14=38. Tests cover that interval, first/single session, no-fill interval, reversed/outside/noninteger intervals preserving prior endpoints without rerender, malformed/unavailable dates, duplicate dates, invalid and oversized positions, complete reset, unchanged frozen selection, and cursor mapping for every plotted point of a20-session path. Node syntax and both actual report logic checks passed.

No unresolved consequential finding from this source/logic review. This does not establish browser event wiring, visual layout, focus behavior or real-market validity.

## Final source acceptance

Independently recomputed runtime fingerprint: `a8191953bef6aacb95e926c947b1581ad29ac01109ac2a347864801e4ea14d0e`.

Read final source changes: excess comparison now correctly labels return subtraction in percentage points; month buttons expose both interval and signed return in their accessible name; chart pointer handler ignores non-primary buttons before coordinate translation; episode heading discloses the up-to-eight limitation. The source-level changes preserve previously accepted numerical accounting and synchronized-selection behavior.

Re-ran the extended durable checker successfully against both `work/interactive-demo-final/development/report.html` and `work/interactive-demo-final/holdout/report.html`. No unresolved consequential source/logic findings within this review. Parent separately reports successful actual desktop chart-center selection, January2019 month interval selection, and worst-trough account synchronization. Those are parent-observed browser evidence, not independently observed by this reviewer; mobile/browser acceptance remains the parent's separate gate.

## Native anchor regression correction

Parent browser verification caught a duplicate static `interval` ID shared by the new comparison section and previous uncertainty paragraph. This demonstrates the earlier pure helper tests did not validate actual native anchor navigation. Parent renamed the uncertainty paragraph to `uncertainty-interval` and updated its text target; reviewer added durable inspection of the actual static markup before the first script, excluding embedded JSON/JS strings. The checker now rejects duplicate IDs, requires exactly one target for every static native hash link, requires `#interval` to be the comparison section, and requires the uncertainty paragraph to use its distinct ID.

Both `work/interactive-demo-v3` region reports passed. Negative regression: prior `work/interactive-demo-final/development/report.html` was rejected specifically for its duplicate static IDs. Independently recomputed corrected source fingerprint: `4acb12e6843c78bc6631717cb3d6e8ed828b3943641e8cf950d8928a0638a72f`. This supersedes the preceding acceptance hash. Actual corrected browser navigation remains separately verified by the parent.

## Repeated-section navigation regression correction

Parent browser testing found that assigning an already-current hash did not restore the comparison section after browser-driven button focus scrolling. Reviewed actual `navigateSection` helper and all command, month, range and trough call sites. The helper assigns the hash and explicitly calls target.scrollIntoView with block:start on every invocation.

The durable checker extracts this actual helper, stubs target scrolling and asserts two repeated identical `interval` navigations produce two scrolling calls while preserving the same hash. This verifies repeated invocation behavior, not actual browser scroll geometry. Both `work/interactive-demo-v4` reports passed all static and logic checks. Independently recomputed current runtime fingerprint `f3785a53808b331a25d4bd8ae8a844b32bea604b5cf96fe4163df820b4e8a6d4`, superseding preceding acceptance hashes. Parent remains responsible for actual browser re-verification.
