"""
Final debug: call place() exactly as ECLYPSE does (via infrastructure.available)
and trace service-by-service what happens.
"""

from examples.grid_analysis.applications import get_apps
from examples.grid_analysis.infrastructure import get_infrastructure
from examples.grid_analysis.strategy import EnergyMinimizationStrategy
from eclypse.utils.constants import MAX_FLOAT

config = {
    "seed": 42, "max_steps": 2, "nodes": 20,
    "load": 0.0, "policy": ("kill", 0.01),
    "topology": ("star",),
}

infr = get_infrastructure(config)
apps = get_apps(seed=42)
app = apps[0]

stg = EnergyMinimizationStrategy()

# ECLYPSE calls place() with infrastructure.available (not infr itself)
avail = infr.available

print(f"infr.available type: {type(avail)}")
print(f"available nodes: {len(list(avail.nodes))}")
print()

# Replicate place() logic manually with full tracing
stg.initial_resources = avail.nodes(data=True)

print(f"initial_resources is live view: {stg.initial_resources is not None}")
node_id, node_data = next(iter(avail.nodes(data=True)))
snap = stg.initial_resources[node_id]
print(f"  initial_resources['{node_id}'] is avail.nodes['{node_id}']: {snap is avail.nodes[node_id]}")
print()

import random as rnd
rnd.seed(42)
infrastructure_nodes = list(avail.nodes(data=True))
rnd.shuffle(infrastructure_nodes)

print(f"Services to place: {[s for s, _ in app.nodes(data=True)]}")
print()

mapping = {}
for service, sattr in app.nodes(data=True):
    min_energy = MAX_FLOAT
    best_fit = None
    best_nattr = None
    candidates = 0

    for node, nattr in infrastructure_nodes:
        satisfies = avail.node_assets.satisfies(nattr, sattr)
        if satisfies:
            candidates += 1
            allocated = avail.node_assets.consume(stg.initial_resources[node], nattr)
            energy = (
                allocated.get("energy", 0)
                + 0.25 * allocated.get("cpu", 0)
                + 0.25 * allocated.get("gpu", 0)
                + 0.25 * allocated.get("ram", 0)
                + 0.25 * allocated.get("storage", 0)
            )
            if energy < min_energy and energy > 0:
                min_energy = energy
                best_fit = node
                best_nattr = nattr

    mapping[service] = best_fit
    placed = best_fit is not None
    print(f"  Service '{service}': candidates={candidates}, best_fit={best_fit}, energy={min_energy:.2f}, placed={placed}")

    if best_fit is not None and best_nattr is not None:
        new_res = avail.node_assets.consume(best_nattr, sattr)
        infrastructure_nodes.remove((best_fit, best_nattr))
        infrastructure_nodes.append((best_fit, new_res))

print()
placed_count = sum(1 for v in mapping.values() if v is not None)
print(f"Final mapping: {placed_count}/{len(mapping)} services placed")
print(f"Mapping: {mapping}")

# Check ECLYPSE partial detection
is_partial = [s for s in app.nodes if s not in mapping or mapping[s] is None]
all_none = all(v is None for v in mapping.values())
print(f"\nECLYPSE checks:")
print(f"  not mapping: {not mapping}")
print(f"  all values None: {all_none}")
print(f"  is_partial services: {is_partial}")
print(f"  → mapping will be RESET: {not mapping or all_none or bool(is_partial)}")
