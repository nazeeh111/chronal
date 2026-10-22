# Publication pass review

Runtime fingerprint: `9723bcd2bb63e53f128dad670f4e8d5972bef9a92634cf52b27476f455c800d7`.
Reviewed locally on 2026-10-22.

## Reproduced core findings

MarketData accepted exact UTC-microsecond arrays outside the CSV reader's supported calendar range. Years 0000 and 10000 could therefore produce an unusable locked plan through the Python API. All three timestamp arrays now reject years outside 0001–9999. Boundary-year CSV round trips preserve exact data and semantic hashes. This changes accepted input bounds, not normal simulated returns.

FreshDirectory used Path.exists(), which treats dangling symlinks as absent. Its final rename could replace an existing dangling destination despite the no-overwrite contract. Entry and immediately-before-rename checks now also refuse symlinks. Regression tests preserve both a preexisting dangling link and one appearing before the final check. These checks do not establish exclusion against a noncooperating filesystem writer racing after that check; no cross-process lock or platform-specific no-replace rename is claimed.

## Reproduced terminal findings

Episodes was omitted from desktop links and consequently from the mobile picker. It is now included. Programmatic section jumps scrolled without transferring focus; destinations are now focusable and focused with preventScroll after explicit scrolling. Intraday day counts covered only evaluated indices, so a pre-region cutoff could collapse to a date. Counts now cover every source timestamp.

A shared asset context synchronizes exact identifiers across three native selectors and filters holdings, selected-session intent rows, full-region finder and fills. It preserves all portfolio totals and clearly labels whole-session execution metrics. `asset #N` avoids ambiguous names; bare `asset` clears focus. The independent checker covers literal `all`, spaces/punctuation, invalid/unsafe positions, all control synchronization, original holdings-column mapping, empty intersections, retained side/session/reason/outcome filters, reset, strategy changes, unchanged result bytes and winner.

## Verification and boundaries

86 tests plus 134 subtests passed locally on Python 3.11 and 3.14. Ruff lint/format passed 24 Python files. Both current reports passed the expanded Node helper/static checker. The source-lock test that failed while report.py changed concurrently passed once runtime edits settled; final integrated checks use settled bytes.

Actual desktop browser observation focused SYN_C on 2019-09-18: all three selectors agreed, holdings showed 328.18464 shares, and the request row showed 328.77392 requested / 328.18464 filled / 0.58927527 expired. Whole-portfolio counts remained 4 intents/4 fills with 78.08 currency adverse fill cost and 78.08 commission. Native section navigation focused Execution; the next Tab reached Next event. On 390 px mobile, Episodes was selectable, positioned about 82 px below the top and received focus. `asset #2` selected SYN_B while account totals still reported 2 portfolio positions and 4 fills. Screenshots: [desktop focus](assets/asset-focus.png), [mobile account](assets/asset-mobile.png).

The fresh prepublication privacy/license/quickstart review found no consequential blocker: intended public files contain no local absolute paths, suspicious credential filenames, symlinks or PNG identity chunks. No credential stores were inspected. The final staged scope and remote commit are separately verified during publication. Upstream 32-project registry is design evidence, not a quality grade or profitability proof. Saved inspection-state restore remains proposed, not implemented.
