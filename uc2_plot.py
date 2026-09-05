"""
UC2 plot: reproduces Figure 7 from the ECLYPSE paper.
5-series single panel matching paper layout:
  (1) Response time          – raw, thin orange
  (2) Max user delay         – raw, thin cyan
  (3) Response time (avg)    – bold orange smoothed line
  (4) Max user delay (avg)   – bold cyan smoothed line
  (5) Users update           – gray dashed verticals at ticks 1000/2000/3000/4000

"Response time" is approximated by the per-tick mean user delay across
active edge nodes: latency(node→FrontendService) + uc × log(1+uc).
The ECLYPSE default response_time metric (inter-service path sum) is constant
in this setup because BestFit collapses all SockShop services onto one node
(empty requirement dicts → no placement constraints).
"""
from pathlib import Path

import matplotlib.lines as mlines
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import pandas as pd

CSV_DIR = Path("results/uc2-20260707_190913/csv")
FIG_DIR = Path("results/uc2/figures")
FIG_DIR.mkdir(parents=True, exist_ok=True)

EVENT_TICKS = [1000, 2000, 3000, 4000]

# colours matching the paper
RT_COLOR = "#26C6DA"    # cyan    – response time
UD_COLOR = "#FFA500"    # orange  – max user delay
EV_COLOR = "#BDBDBD"    # silver  – users update verticals

WINDOW = 50             # rolling average window (ticks)


def load_user_delay(csv_path):
    df = pd.read_csv(csv_path)
    df = df[df["callback_id"] == "user_delay"].copy()
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    df = df[df["value"] < 1e9]   # drop inf (application not reachable)
    return df


if __name__ == "__main__":
    ud_raw = load_user_delay(CSV_DIR / "node.csv")

    by_tick = ud_raw.groupby("n_event")["value"].agg(
        response_time="mean",   # mean across nodes ≈ user-perceived response time
        max_user_delay="max",
    ).reset_index()
    by_tick.rename(columns={"n_event": "tick"}, inplace=True)

    # rolling averages
    idx = by_tick.set_index("tick")
    rt_avg  = idx["response_time"].rolling(WINDOW, center=True, min_periods=1).mean()
    ud_avg  = idx["max_user_delay"].rolling(WINDOW, center=True, min_periods=1).mean()

    # ── plot ────────────────────────────────────────────────────────────────
    fig, ax = plt.subplots(figsize=(12, 4))

    # (1) Response time – raw
    ax.plot(by_tick["tick"], by_tick["response_time"],
            color=RT_COLOR, linewidth=0.6, alpha=0.40, zorder=2)

    # (2) Max user delay – raw
    ax.plot(by_tick["tick"], by_tick["max_user_delay"],
            color=UD_COLOR, linewidth=0.6, alpha=0.40, zorder=2)

    # (3) Response time (avg) – bold
    ax.plot(rt_avg.index, rt_avg.values,
            color=RT_COLOR, linewidth=2.0, zorder=3)

    # (4) Max user delay (avg) – bold
    ax.plot(ud_avg.index, ud_avg.values,
            color=UD_COLOR, linewidth=2.0, zorder=3)

    # (5) Users update – vertical lines (first one carries the legend handle)
    for i, t in enumerate(EVENT_TICKS):
        ax.axvline(t, color=EV_COLOR, linewidth=1.0, linestyle="--",
                   zorder=1, label="_" if i else "_users")

    # ── legend (5 entries matching paper) ───────────────────────────────────
    legend_handles = [
        mlines.Line2D([], [], color=RT_COLOR, linewidth=0.8, alpha=0.6,
                      label="Response time"),
        mlines.Line2D([], [], color=UD_COLOR, linewidth=0.8, alpha=0.6,
                      label="Max user delay"),
        mlines.Line2D([], [], color=RT_COLOR, linewidth=2.0,
                      label="Response time (avg)"),
        mlines.Line2D([], [], color=UD_COLOR, linewidth=2.0,
                      label="Max user delay (avg)"),
        mlines.Line2D([], [], color=EV_COLOR, linewidth=1.0, linestyle="--",
                      label="Users update"),
    ]
    ax.legend(handles=legend_handles, loc="upper left", fontsize=8, frameon=True)

    ax.set_xlabel("Tick")
    ax.set_ylabel("Response Time (ms)")
    ax.set_title("Response time and maximum user delay of the SockShop application (UC2)")
    ax.xaxis.set_major_locator(ticker.MultipleLocator(500))
    ax.grid(axis="y", linestyle="--", alpha=0.3)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    plt.tight_layout()
    out = FIG_DIR / "fig7_uc2.png"
    fig.savefig(out, dpi=150)
    plt.close(fig)
    print(f"Saved {out}")

    print("\nSummary:")
    print(f"  Response time    mean={by_tick['response_time'].mean():.1f}ms "
          f"max={by_tick['response_time'].max():.1f}ms")
    print(f"  Max user delay   mean={by_tick['max_user_delay'].mean():.1f}ms "
          f"max={by_tick['max_user_delay'].max():.1f}ms")
