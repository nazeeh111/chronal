"""Editable, source-grounded PaperBanana figures; no model or network calls.

Run from the repository root. SVG remains the vector master. Use the documented
PaperBanana renderer, or any ordinary SVG viewer, to inspect fresh previews.
"""

import argparse
import html
import json
import math
from pathlib import Path


INK = "#183335"
MUTED = "#566b6c"
LINE = "#cad6d5"
TEAL = "#237568"
GOLD = "#ac7225"
PURPLE = "#7760a6"
RED = "#ae594a"


class Figure:
    def __init__(self, width, height, title, description):
        self.width, self.height = width, height
        self.parts = [
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
            f'viewBox="0 0 {width} {height}" role="img" aria-labelledby="figure-title figure-desc">',
            f'<title id="figure-title">{html.escape(title)}</title>',
            f'<desc id="figure-desc">{html.escape(description)}</desc>',
            '<defs><marker id="arrow" markerWidth="8" markerHeight="8" refX="7" refY="4" '
            f'orient="auto-start-reverse"><path d="M0 0L8 4L0 8Z" fill="{MUTED}"/></marker></defs>',
            f'<rect width="{width}" height="{height}" fill="white"/>',
        ]

    def text(
        self, x, y, content, *, size=20, color=INK, anchor="start", family="Arial,sans-serif", weight=400
    ):
        self.parts.append(
            f'<text x="{x}" y="{y}" fill="{color}" font-family="{family}" font-size="{size}" '
            f'font-weight="{weight}" text-anchor="{anchor}">{html.escape(str(content))}</text>'
        )

    def rect(self, x, y, w, h, fill="white", stroke=LINE, radius=9):
        self.parts.append(
            f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{radius}" fill="{fill}" stroke="{stroke}" stroke-width="1.6"/>'
        )

    def edge(self, identity, path, *, dashed=False):
        dash = ' stroke-dasharray="8 6"' if dashed else ""
        self.parts.append(
            f'<path id="{identity}" d="{path}" fill="none" stroke="{MUTED}" stroke-width="2.2"{dash} marker-end="url(#arrow)"/>'
        )

    def node(self, identity, x, y, title, lines, *, color=TEAL, fill="#f0f7f4", width=300, height=120):
        self.parts.append(f'<g id="{identity}"><title>{html.escape(title)}</title>')
        self.rect(x, y, width, height, fill)
        self.parts.append(
            f'<path d="M{x + 1} {y + 18}V{y + height - 18}" stroke="{color}" stroke-width="4"/>'
        )
        self.text(x + 22, y + 35, title, size=24, weight=600)
        for i, line in enumerate(lines):
            self.text(x + 22, y + 65 + i * 25, line, size=18, color=MUTED)
        self.parts.append("</g>")

    def header(self, number, title, subtitle):
        self.text(64, 47, f"CHRONAL / {number}", size=15, color=TEAL, family="monospace")
        self.text(64, 99, title, size=39, family="Georgia,serif")
        self.text(64, 134, subtitle, size=20, color=MUTED)

    def save(self, path):
        path = Path(path)
        if path.exists():
            raise ValueError(f"refusing to overwrite a figure: {path}")
        path.write_text("\n".join([*self.parts, "</svg>"]) + "\n")


