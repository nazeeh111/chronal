# CHRONAL 0.1.0 research preview

Public source: [nazeeh111/chronal](https://github.com/nazeeh111/chronal).
Runtime fingerprint: `9723bcd2bb63e53f128dad670f4e8d5972bef9a92634cf52b27476f455c800d7`.

Published on 2026-10-22. The [initial complete CI run](https://github.com/nazeeh111/chronal/actions/runs/39862746760) passed all four Python 3.11–3.14 jobs for source commit `b5d8f6b21b98fc46582088f91913b141ce944ffd`. Each job ran lint/format checks, unit tests, fresh demo/report checks, full demo replay, a two-seed study/replay and package build. The optional report checker ran under Node 22.

Local macOS verification passed 86 tests plus 134 subtests on Python 3.11 and 3.14. All 12 retained study seeds 100–111 were fully replayed under Python 3.11, and the separately installed wheel fully replayed both the demo and complete study outside the source tree. Package byte checks, documentation links and delivery checksums are verified separately.

A follow-up workflow update pins official Node 24-based action releases by commit SHA and uses Ubuntu 24.04 to avoid the previous action-runtime deprecation and moving-runner warning. Check the [live Actions page](https://github.com/nazeeh111/chronal/actions/workflows/checks.yml) for that revision's status; the initial run above is an immutable record, not a claim about every later commit. Runtime Python source is unchanged by this workflow/documentation update.

Private vulnerability reporting remains disabled. [SECURITY.md](../SECURITY.md) documents the supported public issue route and how to request private contact without disclosing sensitive details. No brokerage execution, deployment, paid API or credential change is part of this release. Synthetic outcomes do not establish a trading edge.
