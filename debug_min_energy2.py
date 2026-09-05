"""
Deep debug: trace why min-energy places 0 services.
"""

from examples.grid_analysis.applications import get_apps
from examples.grid_analysis.infrastructure import get_infrastructure
from examples.grid_analysis.strategy import EnergyMinimizationStrategy
from eclypse.utils.constants import MAX_FLOAT

config = {
    "seed": 42, "max_steps": 2, "nodes": 20,
    "load": 0.0, "policy": ("kill", 0.01),
    "topology": ("star",), "strategy": "min-energy",
}

infr = get_infrastructure(config)
apps = get_apps(seed=42)
app = apps[0]
stg = EnergyMinimizationStrategy()

# --- 1. snapshot type and live-view check ---
stg.initial_resources = infr.nodes(data=True)
print(f"initial_resources type: {type(stg.initial_resources)}\n")

# iterate to get a real node_id
node_id, node_data = next(iter(infr.available.nodes(data=True)))
snap = stg.initial_resources[node_id]   # index by node_id string
live = infr.nodes[node_id]
print(f"Sample node_id: '{node_id}'")
print(f"  snapshot is live dict? {snap is live}  ← True = NodeDataView is a live view")
print(f"  snapshot: {dict(snap)}")
print(f"  live:     {dict(live)}\n")

# --- 2. is_feasible ---
feasible = stg.is_feasible(infr, app)
avail = list(infr.available.nodes)
print(f"is_feasible: {feasible}")
print(f"available nodes: {len(avail)} of {infr.number_of_nodes()} total\n")

# --- 3. service requirements ---
services = list(app.nodes(data=True))
print(f"Application '{app.name}' has {len(services)} services:")
for svc, sattr in services:
    print(f"  {svc}: {dict(sattr)}")
print()

# --- 4. node-service satisfies check ---
infr_nodes = list(infr.available.nodes(data=True))
print(f"Checking satisfies() for first service against all {len(infr_nodes)} nodes:")
first_svc, first_sattr = services[0]
sat_count = 0
for nid, nattr in infr_nodes:
    ok = infr.node_assets.satisfies(nattr, first_sattr)
    if ok:
        sat_count += 1
print(f"  Nodes satisfying '{first_svc}': {sat_count}/{len(infr_nodes)}")
if sat_count == 0:
    # show what asset is blocking
    print("  Checking individual assets for first node:")
    nid, nattr = infr_nodes[0]
    for key in first_sattr:
        node_val = nattr.get(key, "MISSING")
        svc_val = first_sattr[key]
        print(f"    {key}: node={node_val}, service={svc_val}")
print()

# --- 5. energy calculation for one satisfying node (or any node) ---
nid, nattr = infr_nodes[0]
allocated = infr.node_assets.consume(stg.initial_resources[nid], nattr)
energy = (
    allocated.get("energy", 0)
    + 0.25 * allocated.get("cpu", 0)
    + 0.25 * allocated.get("gpu", 0)
    + 0.25 * allocated.get("ram", 0)
    + 0.25 * allocated.get("storage", 0)
)
print(f"Energy calc for node '{nid}':")
print(f"  initial_resources[nid] is nattr? {stg.initial_resources[nid] is nattr}")
print(f"  allocated: {dict(allocated)}")
print(f"  energy = {energy:.4f}  (energy > 0: {energy > 0})")
