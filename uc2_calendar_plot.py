"""
UC2-Calendar baseline plot.

Three panels sharing the x-axis:
  Top    : mean + max user_delay (ms) per tick, rolling average overlay,
           deadline vlines and holiday shading
  Middle : fraction of nodes where app is unreachable (inf user_delay)
  Bottom : calendar phase colour bar
"""

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

CSV_DIR = Path("results/uc2_calendar-20260823_174257/csv")
FIG_DIR = Path("results/uc2_calendar/figures")
FIG_DIR.mkdir(parents=True, exist_ok=True)

WINDOW   = 30          # rolling-average width (ticks)
N_MONTHS = 3

# ── colours ─────────────────────────────────────────────────────────────────
C_BLUE   = "#4C8ED9"
C_ORANGE = "#FFA500"
C_RED    = "#E05252"
C_GRAY   = "#BDBDBD"
C_GREEN  = "#4CAF50"

PHASE_COLORS = {
    "normal":       C_BLUE,
    "pre_deadline": C_ORANGE,
    "deadline":     C_RED,
    "post_deadline":"#FF8C69",
    "holiday":      C_GRAY,
}

# ── load data ────────────────────────────────────────────────────────────────
sim  = pd.read_csv(CSV_DIR / "simulation.csv")
node = pd.read_csv(CSV_DIR / "node.csv")

phase_map = (sim[sim["callback_id"] == "tick_phase"]
             .drop_duplicates("n_event")
             .set_index("n_event")["value"])

ud = node[node["callback_id"] == "user_delay"].copy()
ud["value"] = pd.to_numeric(ud["value"], errors="coerce")

# per-tick: fraction unreachable, mean and max of finite values
total_nodes = ud.groupby("n_event")["value"].count()
inf_mask    = ud["value"].isna() | (ud["value"] >= 1e9)
inf_frac    = ud[inf_mask].groupby("n_event")["value"].count() / total_nodes
inf_frac    = inf_frac.reindex(total_nodes.index, fill_value=0)

ud_finite = ud[~inf_mask]
by_tick = (ud_finite.groupby("n_event")["value"]
           .agg(mean="mean", maximum="max")
           .reindex(total_nodes.index, fill_value=np.nan))

ticks = by_tick.index.values
mean_roll = (by_tick["mean"].rolling(WINDOW, center=True, min_periods=1).mean())
max_roll  = (by_tick["maximum"].rolling(WINDOW, center=True, min_periods=1).mean())

# ── build phase arrays for the colour bar ───────────────────────────────────
phase_seq = phase_map.reindex(total_nodes.index).values

# ── plot ─────────────────────────────────────────────────────────────────────
fig, (ax_top, ax_mid, ax_bot) = plt.subplots(
    3, 1, figsize=(14, 8), sharex=True,
    gridspec_kw={"height_ratios": [4, 2, 1]},
)
fig.suptitle(
    "UC2-Calendar: BestFit baseline — user delay under synthetic calendar load\n"
    f"(187-node hierarchical infrastructure, SockShop, {N_MONTHS} monthly cycles)",
    fontsize=12, fontweight="bold",
)

# ── shade holiday spans and deadline vlines (all panels) ────────────────────
for m in range(N_MONTHS):
    mo = m * TICKS_PER_MONTH
    for d in range(1, DAYS_PER_MONTH + 1):
        span_s = mo + (d - 1) * TICKS_PER_DAY
        span_e = span_s + TICKS_PER_DAY
        if d in HOLIDAY_DAYS:
            for ax in (ax_top, ax_mid):
                ax.axvspan(span_s, span_e, color=C_GRAY, alpha=0.18, zorder=0)
    deadline_t = mo + 14 * TICKS_PER_DAY   # day 15 centre
    for ax in (ax_top, ax_mid):
        ax.axvline(deadline_t, color=C_RED, linestyle="--",
                   linewidth=1.0, alpha=0.75, zorder=1,
                   label="Deadline (day 15)" if m == 0 else "_")

# ── top panel: mean & max user_delay ─────────────────────────────────────────
ax_top.plot(ticks, by_tick["mean"],    color=C_BLUE,   lw=0.5, alpha=0.35, zorder=2)
ax_top.plot(ticks, by_tick["maximum"], color=C_ORANGE, lw=0.5, alpha=0.25, zorder=2)
ax_top.plot(ticks, mean_roll,          color=C_BLUE,   lw=2.0, zorder=3,
            label="Mean user delay (avg)")
