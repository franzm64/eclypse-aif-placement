"""Generate the 4-tier infrastructure topology figure for the report."""
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.collections as mc
from pathlib import Path

OUT = Path("results/infra_topology.pdf")
OUT.parent.mkdir(parents=True, exist_ok=True)

layers     = [65, 56, 37, 29]
names      = ["Edge", "Fog", "Regional Cloud", "Central Cloud"]
colors     = ["#E8933A", "#3BAA72", "#3B82C4", "#8B5CF6"]
y_pos      = [0.0, 1.0, 2.0, 3.0]

fig, ax = plt.subplots(figsize=(10, 4))
fig.patch.set_facecolor("white")
ax.set_facecolor("white")

# Node x-coordinates per layer
xs_per_layer = [np.linspace(0.0, 1.0, n) for n in layers]

# Draw edges between adjacent tiers (all-to-all, low alpha)
blend = lambda c1, c2: tuple(0.5*(np.array(matplotlib.colors.to_rgb(c1))
                                 + np.array(matplotlib.colors.to_rgb(c2))))
alphas = [0.030, 0.045, 0.070]   # denser upper tiers → slightly higher alpha

for i in range(len(layers) - 1):
    src_xs, dst_xs = xs_per_layer[i], xs_per_layer[i + 1]
    sy, dy = y_pos[i], y_pos[i + 1]
    ec = blend(colors[i], colors[i + 1])
    segs = [[(x1, sy), (x2, dy)] for x1 in src_xs for x2 in dst_xs]
    ax.add_collection(mc.LineCollection(segs, color=ec, alpha=alphas[i], linewidths=0.35))

# Draw nodes on top of edges
for xs, y, c in zip(xs_per_layer, y_pos, colors):
    ax.scatter(xs, [y] * len(xs), s=22, c=c, zorder=5,
               edgecolors="white", linewidths=0.4)

# Right-side layer labels
for name, y, c, n in zip(names, y_pos, colors, layers):
    ax.text(1.05, y, f"{name}  ({n} nodes)", va="center", ha="left",
            color=c, fontsize=11, fontweight="bold")

ax.set_xlim(-0.04, 1.50)
ax.set_ylim(-0.35, 3.35)
ax.axis("off")
fig.tight_layout(pad=0.3)
fig.savefig(OUT, bbox_inches="tight", facecolor="white")
print(f"Saved {OUT}")
