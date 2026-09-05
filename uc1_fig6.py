"""
Reproduce Figure 6 from the ECLYPSE paper (arXiv 2501.17126v1).
3-panel compound figure: one panel per topology, showing the best-performing
strategy for that topology. X-axis = infrastructure size, bars = policies,
error bars = std over seeds x loads.
"""
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import pandas as pd

RESULTS_CSV = Path("results/uc1/results.csv")
FIG_DIR = Path("results/uc1/figures")
FIG_DIR.mkdir(parents=True, exist_ok=True)

TOPOLOGY_ORDER = ["star", "random", "hierarchical"]

POLICIES = [
    ("degrade", 0.4),
    ("degrade", 0.5),
    ("degrade", 0.6),
    ("kill",    0.01),
    ("kill",    0.05),
    ("kill",    0.1),
]
POLICY_LABELS = [
    "degrade 40%", "degrade 50%", "degrade 60%",
    "kill 1%",     "kill 5%",     "kill 10%",
]
POLICY_COLORS = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd", "#8c564b"]

df = pd.read_csv(RESULTS_CSV)
df["policy_tuple"] = list(zip(df["policy_type"], df["policy_param"]))
df["placement_pct"] = df["placement_success"] * 100


# Paper's Figure 6 pairings (topology → strategy)
PAPER_PAIRINGS = {
    "star":         "best-fit",
    "random":       "first-fit",
    "hierarchical": "min-energy",
}

n_sizes = len(df["nodes"].unique())
fig_width = 5 + n_sizes * 3   # scale width with number of node sizes
fig, axes = plt.subplots(1, 3, figsize=(fig_width, 5), sharey=True)
fig.suptitle("Placement success rate in UC1", fontsize=13, fontweight="bold", y=1.01)

node_sizes = sorted(df["nodes"].unique())
x = np.arange(len(node_sizes))
n_policies = len(POLICIES)
bar_width = 0.12
group_width = n_policies * bar_width
offsets = np.linspace(-(group_width / 2) + bar_width / 2,
                       (group_width / 2) - bar_width / 2,
                       n_policies)

for ax, topology in zip(axes, TOPOLOGY_ORDER):
    best_stg = PAPER_PAIRINGS[topology]
    sub = df[(df["topology"] == topology) & (df["strategy"] == best_stg)]

    for i, (policy, label, color) in enumerate(zip(POLICIES, POLICY_LABELS, POLICY_COLORS)):
        means, errs = [], []
        for n in node_sizes:
            vals = sub[
                (sub["nodes"] == n) &
                (sub["policy_type"] == policy[0]) &
                (sub["policy_param"] == policy[1])
            ]["placement_pct"]
            means.append(vals.mean() if len(vals) else 0)
            errs.append(vals.std() if len(vals) > 1 else 0)

        ax.bar(x + offsets[i], means, bar_width,
               color=color, label=label,
               yerr=errs, capsize=2,
               error_kw={"elinewidth": 1, "ecolor": "black"})

    ax.set_title(f"{topology}\n({best_stg})", fontsize=11)
    ax.set_xticks(x)
    ax.set_xticklabels([f"{n}" for n in node_sizes])
    ax.set_xlabel("Infrastructure size (nodes)")
    ax.set_ylim(0, 100)
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:.0f}%"))
    ax.grid(axis="y", linestyle="--", alpha=0.4)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

axes[0].set_ylabel("Placement success rate")

# Shared legend below all panels
legend_patches = [
    mpatches.Patch(color=c, label=l)
    for c, l in zip(POLICY_COLORS, POLICY_LABELS)
]
fig.legend(handles=legend_patches, loc="lower center", ncol=6,
           bbox_to_anchor=(0.5, -0.08), frameon=False, fontsize=9)

plt.tight_layout()
out = FIG_DIR / "fig6_compound.png"
fig.savefig(out, dpi=150, bbox_inches="tight")
plt.close(fig)
print(f"Saved {out}")

# Print strategy pairings and mean placement rates
print("\nPaper pairings used:")
for topo, stg in PAPER_PAIRINGS.items():
    mean = df[(df["topology"] == topo) & (df["strategy"] == stg)]["placement_pct"].mean()
    print(f"  {topo:<14} {stg:<12} mean={mean:.1f}%")


# ── Figure 6 extended: 3×3 grid (rows = strategies, cols = topologies) ──────
STRATEGY_ORDER = ["best-fit", "first-fit", "min-energy"]

fig3, axes3 = plt.subplots(3, 3, figsize=(fig_width, 13), sharey=True, sharex="col")
fig3.suptitle(
    "Placement success rate — all topology × strategy combinations (UC1)",
    fontsize=13, fontweight="bold",
)

for row, strategy in enumerate(STRATEGY_ORDER):
    for col, topology in enumerate(TOPOLOGY_ORDER):
        ax = axes3[row, col]
        sub = df[(df["topology"] == topology) & (df["strategy"] == strategy)]
        is_paper = PAPER_PAIRINGS[topology] == strategy

        for i, (policy, label, color) in enumerate(zip(POLICIES, POLICY_LABELS, POLICY_COLORS)):
            means, errs = [], []
            for n in node_sizes:
                vals = sub[
                    (sub["nodes"] == n) &
                    (sub["policy_type"] == policy[0]) &
                    (sub["policy_param"] == policy[1])
                ]["placement_pct"]
                means.append(vals.mean() if len(vals) else 0)
                errs.append(vals.std() if len(vals) > 1 else 0)

            ax.bar(x + offsets[i], means, bar_width,
                   color=color, label=label,
                   yerr=errs, capsize=2,
                   error_kw={"elinewidth": 1, "ecolor": "black"})

        # Title — bold + coloured border for paper's pairings
        title = f"{topology} / {strategy}"
        ax.set_title(title, fontsize=10,
                     fontweight="bold" if is_paper else "normal",
                     color="#CC3300" if is_paper else "black")
        if is_paper:
            for spine in ax.spines.values():
                spine.set_edgecolor("#CC3300")
                spine.set_linewidth(1.8)
        else:
            ax.spines["top"].set_visible(False)
            ax.spines["right"].set_visible(False)

        ax.set_xticks(x)
        ax.set_xticklabels([f"{n}" for n in node_sizes])
        ax.set_ylim(0, 100)
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:.0f}%"))
        ax.grid(axis="y", linestyle="--", alpha=0.4)

        if col == 0:
            ax.set_ylabel(f"{strategy}\n\nPlacement success", fontsize=9)
        if row == 2:
            ax.set_xlabel("Infrastructure size (nodes)", fontsize=9)

fig3.legend(handles=legend_patches, loc="lower center", ncol=6,
            bbox_to_anchor=(0.5, -0.03), frameon=False, fontsize=9)

plt.tight_layout()
out3 = FIG_DIR / "fig6_3x3_compound.png"
fig3.savefig(out3, dpi=150, bbox_inches="tight")
plt.close(fig3)
print(f"Saved {out3}")
