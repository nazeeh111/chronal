# CHRONAL final publication research

## Decision

A worthwhile next improvement is a portable **inspection-state record**, bound to the exact evaluated report. This addresses an actual gap in a dense research terminal: someone can identify a blocked request or a suspicious fit but cannot preserve the strategy, session, interval, and filters that exposed it. A saved inspection is a view of an existing immutable evaluation, never a new strategy selection or a rerun.

The strongest transfer is not a new chart library. It is FINOS Perspective's separation of fallible validation from a single state commit, combined with Panel's explicit typed parameter mapping. No new dependency, server, account, browser storage, or live trading integration is needed. A JSON export/import is a portable fallback when clipboard APIs and file-URL fragments are unavailable. This is a proposal from inspected source, not an implemented or locally replicated feature in this research task.

## Source inspection and counterchecks

Fourteen actual implementation, test, documentation and license files from three previously unregistered repositories were retrieved at complete commit SHAs. [PUBLICATION_SOURCES.json](PUBLICATION_SOURCES.json) records their raw URLs and SHA256 hashes. No upstream source was copied into CHRONAL, executed, or installed.

### FINOS Perspective

Commit `0857a7d9c1e34f9d82496b8a81f6778944178b85`, Apache License 2.0.

The decisive source is `rust/perspective-viewer/src/rust/tasks/transactional_restore.rs`: prepare validates the plugin and target, prepares the view, and validates plugin/column configuration before producing a Prepared value. Commit writes the session and renderer without an intervening asynchronous wait. This is more specific evidence than the documentation's general save/restore promise.

`packages/viewer-datagrid/test/js/transactional_restore.spec.ts` includes invalid column settings combined with a valid grouping change, unknown columns, unknown plugins, invalid expressions, and valid combined changes. Rejections assert that saved state equals the prior state and no render occurs; a following valid restore still works. `rust/perspective-viewer/test/js/viewer_api/save_restore.spec.ts` checks a saved configuration round trip through reset. These are upstream tests inspected statically, not tests run locally.

Counterevidence: Perspective's documentation allows restoration against a table of identical schema. Identical columns do not mean identical dataset, evaluated region, model registration, or strategy results. CHRONAL therefore needs stricter record binding than this general visualization system. Partial restore and null/reset semantics are convenient upstream but add ambiguity to a small audit record; use a complete versioned record initially.

Primary links:
- https://github.com/finos/perspective/blob/0857a7d9c1e34f9d82496b8a81f6778944178b85/rust/perspective-viewer/src/rust/tasks/transactional_restore.rs
- https://github.com/finos/perspective/blob/0857a7d9c1e34f9d82496b8a81f6778944178b85/packages/viewer-datagrid/test/js/transactional_restore.spec.ts
- https://github.com/finos/perspective/blob/0857a7d9c1e34f9d82496b8a81f6778944178b85/docs/md/how_to/javascript/save_restore.md

### HoloViz Panel

Commit `25bd3e07e41bd73e26b22ef0f9a532ea0aed16a3`, BSD 3-Clause.

`panel/io/location.py` explicitly maps external parameter names to registered internal parameters, ignores unrelated query keys, preserves raw strings before typed deserialization, and routes update failure to a callback. Its synchronization guard prevents a URL update from recursively updating itself. `panel/tests/io/test_location.py` covers selected parameter subsets, renamed parameters, negative integers, invalid typed values, partial unsynchronization, and numeric/JSON-looking strings such as `007`, `true`, and `[1, 2]` remaining strings.

Transfer: strategy and asset identifiers must be validated as exact strings from the report, while session/range positions must be bounded integers. Avoid a generic coercion function that converts a real asset named `007` into the number 7 or treats `all` as an unescapable sentinel. Register the allowed fields rather than spreading untrusted JSON into global state.

Counterevidence: Panel supports a broad dynamic Python parameter ecosystem and URL state intended for applications. That architecture would add a server and dependencies to CHRONAL without solving its narrow offline need. Its observed error callback is not evidence of transactional all-or-nothing updates across all parameter owners. CHRONAL should explicitly validate the entire record before changing any UI field.

Primary links:
- https://github.com/holoviz/panel/blob/25bd3e07e41bd73e26b22ef0f9a532ea0aed16a3/panel/io/location.py
- https://github.com/holoviz/panel/blob/25bd3e07e41bd73e26b22ef0f9a532ea0aed16a3/panel/tests/io/test_location.py

### Datasette

Commit `a8e13cc489b41f2f9a5aa691f5eb1bedf99a0e0b`, Apache License 2.0.

