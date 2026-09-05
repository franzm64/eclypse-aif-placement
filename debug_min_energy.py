"""
Debug script: trace why min-energy never places any applications.
Runs a single 5-step simulation and instruments the place() method.
"""

import types
from examples.grid_analysis.applications import get_apps
from examples.grid_analysis.infrastructure import get_infrastructure
from examples.grid_analysis.metrics import get_metrics
from examples.grid_analysis.strategy import EnergyMinimizationStrategy
from eclypse.simulation import Simulation
from eclypse.simulation.config import SimulationConfig

config = {
    "seed": 42,
    "max_steps": 5,
    "nodes": 20,
    "load": 0.0,
    "policy": ("kill", 0.01),
    "topology": ("star",),
    "strategy": "min-energy",
}

stg = EnergyMinimizationStrategy()
call_count = [0]

original_place = stg.place

def instrumented_place(self, infrastructure, application, placements, placement_view):
    call_count[0] += 1
    if call_count[0] > 3:
        return original_place(infrastructure, application, placements, placement_view)

    print(f"\n--- place() call #{call_count[0]} for app '{application.name}' ---")

    # Check initial_resources snapshot
    if self.initial_resources is None:
        print("  initial_resources: not yet set")
    else:
        sample_node = next(iter(self.initial_resources))
        live_node_data  = dict(infrastructure.nodes(data=True))[sample_node]
        snap_node_data  = self.initial_resources[sample_node]
        print(f"  Sample node '{sample_node}':")
        print(f"    snapshot (initial_resources): {dict(snap_node_data)}")
        print(f"    live (infrastructure):        {dict(live_node_data)}")
        same_object = snap_node_data is live_node_data
        print(f"    same object? {same_object}  ← if True, snapshot is a LIVE VIEW")

    # Run one candidate energy calculation manually
    infr_nodes = list(infrastructure.available.nodes(data=True))
    if infr_nodes and self.initial_resources is not None:
        node, nattr = infr_nodes[0]
        allocated = infrastructure.node_assets.consume(self.initial_resources[node], nattr)
        energy = (
            allocated.get("energy", 0)
            + 0.25 * allocated.get("cpu", 0)
            + 0.25 * allocated.get("gpu", 0)
            + 0.25 * allocated.get("ram", 0)
            + 0.25 * allocated.get("storage", 0)
        )
        print(f"  First candidate node '{node}':")
        print(f"    nattr (current):    cpu={nattr.get('cpu')}, ram={nattr.get('ram')}, energy={nattr.get('energy')}")
        print(f"    allocated (consumed): {allocated}")
        print(f"    computed energy: {energy}  (condition: energy > 0 → {energy > 0})")

    result = original_place(infrastructure, application, placements, placement_view)
    placed = {k: v for k, v in result.items() if v is not None}
    print(f"  → placed {len(placed)}/{len(result)} services: {placed}")
    return result

stg.place = types.MethodType(instrumented_place, stg)

infr = get_infrastructure(config)
apps = get_apps(seed=config["seed"])

sim_config = SimulationConfig(
    step_every_ms="auto",
    seed=config["seed"],
    max_steps=config["max_steps"],
    include_default_metrics=False,
    events=get_metrics(),
    log_level="CRITICAL",
)

sim = Simulation(infrastructure=infr, simulation_config=sim_config)
for app in apps:
    sim.register(app, stg)
sim.run()
print(f"\nTotal place() calls: {call_count[0]}")
