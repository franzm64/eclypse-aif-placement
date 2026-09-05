"""
UC1 experiment: placement strategy comparison.
432 simulations (3 strategies x 3 topologies x 2 nodes x 2 seeds x 2 loads x 6 policies),
600 steps each. Results saved to results/uc1/results.csv.
"""

import itertools
import time
from pathlib import Path

import pandas as pd

from examples.grid_analysis.applications import get_apps
from examples.grid_analysis.infrastructure import get_infrastructure
from examples.grid_analysis.metrics import get_metrics
from examples.grid_analysis.strategy import EnergyMinimizationStrategy
from eclypse.placement.strategies import BestFitStrategy, FirstFitStrategy
from eclypse.simulation import Simulation
from eclypse.simulation.config import SimulationConfig


RESULTS_DIR = Path("results/uc1")

GRID = {
    "max_steps": [600],
    "strategy":  ["first-fit", "best-fit", "min-energy"],
    "topology":  [("star",), ("hierarchical",), ("random", 0.5)],
    "nodes":     [20, 50],
    "seed":      [42, 3997],
    "load":      [0.0, 0.5],
    "policy":    [
        ("degrade", 0.4), ("degrade", 0.5), ("degrade", 0.6),
        ("kill", 0.01),   ("kill", 0.05),   ("kill", 0.1),
    ],
}


def make_strategy(name):
    if name == "first-fit":
        return FirstFitStrategy()
    if name == "best-fit":
        return BestFitStrategy()
    if name == "min-energy":
        return EnergyMinimizationStrategy()
    raise ValueError(name)


def run_one(config, out_dir):
    out_dir.parent.mkdir(parents=True, exist_ok=True)  # ensure parent exists; ECLYPSE creates out_dir
    infr = get_infrastructure(config)
    apps = get_apps(seed=config["seed"])
    sim_config = SimulationConfig(
        step_every_ms="auto",
        seed=config["seed"],
        max_steps=config["max_steps"],
        path=out_dir,
        include_default_metrics=False,
        events=get_metrics(),
        log_level="CRITICAL",
    )
    sim = Simulation(infrastructure=infr, simulation_config=sim_config)
    for app in apps:
        sim.register(app, make_strategy(config["strategy"]))
    sim.run()


def placement_success_rate(out_dir):
    csv = out_dir / "csv" / "application.csv"
    df = pd.read_csv(csv)
    placed = df[df["callback_id"] == "is_placed"].copy()
    placed["value"] = placed["value"].map({"True": True, "False": False})
    return placed["value"].mean()


def all_configs():
    keys = list(GRID.keys())
    for combo in itertools.product(*GRID.values()):
        yield dict(zip(keys, combo))


if __name__ == "__main__":
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    configs = list(all_configs())
    n = len(configs)
    print(f"Starting UC1 experiment: {n} simulations, 600 steps each")
    print(f"Results → {RESULTS_DIR}/results.csv\n")

    records = []
    wall_start = time.perf_counter()

    for i, cfg in enumerate(configs, 1):
        sim_dir = RESULTS_DIR / f"sim_{i:04d}"
        t0 = time.perf_counter()
        run_one(cfg, sim_dir)
        elapsed = time.perf_counter() - t0
        rate = placement_success_rate(sim_dir)

        topo_str = cfg["topology"][0]
        records.append({
            "sim_id":    i,
            "strategy":  cfg["strategy"],
            "topology":  topo_str,
            "nodes":     cfg["nodes"],
            "seed":      cfg["seed"],
            "load":      cfg["load"],
            "policy_type":  cfg["policy"][0],
            "policy_param": cfg["policy"][1],
            "placement_success": rate,
            "time_s":    round(elapsed, 3),
        })

        eta = (time.perf_counter() - wall_start) / i * (n - i)
        print(f"[{i:>3}/{n}] {cfg['strategy']:<12} {topo_str:<14} "
              f"n={cfg['nodes']:>2} seed={cfg['seed']:>6} "
              f"load={cfg['load']} {str(cfg['policy']):<20} "
              f"placed={rate:.2f}  {elapsed:.1f}s  ETA {eta:.0f}s")

    df = pd.DataFrame(records)
    df.to_csv(RESULTS_DIR / "results.csv", index=False)

    wall_total = time.perf_counter() - wall_start
    print(f"\nDone. Total time: {wall_total:.1f}s ({wall_total/60:.1f} min)")
    print(f"Results saved to {RESULTS_DIR}/results.csv")