`datasette/views/base.py::stream_csv` distinguishes the first page from all matching rows, follows explicit pagination when streaming, emits one heading row, and writes using a CSV writer rather than concatenating cell strings. `tests/test_csv.py::test_table_csv_stream` checks a normal export returns 100 rows and streaming returns 1001. The view streaming test additionally checks no duplicate rows. Non-ASCII text and response headers are tested separately.

Transfer: if CHRONAL adds a CSV export of the execution finder, export **all matching attempts**, not the current twelve-row page. Label filtered export separately from canonical fills/equity exports. Include exact unrounded numeric values, timestamp, strategy, asset and globally stable session index. Preserve filter context in a separate JSON record so CSV is not mistaken for the complete immutable research artifact.

Counterevidence: Datasette documents streaming truncation and can append an error into the response after a 200 response has started; its size-limit test is explicitly marked flaky. That is unsuitable as proof of complete audit export. CHRONAL already has all matching rows in memory, so build the complete output before offering a download. The inspected CSV path uses ordinary quoting, which does not establish spreadsheet formula safety for arbitrary string cells. JSON remains the exact audit interchange; any spreadsheet-safe CSV policy must be explicit because prefixing dangerous text changes its value. Avoid importing a networked SQL publisher for a browser-local export.

Primary links:
- https://github.com/simonw/datasette/blob/a8e13cc489b41f2f9a5aa691f5eb1bedf99a0e0b/datasette/views/base.py
- https://github.com/simonw/datasette/blob/a8e13cc489b41f2f9a5aa691f5eb1bedf99a0e0b/tests/test_csv.py
- https://github.com/simonw/datasette/blob/a8e13cc489b41f2f9a5aa691f5eb1bedf99a0e0b/docs/csv_export.rst

## Bounded implementation contract

Preferred first version: a copyable/pasteable JSON inspection record, optional local download. Suggested fields: format identifier, schema version, exact report binding, inspected strategy, chart mode, selected global session index, inclusive interval endpoints, fill filters, execution finder filters, section. Store exact string identifiers, booleans and integers. Do not store results, coefficients, credentials, arbitrary DOM selectors, HTML, URLs, or executable commands.

Binding should cover more than data/code SHA: use the locked plan (including registered candidates), stage, and actual evaluated report result identity. Two seeds with identical schema, development and holdout reports from one plan, or two execution configurations must not accept one another's record. A SHA256 of deterministic source payload bytes is a compatibility binding, not authentication against a maliciously modified report.

Validate file/text size, plain object shape, exact schema version, allowed keys, report binding, own-property strategy membership, exact enum values, booleans, finite bounded integer indices, ordered interval inside that strategy's region, exact asset/reason membership. Reject the whole record if any field is invalid. Validate into a separate object, then assign fields and update in a deterministic order. Update should not replace the frozen winner or mutate evaluation payloads. A model-fit dropdown is derived from the session, so do not save contradictory fit and session fields. Do not save pagination unless the complete filtered state is restored first; resetting to page one is less ambiguous.

Meaningful checks: complete round trip; malformed/oversized JSON; wrong report/plan/stage; unknown schema, field, strategy, enum or asset; fractional, negative, infinite and out-of-range indices; reversed/out-of-region interval; mixed valid/invalid record leaves every control unchanged; prototype-like names handled by membership checks; identifiers containing quotes, Unicode, numeric-looking text, `all`, `__proto__`; empty matching attempts; winner/results immutable. A saved state should restore offline and on a fresh browser, without localStorage or a service worker.

If this is too much scope for the final run, prefer a read-only inspection JSON export with explicit contents over a partially validated importer. A shared asset selector that synchronizes holdings/fills/attempts is another useful route, but silent reset or propagation of asset filters across strategy changes can conceal evidence, so show its active scope explicitly.

## Limits

This inspection supports concrete workflow and validation mechanisms. It does not establish CHRONAL's novelty, institutional readiness, profitability, security completeness, or superiority over upstream projects. Source count is not quality evidence. The previous registry contains 29 distinct repos; these three produce 32 only after integrating this registry. No upstream runtime or benchmark was executed.

## Delivered scope

This release chooses the bounded shared-asset workflow: native selectors and `asset #N` synchronize exact asset identifiers across holdings, selected-session request rows, finder and fills. Clearing uses a distinct empty sentinel, preserving literal names such as `all`. Portfolio totals remain unchanged and visibly labeled. The observed-state import/export proposal remains future work; no importer or claim of implemented saved-state restoration is added. Inspection of typed external state informed exact identifier membership and validation-before-mutation for asset commands.
