"""
UC2-Constrained comparison plot: BestFit vs AIF under oscillating kill/recovery
with realistic resource constraints (cpu 2–8 cores, ram 1–8 GB per node).

Three-panel layout (shared x-axis):
  Top    : mean user_delay — BestFit (blue) vs AIF (green), rolling averages
  Middle : unreachable fraction
  Bottom : calendar phase colour bar
"""
import sys
sys.path.insert(0, "eclypse")

from pathlib import Path

import matplotlib.lines as mlines
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
import pandas as pd

from examples.user_distribution.calendar_policy import (
    DAYS_PER_MONTH,
    HOLIDAY_DAYS,
    TICKS_PER_DAY,
    TICKS_PER_MONTH,
)

BESTFIT_CSV = Path("results/uc2_constrained_bestfit-20260827_000444/csv")
AIF_CSV     = Path("results/uc2_constrained_aif-20260827_000450/csv")

FIG_DIR = Path("results/uc2_constrained/figures")
FIG_DIR.mkdir(parents=True, exist_ok=True)

WINDOW   = 30
N_MONTHS = 3

C_BLUE  = "#4C8ED9"
C_GREEN = "#2ECC71"
C_RED   = "#E05252"
C_GRAY  = "#BDBDBD"

PHASE_COLORS = {
    "normal":        C_BLUE,
    "pre_deadline":  "#FFA500",
    "deadline":      C_RED,
    "post_deadline": "#FF8C69",
    "holiday":       C_GRAY,
}


def _load(csv_dir: Path):
    sim  = pd.read_csv(csv_dir / "simulation.csv")
    node = pd.read_csv(csv_dir / "node.csv")

    phase_map = (sim[sim["callback_id"] == "tick_phase"]
                 .drop_duplicates("n_event")
                 .set_index("n_event")["value"])

    ud = node[node["callback_id"] == "user_delay"].copy()
    ud["value"] = pd.to_numeric(ud["value"], errors="coerce")

    total_nodes = ud.groupby("n_event")["value"].count()
    inf_mask    = ud["value"].isna() | (ud["value"] >= 1e9)
    inf_frac    = (ud[inf_mask].groupby("n_event")["value"].count()
                   .reindex(total_nodes.index, fill_value=0) / total_nodes)

    ud_finite = ud[~inf_mask]
    by_tick   = (ud_finite.groupby("n_event")["value"]
                 .agg(mean="mean")
                 .reindex(total_nodes.index, fill_value=np.nan))

    return phase_map, by_tick, inf_frac


phase_map_bf, bt_bf, if_bf = _load(BESTFIT_CSV)
phase_map_ai, bt_ai, if_ai = _load(AIF_CSV)

ticks = bt_bf.index.values

mean_bf = bt_bf["mean"].rolling(WINDOW, center=True, min_periods=1).mean()
mean_ai = bt_ai["mean"].rolling(WINDOW, center=True, min_periods=1).mean()
inf_bf  = if_bf.rolling(WINDOW, center=True, min_periods=1).mean()
inf_ai  = if_ai.rolling(WINDOW, center=True, min_periods=1).mean()

phase_seq = phase_map_bf.reindex(ticks).values

fig, (ax_top, ax_mid, ax_bot) = plt.subplots(
    3, 1, figsize=(14, 8), sharex=True,
    gridspec_kw={"height_ratios": [4, 2, 1]},
)
fig.suptitle(
    "UC2-Constrained: BestFit vs Active Inference — resource-constrained placement\n"
    f"(187-node hierarchical, cpu 2–8 cores, ram 1–8 GB, {N_MONTHS} monthly cycles, "
    "kill=2%, revive~N(2%,1%))",
    fontsize=12, fontweight="bold",
)

for m in range(N_MONTHS):
    mo = m * TICKS_PER_MONTH
    for d in range(1, DAYS_PER_MONTH + 1):
        if d in HOLIDAY_DAYS:
            s, e = mo + (d - 1) * TICKS_PER_DAY, mo + d * TICKS_PER_DAY
            for ax in (ax_top, ax_mid):
                ax.axvspan(s, e, color=C_GRAY, alpha=0.18, zorder=0)
    deadline_t = mo + 14 * TICKS_PER_DAY
    for ax in (ax_top, ax_mid):
        ax.axvline(deadline_t, color=C_RED, linestyle="--",
                   linewidth=1.0, alpha=0.70, zorder=1,
                   label="Deadline (day 15)" if m == 0 else "_")

