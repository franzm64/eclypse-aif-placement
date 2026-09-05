"""
Standalone test plot for CalendarLoadPolicy.
Shows the synthetic monthly load profile over N_MONTHS cycles without
running a full simulation — purely a sanity-check of the stimulus.

Three panels share the same x-axis:
  Top    : per-tick load factor (thin) + 1-day rolling mean (bold)
  Middle : day-of-month indicator with deadline and holiday markers
  Bottom : cumulative absolute user-count (summed across all 187 nodes)
"""
import sys
sys.path.insert(0, "eclypse")

import random
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.ticker as ticker
import pandas as pd
from pathlib import Path

from examples.user_distribution.calendar_policy import (
    TICKS_PER_DAY,
    DAYS_PER_MONTH,
    TICKS_PER_MONTH,
    HOLIDAY_DAYS,
    load_factor,
)

# ── Parameters ──────────────────────────────────────────────────────────────
N_MONTHS = 3
N_TICKS  = N_MONTHS * TICKS_PER_MONTH
SEED     = 0

FIG_DIR = Path("results/uc2/figures")
FIG_DIR.mkdir(parents=True, exist_ok=True)

# ── Load spatial baseline ────────────────────────────────────────────────────
df_base = pd.read_parquet("eclypse/examples/user_distribution/dataset.parquet")
df_base = df_base[df_base["time"] == df_base["time"].min()]
total_baseline_users = int(df_base["user_count"].sum())

