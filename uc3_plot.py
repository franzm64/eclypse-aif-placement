"""
UC3 plots: reproduces Figures 9 and 10 from the ECLYPSE paper.

Figure 9 – dual y-axis:
  Left  : Accuracy [%]  (blue line + shaded std band)
  Right : Image Count [#imgs/tick] (orange line)
  Markers: Model Change events (orange dots on Image Count line)

Figure 10 – CPU usage:
  Blue noisy line  : EndService + PredictorService remote CPU %
  Orange bold line : rolling average
  Red dashed vline : tick 450 (DegradePolicy starts)

Note: TrainerService runs 100-epoch CPU training in a background thread,
saturating one core (~102% CPU); it is excluded from Figure 10 to stay
comparable with the paper's GPU-training setup where trainer CPU is low.
"""
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import pandas as pd

CSV_DIR = Path("results/uc3-20260710_011009/csv")
FIG_DIR = Path("results/uc3/figures")
FIG_DIR.mkdir(parents=True, exist_ok=True)

DEGRADE_TICK = 450          # DegradePolicy fires at 75 % × 600 steps
WINDOW       = 30           # rolling-average window

BLUE   = "#4C8ED9"
ORANGE = "#FFA500"
RED    = "#E05252"


def load_service(cb_id, service_id=None):
    df = pd.read_csv(CSV_DIR / "service.csv")
    df = df[df["callback_id"] == cb_id].copy()
    if service_id:
        if isinstance(service_id, str):
            df = df[df["service_id"] == service_id]
        else:
            df = df[df["service_id"].isin(service_id)]
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    return df.dropna(subset=["value"])


# ── Figure 9 ────────────────────────────────────────────────────────────────
acc_raw  = load_service("img_counter", "EndService")  # images per tick
acc_data = load_service("accuracy",    "EndService")  # 0-1
mc_ticks = load_service("model_change")["n_event"].tolist()

acc_by_tick = (acc_data.groupby("n_event")["value"]
               .mean()
               .reset_index()
               .rename(columns={"n_event": "tick", "value": "mean"}))

acc_smooth = (acc_by_tick.set_index("tick")["mean"]
              .rolling(WINDOW, center=True, min_periods=1).mean())

img_by_tick = (acc_raw.groupby("n_event")["value"]
               .mean().reset_index()
               .rename(columns={"n_event": "tick", "value": "img_count"}))

fig9, ax_acc = plt.subplots(figsize=(10, 4))
ax_img = ax_acc.twinx()

# Accuracy (left axis, 0-100 %) – raw thin + bold rolling average
ax_acc.plot(acc_by_tick["tick"], acc_by_tick["mean"] * 100,
            color=BLUE, linewidth=0.7, alpha=0.35, zorder=2)
ax_acc.plot(acc_smooth.index, acc_smooth.values * 100,
            color=BLUE, linewidth=2.0, label="Accuracy", zorder=3)

# Image count (right axis)
ax_img.plot(img_by_tick["tick"], img_by_tick["img_count"],
            color=ORANGE, linewidth=1.2, label="Image Count", zorder=2)

# Model-change markers: dashed vertical lines
for t in mc_ticks:
    ax_acc.axvline(t, color=ORANGE, linestyle="--", linewidth=0.6,
                   alpha=0.5, zorder=1)

ax_acc.set_xlabel("Tick")
ax_acc.set_ylabel("Accuracy [%]")
ax_img.set_ylabel("Count [#imgs/tick]")
ax_acc.set_ylim(0, 110)
ax_img.set_ylim(0, img_by_tick["img_count"].max() * 1.3)
ax_acc.xaxis.set_major_locator(ticker.MultipleLocator(100))
ax_acc.grid(axis="y", linestyle="--", alpha=0.3)
ax_acc.spines["top"].set_visible(False)

# Combined legend
import matplotlib.lines as mlines
lines_acc, labels_acc = ax_acc.get_legend_handles_labels()
lines_img, labels_img = ax_img.get_legend_handles_labels()
mc_handle = mlines.Line2D([], [], color=ORANGE, linestyle="--",
                           linewidth=0.9, label="Model Change")
ax_acc.legend(handles=lines_acc + lines_img + [mc_handle],
              labels=labels_acc + labels_img + ["Model Change"],
              loc="upper left", fontsize=9)

ax_acc.set_title("Image prediction accuracy and throughput (UC3)")
plt.tight_layout()
out9 = FIG_DIR / "fig9_uc3_accuracy.png"
fig9.savefig(out9, dpi=150)
plt.close(fig9)
print(f"Saved {out9}")


# ── Figure 10 ───────────────────────────────────────────────────────────────
cpu_raw = load_service("remote_cpu_usage",
                       ["EndService", "PredictorService"])
cpu_by_tick = (cpu_raw.groupby("n_event")["value"]
               .mean().reset_index()
               .rename(columns={"n_event": "tick", "value": "cpu"}))

cpu_smooth = (cpu_by_tick.set_index("tick")["cpu"]
              .rolling(WINDOW, center=True, min_periods=1).mean())

fig10, ax_cpu = plt.subplots(figsize=(10, 4))

ax_cpu.plot(cpu_by_tick["tick"], cpu_by_tick["cpu"],
            color=BLUE, linewidth=0.7, alpha=0.5, zorder=2)
ax_cpu.plot(cpu_smooth.index, cpu_smooth.values,
            color=ORANGE, linewidth=2.0, zorder=3)

ax_cpu.axvline(DEGRADE_TICK, color=RED, linestyle="--",
               linewidth=1.2, label="Start resource decay")

ax_cpu.set_xlabel("Tick")
ax_cpu.set_ylabel("Usage [%]")
ax_cpu.set_title("CPU usage of EndService + PredictorService (UC3)")
ax_cpu.legend(fontsize=9)
ax_cpu.xaxis.set_major_locator(ticker.MultipleLocator(100))
ax_cpu.grid(axis="y", linestyle="--", alpha=0.3)
ax_cpu.spines["top"].set_visible(False)
ax_cpu.spines["right"].set_visible(False)

plt.tight_layout()
out10 = FIG_DIR / "fig10_uc3_cpu.png"
fig10.savefig(out10, dpi=150)
plt.close(fig10)
print(f"Saved {out10}")

# ── summary ─────────────────────────────────────────────────────────────────
print(f"\nSummary:")
print(f"  Accuracy peak : {acc_by_tick['mean'].max()*100:.1f}%  "
      f"(final: {acc_by_tick['mean'].iloc[-1]*100:.1f}%)")
print(f"  Image count   : mean={img_by_tick['img_count'].mean():.1f}  "
      f"post-450 mean="
      f"{img_by_tick[img_by_tick['tick']>DEGRADE_TICK]['img_count'].mean():.1f}")
print(f"  Model updates : {len(mc_ticks)} at ticks {mc_ticks}")
print(f"  CPU (End+Pred): mean={cpu_by_tick['cpu'].mean():.1f}%  "
      f"post-450 mean="
      f"{cpu_by_tick[cpu_by_tick['tick']>DEGRADE_TICK]['cpu'].mean():.1f}%")
