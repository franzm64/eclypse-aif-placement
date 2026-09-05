"""
UC1 plots: placement success rate by strategy.
Reads results/uc1/results.csv, writes results/uc1/figures/.
"""
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

RESULTS_CSV = Path("results/uc1/results.csv")
FIG_DIR = Path("results/uc1/figures")
FIG_DIR.mkdir(parents=True, exist_ok=True)

STRATEGY_ORDER = ["first-fit", "best-fit", "min-energy"]
TOPOLOGY_ORDER = ["star", "hierarchical", "random"]
COLORS = {"first-fit": "#2196F3", "best-fit": "#F44336", "min-energy": "#4CAF50"}


def fig1_overall(df):
    """Mean placement success rate per strategy, overall."""
    agg = df.groupby("strategy")["placement_success"].mean().reindex(STRATEGY_ORDER)
    fig, ax = plt.subplots(figsize=(6, 4))
    bars = ax.bar(agg.index, agg.values,
                  color=[COLORS[s] for s in agg.index], width=0.5, edgecolor="black")
    ax.bar_label(bars, fmt="{:.2f}", padding=3, fontsize=10)
    ax.set_ylim(0, 1.1)
    ax.set_ylabel("Mean placement success rate")
    ax.set_title("UC1 — Placement success rate by strategy (overall)")
    ax.set_xlabel("Strategy")
    plt.tight_layout()
    fig.savefig(FIG_DIR / "fig1_overall.png", dpi=150)
    plt.close(fig)
    print("Saved fig1_overall.png")


def fig2_by_topology(df):
    """Placement success rate per strategy, broken down by topology."""
    agg = (df.groupby(["topology", "strategy"])["placement_success"]
             .mean()
             .unstack("strategy")
             .reindex(columns=STRATEGY_ORDER)
             .reindex(TOPOLOGY_ORDER))

    x = np.arange(len(TOPOLOGY_ORDER))
    width = 0.25
    fig, ax = plt.subplots(figsize=(8, 4))
    for i, stg in enumerate(STRATEGY_ORDER):
        ax.bar(x + i * width, agg[stg], width,
               label=stg, color=COLORS[stg], edgecolor="black")

    ax.set_xticks(x + width)
    ax.set_xticklabels(TOPOLOGY_ORDER)
    ax.set_ylim(0, 1.15)
    ax.set_ylabel("Mean placement success rate")
    ax.set_title("UC1 — Placement success rate by strategy and topology")
    ax.set_xlabel("Topology")
    ax.legend()
    plt.tight_layout()
    fig.savefig(FIG_DIR / "fig2_by_topology.png", dpi=150)
    plt.close(fig)
    print("Saved fig2_by_topology.png")


def fig3_by_load(df):
    """Effect of infrastructure pre-load on placement success."""
    agg = (df.groupby(["load", "strategy"])["placement_success"]
             .mean()
             .unstack("strategy")
             .reindex(columns=STRATEGY_ORDER))

    fig, ax = plt.subplots(figsize=(6, 4))
    for stg in STRATEGY_ORDER:
        ax.plot(agg.index, agg[stg], marker="o", label=stg, color=COLORS[stg])

    ax.set_ylim(0, 1.05)
    ax.set_ylabel("Mean placement success rate")
    ax.set_xlabel("Infrastructure load")
    ax.set_title("UC1 — Placement success vs. infrastructure load")
    ax.legend()
    plt.tight_layout()
    fig.savefig(FIG_DIR / "fig3_by_load.png", dpi=150)
    plt.close(fig)
    print("Saved fig3_by_load.png")


def fig4_by_policy_type(df):
    """Degrade vs kill policies."""
    agg = (df.groupby(["policy_type", "strategy"])["placement_success"]
             .mean()
             .unstack("strategy")
             .reindex(columns=STRATEGY_ORDER))

    x = np.arange(len(agg.index))
    width = 0.25
    fig, ax = plt.subplots(figsize=(6, 4))
    for i, stg in enumerate(STRATEGY_ORDER):
        ax.bar(x + i * width, agg[stg], width,
               label=stg, color=COLORS[stg], edgecolor="black")

    ax.set_xticks(x + width)
    ax.set_xticklabels(agg.index)
    ax.set_ylim(0, 1.15)
    ax.set_ylabel("Mean placement success rate")
    ax.set_title("UC1 — Placement success by policy type")
    ax.set_xlabel("Update policy")
    ax.legend()
    plt.tight_layout()
    fig.savefig(FIG_DIR / "fig4_by_policy_type.png", dpi=150)
    plt.close(fig)
    print("Saved fig4_by_policy_type.png")


if __name__ == "__main__":
    df = pd.read_csv(RESULTS_CSV)
    print(f"Loaded {len(df)} simulation results")
    print("\nMean placement success rate per strategy:")
    print(df.groupby("strategy")["placement_success"].agg(["mean", "std"]).round(3))
    print()

    fig1_overall(df)
    fig2_by_topology(df)
    fig3_by_load(df)
    fig4_by_policy_type(df)
    print(f"\nAll figures saved to {FIG_DIR}/")