# ── Generate factor time series ──────────────────────────────────────────────
rng     = random.Random(SEED)
ticks   = np.arange(N_TICKS)
factors = np.array([load_factor((t // TICKS_PER_DAY) % DAYS_PER_MONTH + 1, rng)
                    for t in ticks])
total_users = factors * total_baseline_users

# Rolling mean over one day
roll = (pd.Series(factors)
        .rolling(TICKS_PER_DAY, center=True, min_periods=1)
        .mean().values)

day_index = (ticks // TICKS_PER_DAY) % DAYS_PER_MONTH + 1   # 1-based

# ── Colours ──────────────────────────────────────────────────────────────────
C_BLUE   = "#4C8ED9"
C_ORANGE = "#FFA500"
C_RED    = "#E05252"
C_GRAY   = "#BDBDBD"

# ── Plot ─────────────────────────────────────────────────────────────────────
fig, (ax_top, ax_mid, ax_bot) = plt.subplots(
    3, 1, figsize=(14, 8), sharex=True,
    gridspec_kw={"height_ratios": [3, 1, 2]},
)
fig.suptitle(
    f"Synthetic calendar load profile — {N_MONTHS} monthly cycles\n"
    f"(TICKS_PER_DAY={TICKS_PER_DAY}, DAYS_PER_MONTH={DAYS_PER_MONTH})",
    fontsize=12, fontweight="bold",
)

# Mark deadline and holiday spans (drawn first so they sit behind data)
deadline_days = {15}
for m in range(N_MONTHS):
    month_start = m * TICKS_PER_MONTH
    for d in range(1, DAYS_PER_MONTH + 1):
        span_start = month_start + (d - 1) * TICKS_PER_DAY
        span_end   = span_start + TICKS_PER_DAY
        if d in HOLIDAY_DAYS:
            for ax in (ax_top, ax_bot):
                ax.axvspan(span_start, span_end, color=C_GRAY, alpha=0.18, zorder=0)
        if d in deadline_days:
            for ax in (ax_top, ax_bot):
                ax.axvline(span_start + TICKS_PER_DAY // 2,
                           color=C_RED, linestyle="--", linewidth=1.0,
                           alpha=0.8, zorder=1,
                           label="Deadline (day 15)" if m == 0 else "_")

# ── Top panel: load factor ────────────────────────────────────────────────────
ax_top.plot(ticks, factors, color=C_BLUE, linewidth=0.6, alpha=0.45, zorder=2)
ax_top.plot(ticks, roll,    color=C_BLUE, linewidth=2.0, zorder=3, label="Load factor (1-day avg)")
ax_top.set_ylabel("Load factor\n(× baseline)")
ax_top.set_ylim(0)
ax_top.grid(axis="y", linestyle="--", alpha=0.35)
ax_top.spines["top"].set_visible(False)
ax_top.spines["right"].set_visible(False)

# Legend for top panel
deadline_handle = mpatches.Patch(color=C_RED, alpha=0.7, label="Deadline (day 15)")
holiday_handle  = mpatches.Patch(color=C_GRAY, alpha=0.5, label="Holiday / weekend")
line_handle     = plt.Line2D([], [], color=C_BLUE, linewidth=2.0, label="Load factor (1-day avg)")
ax_top.legend(handles=[line_handle, deadline_handle, holiday_handle],
              loc="upper right", fontsize=8, frameon=True)

# ── Middle panel: day-of-month bar ────────────────────────────────────────────
bar_colors = []
for d in day_index:
    if d in HOLIDAY_DAYS:
        bar_colors.append(C_GRAY)
    elif d == 15:
        bar_colors.append(C_RED)
    elif d in {13, 14, 16, 17}:
        bar_colors.append(C_ORANGE)
    else:
        bar_colors.append(C_BLUE)

ax_mid.bar(ticks, np.ones(N_TICKS), width=1.0, color=bar_colors, align="edge")
ax_mid.set_yticks([])
ax_mid.set_ylabel("Day type", fontsize=8)
ax_mid.spines["top"].set_visible(False)
ax_mid.spines["right"].set_visible(False)
ax_mid.spines["left"].set_visible(False)

# ── Bottom panel: total user count ────────────────────────────────────────────
roll_users = (pd.Series(total_users)
              .rolling(TICKS_PER_DAY, center=True, min_periods=1)
              .mean().values)
ax_bot.plot(ticks, total_users, color=C_ORANGE, linewidth=0.6, alpha=0.4, zorder=2)
ax_bot.plot(ticks, roll_users,  color=C_ORANGE, linewidth=2.0, zorder=3)
ax_bot.set_ylabel("Total users\n(all nodes)")
ax_bot.set_ylim(0)
ax_bot.grid(axis="y", linestyle="--", alpha=0.35)
ax_bot.spines["top"].set_visible(False)
ax_bot.spines["right"].set_visible(False)

# ── X axis ticks: one per month boundary ─────────────────────────────────────
month_ticks  = np.arange(0, N_TICKS + 1, TICKS_PER_MONTH)
month_labels = [f"Month {m+1}" for m in range(N_MONTHS)] + [""]
ax_bot.set_xticks(month_ticks)
ax_bot.set_xticklabels(month_labels)
ax_bot.set_xlabel("Simulation tick")
ax_bot.xaxis.set_minor_locator(ticker.MultipleLocator(TICKS_PER_DAY * 5))

plt.tight_layout()
out = FIG_DIR / "calendar_load_profile.png"
fig.savefig(out, dpi=150, bbox_inches="tight")
plt.close(fig)
print(f"Saved {out}")

# ── Summary stats ─────────────────────────────────────────────────────────────
print(f"\nLoad factor summary over {N_TICKS} ticks:")
print(f"  baseline days : mean={np.mean(factors[np.isin(day_index, list(set(range(1,31)) - HOLIDAY_DAYS - {13,14,15,16,17}))]):.2f}")
print(f"  holiday days  : mean={np.mean(factors[np.isin(day_index, list(HOLIDAY_DAYS))]):.2f}")
print(f"  pre-deadline  : mean={np.mean(factors[np.isin(day_index, [13,14])]):.2f}")
print(f"  deadline      : mean={np.mean(factors[day_index == 15]):.2f}")
print(f"  post-deadline : mean={np.mean(factors[np.isin(day_index, [16,17])]):.2f}")
print(f"  overall       : mean={factors.mean():.2f}  max={factors.max():.2f}")
