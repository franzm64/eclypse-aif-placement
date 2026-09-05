"""
Smoke test for UC1 (grid_analysis). Runs 3 strategies x 1 config = 3 simulations,
20 steps each. Confirms Ray, ECLYPSE, and all imports work correctly.
"""
import ray
from examples.grid_analysis.applications import get_apps
from examples.grid_analysis.infrastructure import get_infrastructure
from examples.grid_analysis.metrics import get_metrics
from examples.grid_analysis.strategy import EnergyMinimizationStrategy
from eclypse.placement.strategies import BestFitStrategy, FirstFitStrategy
from eclypse.simulation import Simulation
from eclypse.simulation.config import SimulationConfig


STRATEGIES = {
    "first-fit": FirstFitStrategy(),
    "best-fit": BestFitStrategy(),
    "min-energy": EnergyMinimizationStrategy(),
}

BASE_CONFIG = {
    "seed": 42,
    "max_steps": 20,
    "nodes": 20,
    "load": 0.0,
    "policy": ("kill", 0.01),
    "topology": ("star",),
}


def run_one(strategy_name):
    config = {**BASE_CONFIG, "strategy": strategy_name}
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
        sim.register(app, STRATEGIES[strategy_name])
    sim.run()
    print(f"  [{strategy_name}] OK")


if __name__ == "__main__":
    ray.init(ignore_reinit_error=True)
    print("Ray initialized.")
    print("Running smoke test (3 strategies x 20 steps)...")
    for name in STRATEGIES:
        run_one(name)
    print("Smoke test passed.")
    ray.shutdown()