def architecture(out):
    f = Figure(
        1600,
        940,
        "Chronal research lifecycle",
        "Validated data and bounded hypotheses become a locked plan, chronological development, "
        "cash-ledger evidence, a frozen selection and a separate holdout. Only development evidence "
        "feeds AI critique for a new plan. Every stage retains replayable records.",
    )
    f.header(
        "FIGURE 01",
        "From hypothesis to replayable evidence.",
        "A local research workflow. No live execution path or language-model API is present.",
    )
    f.node("input-contract", 64, 210, "Declare the inputs", ["OHLCV + availability", "Bounded strategy JSON"])
    f.node(
        "locked-plan",
        430,
        210,
        "Lock the experiment",
        ["Data, candidates and code", "Costs + chronological windows"],
    )
    f.node(
        "development-folds",
        796,
        210,
        "Fit, decide, simulate",
        ["Train-only models and scaler", "Later-open cash / costs / risk"],
        color=PURPLE,
        fill="#f5f2fa",
    )
    f.node(
        "development-evidence",
        1162,
        210,
        "Development evidence",
        ["All registered candidates", "Fold metrics + stress tests"],
    )
    for i, x in enumerate([364, 730, 1096]):
        f.edge(f"edge-development-{i}", f"M{x} 270H{x + 66}")
    f.node(
        "frozen-selection",
        1162,
        450,
        "Freeze one candidate",
        ["Development Sharpe rule", "Exact registered specification"],
        color=GOLD,
        fill="#fcf6ec",
    )
    f.edge("edge-freeze", "M1312 330V450")
    f.text(1330, 394, "selection boundary", size=16, color=GOLD)
    f.node(
        "separate-holdout",
        796,
        450,
        "Open the holdout",
        ["Frozen candidate + baseline", "New cash book; earlier-only fits"],
        color=GOLD,
        fill="#fcf6ec",
    )
    f.node(
        "holdout-record",
        430,
        450,
        "Retain the outcome",
        ["Report, fills, positions, CSVs", "No candidate reselection"],
    )
    f.node(
        "verification",
        64,
        450,
        "Verify and replay",
        ["Cash / shares / fees / NAV", "Source, exports and selection"],
    )
    for i, x in enumerate([1162, 796, 430]):
        f.edge(f"edge-holdout-{i}", f"M{x} 510H{x - 66}")
    f.node(
        "ai-packet",
        1162,
        710,
        "AI review packet",
        ["Development evidence only", "Holdout observations excluded"],
        color=PURPLE,
        fill="#f5f2fa",
    )
    f.node(
        "new-hypotheses",
        796,
        710,
        "Critique the mechanism",
        ["Existing user assistant", "Return bounded JSON; no code"],
        color=PURPLE,
        fill="#f5f2fa",
    )
    f.node(
        "new-plan",
        430,
        710,
        "Register a new plan",
        ["Preserve previous trial history", "Use new confirmatory data"],
        color=PURPLE,
        fill="#f5f2fa",
    )
    f.edge("edge-development-packet", "M1462 270H1525V770H1462", dashed=True)
    f.text(1312, 687, "Only this evidence enters critique", size=16, color=PURPLE, anchor="middle")
    f.edge("edge-packet-critique", "M1162 770H1096", dashed=True)
    f.edge("edge-critique-new-plan", "M796 770H730", dashed=True)
    f.edge("edge-new-plan-registration", "M580 830V872H34V371H580V330", dashed=True)
    f.text(
        64,
        910,
        "Solid: evaluated experiment     Dashed: optional hypothesis revision     Both evaluated stages retain full evidence bundles.",
        size=17,
        color=MUTED,
    )
    f.save(out / "research-lifecycle.svg")


def chronology(out):
    f = Figure(
        1600,
        920,
        "Chronal information and execution clocks",
        "The default split fits on sessions0 through251, purges252 and253, then tests254 onward. "
        "A close-t decision fills at a later open, never the same close. Delayed publication blocks "
        "a close-time decision and cannot be retroactively used at that cutoff.",
    )
    f.header(
        "FIGURE 02",
        "Time is part of the model.",
        "Illustrative timing schematic; widths are not proportional to elapsed time.",
    )
    f.text(64, 200, "A / CHRONOLOGICAL FIT", size=17, color=TEAL, weight=600)
    x = [64, 640, 850, 1250]
    w = [550, 184, 374, 286]
    colors = ["#edf5f1", "#f8eee8", "#f4f1fa", "#fcf4e7"]
    labels = [
        ("TRAIN", "[0,252)"),
        ("PURGE", "252,253"),
        ("FIRST TEST", "[254,317)"),
        ("HOLDOUT", "[630,756)"),
    ]
    for i in range(4):
        f.rect(x[i], 227, w[i], 98, colors[i])
        f.text(x[i] + 18, 262, labels[i][0], size=21, weight=600)
        f.text(x[i] + 18, 297, labels[i][1], size=22, family="monospace")
    f.text(
        64,
        365,
        "Ridge feature at close k → label open[k+2] / open[k+1] −1; every label endpoint is before the exclusive fit cutoff.",
        size=20,
        color=MUTED,
    )
    f.text(
        64,
        404,
        "Later folds expand training using earlier observations. The candidate specification stays frozen during the holdout.",
        size=20,
        color=MUTED,
    )
    f.text(64, 480, "B / DECISION AND FILL", size=17, color=TEAL, weight=600)
    f.node(
        "observed-close",
        64,
        510,
        "Close t",
        ["Required bars have arrived", "Propose target weights"],
        width=360,
    )
    f.node(
        "eligible-open",
        620,
        510,
        "Open t+1 (+ delay)",
        ["Resolve cash-aware quantities", "Adverse prices + commission"],
        width=410,
    )
    f.node(
        "realized-mark",
        1190,
        510,
        "Fill-session close",
        ["Ex-post portfolio NAV", "Publication-aware risk state"],
        width=346,
    )
    f.edge("edge-close-open", "M424 570H620")
    f.edge("edge-open-mark", "M1030 570H1190")
    f.text(521, 542, "no same-close fill", size=17, color=GOLD, anchor="middle")
    f.text(64, 708, "C / LATE PUBLICATION", size=17, color=TEAL, weight=600)
    f.rect(64, 735, 1472, 115, "#fcf7f4")
    f.text(
        88,
        773,
        "If a required bar arrives after close t: no new target at that cutoff; existing holdings remain.",
        size=23,
        weight=600,
    )
    f.text(
        88,
        810,
        "A later arrival cannot rewrite the earlier decision. Risk uses recorded equity snapshots only once their marking bars are published.",
        size=20,
        color=MUTED,
    )
    f.text(
        64,
        890,
        "Opening-price sizing and realized daily-volume capacity remain declared approximations, not a reconstructed opening auction.",
        size=18,
        color=MUTED,
    )
    f.save(out / "causal-timing.svg")