ax_top.plot(ticks, bt_bf["mean"].values, color=C_BLUE,  lw=0.5, alpha=0.3, zorder=2)
ax_top.plot(ticks, bt_ai["mean"].values, color=C_GREEN, lw=0.5, alpha=0.3, zorder=2)
ax_top.plot(ticks, mean_bf.values, color=C_BLUE,  lw=2.0, zorder=3, label="BestFit")
ax_top.plot(ticks, mean_ai.values, color=C_GREEN, lw=2.0, zorder=3, label="AIF")

ax_top.set_ylabel("Mean user delay (ms)")
ax_top.set_ylim(0)
ax_top.grid(axis="y", linestyle="--", alpha=0.35)
ax_top.spines["top"].set_visible(False)
ax_top.spines["right"].set_visible(False)

legend_top = [
    mlines.Line2D([], [], color=C_BLUE,  lw=2.0, label="BestFit"),
    mlines.Line2D([], [], color=C_GREEN, lw=2.0, label="AIF"),
    mpatches.Patch(color=C_RED,  alpha=0.5, label="Deadline (day 15)"),
    mpatches.Patch(color=C_GRAY, alpha=0.4, label="Holiday"),
]
ax_top.legend(handles=legend_top, loc="upper left", fontsize=8, frameon=True)

ax_mid.fill_between(ticks, if_bf.values * 100, color=C_BLUE,  alpha=0.18, zorder=2)
ax_mid.fill_between(ticks, inf_ai.values * 100, color=C_GREEN, alpha=0.18, zorder=2)
ax_mid.plot(ticks, inf_bf.values * 100, color=C_BLUE,  lw=1.8, zorder=3,
            label="BestFit unreachable")
ax_mid.plot(ticks, inf_ai.values * 100, color=C_GREEN, lw=1.8, zorder=3,
            label="AIF unreachable")

ax_mid.set_ylabel("Nodes with\napp unreachable (%)")
ax_mid.set_ylim(0, 105)
ax_mid.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:.0f}%"))
ax_mid.grid(axis="y", linestyle="--", alpha=0.35)
ax_mid.spines["top"].set_visible(False)
ax_mid.spines["right"].set_visible(False)
ax_mid.legend(loc="upper left", fontsize=8, frameon=True)

bar_colors = [PHASE_COLORS.get(str(p), C_BLUE) for p in phase_seq]
ax_bot.bar(ticks, np.ones(len(ticks)), width=1.0, color=bar_colors, align="edge")
ax_bot.set_yticks([])
ax_bot.set_ylabel("Phase", fontsize=8)
ax_bot.spines["top"].set_visible(False)
ax_bot.spines["right"].set_visible(False)
ax_bot.spines["left"].set_visible(False)

month_ticks  = np.arange(0, N_MONTHS * TICKS_PER_MONTH + 1, TICKS_PER_MONTH)
month_labels = [f"Month {m+1}" for m in range(N_MONTHS)] + [""]
ax_bot.set_xticks(month_ticks)
ax_bot.set_xticklabels(month_labels)
ax_bot.xaxis.set_minor_locator(ticker.MultipleLocator(TICKS_PER_DAY * 5))
ax_bot.set_xlabel("Simulation tick")

plt.tight_layout()
out = FIG_DIR / "fig_uc2_constrained_bestfit_vs_aif.png"
fig.savefig(out, dpi=150, bbox_inches="tight")
plt.close(fig)
print(f"Saved {out}")

print("\nMean user_delay (finite observations, all phases):")
print(f"  BestFit : {bt_bf['mean'].mean():.1f} ms")
print(f"  AIF     : {bt_ai['mean'].mean():.1f} ms")

print("\nMean unreachable fraction:")
print(f"  BestFit : {if_bf.mean()*100:.1f}%")
print(f"  AIF     : {if_ai.mean()*100:.1f}%")
