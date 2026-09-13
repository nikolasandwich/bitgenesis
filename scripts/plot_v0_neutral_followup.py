"""Plot all four verified neutral follow-ups, including the entire saved horizon."""

import argparse
import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import StrMethodFormatter

from summarize_v0_neutral_followup import read_rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=Path("data/campaign-015"))
    parser.add_argument("--verification", type=Path, default=Path("docs/research/results/campaign-015-verification.json"))
    parser.add_argument("--output", type=Path, default=Path("docs/research/figures/campaign-015-followup"))
    args = parser.parse_args()
    targets = [args.output.with_suffix(s) for s in (".png", ".svg", ".json")]
    if any(p.exists() for p in targets):
        raise FileExistsError("Choose a new figure prefix")
    report = json.loads(args.verification.read_text(encoding="utf-8"))
    cases = [(1, 72, 1206), (2, 8, 1200), (2, 72, 1208), (4, 72, 1208)]
    if [(r["movement_cost"], r["initial_b"], r["seed"]) for r in report["runs"]] != cases:
        raise ValueError("Expected all four selected cases")
    series, hashes = [], {}
    for record in report["runs"]:
        c, b, s = record["movement_cost"], record["initial_b"], record["seed"]
        path = args.input / f"cost-{c}-b-{b}-neutral-seed-{s}.csv"
        hashes[path.name] = hashlib.sha256(path.read_bytes()).hexdigest()
        if hashes[path.name] != report["input_sha256"][path.name]:
            raise ValueError("Raw records differ from audited inputs")
        rows = read_rows(path)
        if len(rows) != 30001 or any(r["tick"] != t for t, r in enumerate(rows)):
            raise ValueError("Truncated or disordered trajectory")
        if any(r["b_fraction"] is None or not 0 <= r["b_fraction"] <= 1 for r in rows):
            raise ValueError("Unexpected extinct or invalid fraction record")
        if any(rows[t] != record["observations"][str(t)] for t in (3000, 10000, 30000)):
            raise ValueError("Observation mismatch")
        series.append(rows)
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9, "svg.fonttype": "none", "path.simplify": False})
    fig, axes = plt.subplots(4, 2, figsize=(12, 10))
    for i, (record, rows) in enumerate(zip(report["runs"], series)):
        lost = "A" if record["a_loss_tick"] is not None else "B"
        loss_tick = record["a_loss_tick"] if lost == "A" else record["b_loss_tick"]
        if loss_tick is None or rows[loss_tick][lost.lower()] != 0 or rows[loss_tick-1][lost.lower()] == 0:
            raise ValueError("Loss annotation disagrees with data")
        for j, horizon in enumerate((6000, 30000)):
            ax = axes[i, j]
            shown = rows[:horizon+1]
            ax.axvspan(0, 3000, color="#edf0f1", zorder=0)
            ax.plot([r["tick"] for r in shown], [r["b_fraction"] for r in shown],
                    color="#267d68", linewidth=1)
            ax.axvline(3000, color="#63747c", linestyle="--", linewidth=1)
            ax.plot(loss_tick, rows[loss_tick]["b_fraction"], marker="o", color="#a65335", markersize=4)
            ax.set_xlim(0, horizon)
            ax.set_ylim(-.06, 1.06)
            ax.set_yticks([0, .5, 1], ["0%", "50%", "100%"])
            ax.set_xticks([0, 3000, 6000] if j == 0 else [0, 10000, 20000, 30000])
            ax.xaxis.set_major_formatter(StrMethodFormatter("{x:,.0f}"))
            ax.grid(axis="y", color="#e5e8e9", linewidth=.6)
            ax.spines[["top", "right"]].set_visible(False)
            if j == 0:
                ax.set_ylabel("B / (A + B)")
                ax.set_title(f"Cost {record['movement_cost']} | initial B {record['initial_b']}/80 | seed {record['seed']}", loc="left", fontsize=10)
                ax.text(.98, .5, f"{lost} lost at {loss_tick:,}", transform=ax.transAxes,
                        ha="right", va="center", fontsize=9, bbox=dict(facecolor="white", alpha=.85, edgecolor="none"))
            else:
                ax.set_title(f"Full horizon | final A={record['a']}, B={record['b']}", loc="left", fontsize=10)
            if i == 3:
                ax.set_xlabel("Tick (early detail)" if j == 0 else "Tick (complete observation)")
    fig.suptitle("Temporary two-group persistence ends in all four selected worlds", fontsize=15, y=.98)
    fig.text(.5, .945, "Neutral founder labels: identical trait 250, mutation disabled. Gray region = original 3,000-tick observation.", ha="center", fontsize=10)
    fig.text(.5, .025, "All saved ticks plotted; left panels repeat early detail. Conditional follow-ups, not new independent seeds or a coexistence-rate estimate.", ha="center", fontsize=9)
    fig.subplots_adjust(left=.075, right=.955, top=.90, bottom=.085, wspace=.16, hspace=.54)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    for path in targets[:2]:
        fig.savefig(path, dpi=180)
    plt.close(fig)
    targets[2].write_text(json.dumps(dict(figure="campaign-015-followup-1", cases=cases,
        rows_per_full_panel=30001, rows_per_detail_panel=6001, downsampling=False,
        input_sha256=hashes, verification_sha256=hashlib.sha256(args.verification.read_bytes()).hexdigest(),
        script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()), indent=2)+"\n", encoding="utf-8")


if __name__ == "__main__":
    main()