def study_plot(out, study_path):
    study = json.loads(Path(study_path).read_text())
    rows = study["observations"]
    assert len(rows) == study["summary"]["replications"] and len({r["seed"] for r in rows}) == len(rows)
    assert all(isinstance(r["holdout_excess_total_return"], (int, float)) for r in rows)
    f = Figure(
        1600,
        1070,
        "Chronal synthetic selection study",
        "All12 declared synthetic replications are shown. Each row compares selected candidate excess "
        "total return over the fixed baseline on development and holdout. This is synthetic data, "
        "not investment performance. No uncertainty bars or significance claims are added.",
    )
    f.header(
        "FIGURE 03",
        "Selection is not confirmation.",
        "Synthetic demonstration · all 12 predeclared seeds retained · excess total return in percentage points",
    )
    f.text(64, 194, "SEED / DEVELOPMENT WINNER", size=16, color=MUTED)
    centers = [700, 1260]
    span = 215
    points = [
        row[key] * 100
        for row in rows
        for key in ("development_excess_total_return", "holdout_excess_total_return")
    ]
    if not all(math.isfinite(point) for point in points):
        raise ValueError("study points must be finite")
    limit = max(5, math.ceil(max(abs(point) for point in points) / 5) * 5)
    for center, label in zip(centers, ["DEVELOPMENT", "LATER HOLDOUT"]):
        f.text(center, 194, label, size=19, anchor="middle", weight=600)
        for tick in [-limit, -limit / 2, 0, limit / 2, limit]:
            xx = center + tick / limit * span
            f.parts.append(
                f'<path d="M{xx} 225V905" stroke="{LINE if tick else MUTED}" stroke-width="{1 if tick else 1.8}"/>'
            )
            f.text(xx, 943, f"{tick:+g}" if tick else "0", size=17, color=MUTED, anchor="middle")
    for i, row in enumerate(rows):
        y = 250 + i * 55
        f.text(64, y + 7, str(row["seed"]), size=21, family="monospace")
        f.text(145, y + 7, row["selected"], size=21)
        for center, key, color in zip(
            centers, ["development_excess_total_return", "holdout_excess_total_return"], [TEAL, GOLD]
        ):
            value = row[key] * 100
            if not -limit <= value <= limit:
                raise ValueError("study point exceeds the declared plot scale; choose a wider shared scale")
            endpoint = center + value / limit * span
            f.parts.append(f'<path d="M{center} {y}H{endpoint}" stroke="{color}" stroke-width="9"/>')
            f.parts.append(f'<circle cx="{endpoint}" cy="{y}" r="6" fill="{color}"/>')
            f.text(
                endpoint + (12 if value >= 0 else -12),
                y + 7,
                f"{value:+.2f}",
                size=18,
                color=INK,
                anchor="start" if value >= 0 else "end",
            )
    summary = study["summary"]
    observed = [row["holdout_excess_total_return"] for row in rows]
    assert sum(value > 0 for value in observed) == summary["positive_holdout_excess_count"]
    assert math.isclose(
        math.fsum(observed) / len(observed), summary["mean_holdout_excess_total_return"], abs_tol=1e-12
    )
    f.text(
        64,
        1002,
        f"{summary['positive_holdout_excess_count']}/{summary['replications']} positive holdout excess outcomes. Mean: {summary['mean_holdout_excess_total_return'] * 100:+.2f} pp. One hand-designed generator; no real-market inference.",
        size=23,
        weight=600,
    )
    f.text(
        64,
        1040,
        "Source: examples/selection-study/results.json. Zero is a genuine reference; shared scales; no dropped seeds or invented error bars.",
        size=18,
        color=MUTED,
    )
    f.save(out / "synthetic-selection.svg")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--study", type=Path, default=Path("examples/selection-study/results.json"))
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    architecture(args.out)
    chronology(args.out)
    study_plot(args.out, args.study)


if __name__ == "__main__":
    main()
