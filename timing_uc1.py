"""
Timing run for the scaled-down UC1 grid (72 simulations, sequential).
Runs every combination, reports per-simulation time and total wall clock.
"""

import itertools
import time

from examples.grid_analysis.applications import get_apps
from examples.grid_analysis.infrastructure import get_infrastructure
from examples.grid_analysis.metrics import get_metrics
from examples.grid_analysis.strategy import EnergyMinimizationStrategy
from eclypse.placement.strategies import BestFitStrategy, FirstFitStrategy
from eclypse.simulation import Simulation
from eclypse.simulation.config import SimulationConfig


GRID = {
    "max_steps": [200],
    "strategy":  ["first-fit", "best-fit", "min-energy"],
    "topology":  [("star",), ("hierarchical",), ("random", 0.5)],
    "nodes":     [20, 50],
    "seed":      [42, 3997],
    "load":      [0.0, 0.5],
    "policy":    [("degrade", 0.5), ("kill", 0.05)],
}


def make_strategy(name):
    if name == "first-fit":
        return FirstFitStrategy()
    if name == "best-fit":
        return BestFitStrategy()
    if name == "min-energy":
        return EnergyMinimizationStrategy()
    raise ValueError(name)


def run_one(config):
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
        sim.register(app, make_strategy(config["strategy"]))
    sim.run()


def all_configs():
    keys = list(GRID.keys())
    for combo in itertools.product(*GRID.values()):
        yield dict(zip(keys, combo))


if __name__ == "__main__":
    configs = list(all_configs())
    n = len(configs)
    print(f"Total simulations: {n}")
    print(f"{'#':>4}  {'strategy':<12} {'topology':<18} {'nodes':>5} {'seed':>6} {'load':>5} {'policy':<18} {'time(s)':>8}")
    print("-" * 85)

    times = []
    wall_start = time.perf_counter()

    for i, cfg in enumerate(configs, 1):
        t0 = time.perf_counter()
        run_one(cfg)
        elapsed = time.perf_counter() - t0
        times.append(elapsed)

        topo = str(cfg["topology"])
        policy = str(cfg["policy"])
        print(f"{i:>4}  {cfg['strategy']:<12} {topo:<18} {cfg['nodes']:>5} {cfg['seed']:>6} {cfg['load']:>5} {policy:<18} {elapsed:>8.2f}")

    wall_total = time.perf_counter() - wall_start
    avg = sum(times) / len(times)
    print("-" * 85)
    print(f"Average per simulation : {avg:.2f}s")
    print(f"Total wall clock       : {wall_total:.1f}s  ({wall_total/60:.1f} min)")