ax_top.plot(ticks, max_roll,           color=C_ORANGE, lw=2.0, zorder=3,
            label="Max user delay (avg)")

ax_top.set_ylabel("User delay (ms)")
ax_top.set_ylim(0)
ax_top.grid(axis="y", linestyle="--", alpha=0.35)
ax_top.spines["top"].set_visible(False)
ax_top.spines["right"].set_visible(False)

legend_handles = [
    mlines.Line2D([], [], color=C_BLUE,   lw=2.0, label="Mean user delay (avg)"),
    mlines.Line2D([], [], color=C_ORANGE, lw=2.0, label="Max user delay (avg)"),
    mpatches.Patch(color=C_RED,  alpha=0.6, label="Deadline (day 15)"),
    mpatches.Patch(color=C_GRAY, alpha=0.4, label="Holiday / weekend"),
]
ax_top.legend(handles=legend_handles, loc="upper left", fontsize=8, frameon=True)

# ── middle panel: unreachable fraction ───────────────────────────────────────
inf_roll = inf_frac.rolling(WINDOW, center=True, min_periods=1).mean()
ax_mid.fill_between(ticks, inf_frac.values * 100,
                    color=C_RED, alpha=0.25, zorder=2)
ax_mid.plot(ticks, inf_roll.values * 100,
            color=C_RED, lw=1.8, zorder=3, label="Unreachable (rolling avg)")
ax_mid.set_ylabel("Nodes with\napp unreachable (%)")
ax_mid.set_ylim(0, 105)
ax_mid.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:.0f}%"))
ax_mid.grid(axis="y", linestyle="--", alpha=0.35)
ax_mid.spines["top"].set_visible(False)
ax_mid.spines["right"].set_visible(False)
ax_mid.legend(loc="upper right", fontsize=8)

# ── bottom panel: phase colour bar ───────────────────────────────────────────
bar_colors = [PHASE_COLORS.get(p, C_BLUE) for p in phase_seq]
ax_bot.bar(ticks, np.ones(len(ticks)), width=1.0,
           color=bar_colors, align="edge")
ax_bot.set_yticks([])
ax_bot.set_ylabel("Phase", fontsize=8)
ax_bot.spines["top"].set_visible(False)
ax_bot.spines["right"].set_visible(False)
ax_bot.spines["left"].set_visible(False)

# ── x-axis ───────────────────────────────────────────────────────────────────
month_ticks  = np.arange(0, N_MONTHS * TICKS_PER_MONTH + 1, TICKS_PER_MONTH)
month_labels = [f"Month {m+1}" for m in range(N_MONTHS)] + [""]
ax_bot.set_xticks(month_ticks)
ax_bot.set_xticklabels(month_labels)
ax_bot.xaxis.set_minor_locator(ticker.MultipleLocator(TICKS_PER_DAY * 5))
ax_bot.set_xlabel("Simulation tick")

plt.tight_layout()
out = FIG_DIR / "fig_uc2_calendar_baseline.png"
fig.savefig(out, dpi=150, bbox_inches="tight")
plt.close(fig)
print(f"Saved {out}")

# ── summary table ─────────────────────────────────────────────────────────────
print("\nuser_delay by calendar phase (finite observations only):")
ud_finite2 = ud_finite.copy()
ud_finite2["phase"] = ud_finite2["n_event"].map(phase_map)
summary = (ud_finite2.groupby("phase")["value"]
           .agg(mean="mean", median="median",
                p95=lambda x: x.quantile(0.95),
                n_obs="count")
           .round(1)
           .reindex(["holiday", "normal", "pre_deadline",
                     "deadline", "post_deadline"]))
print(summary.to_string())
print(f"\nUnreachable fraction by phase:")
ud["phase"] = ud["n_event"].map(phase_map)
for ph in ["holiday", "normal", "pre_deadline", "deadline", "post_deadline"]:
    sub = ud[ud["phase"] == ph]
    frac = (sub["value"].isna() | (sub["value"] >= 1e9)).mean()
    print(f"  {ph:<15}: {frac*100:.1f}%")
