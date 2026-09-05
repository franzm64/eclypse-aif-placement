"""
UC2 experiment: response time and user delay for SockShop under varying user load.
Reproduces the paper's UC2 (4167 steps, 187-node hierarchical infrastructure,
user load doubles at ticks 1000/3000 and halves at 2000/4000).
"""
import sys
sys.path.insert(0, "eclypse")

from pathlib import Path
from time import time

from examples.user_distribution.infrastructure import get_infrastructure
from examples.user_distribution.metric import get_metrics

from eclypse.builders.application import get_sock_shop
from eclypse.placement.strategies import BestFitStrategy
from eclypse.simulation import Simulation, SimulationConfig

SEED  = 42
STEPS = 4167
OUT   = Path("results/uc2")

if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)

    app        = get_sock_shop(seed=SEED)
    strategy   = BestFitStrategy()
    infr       = get_infrastructure(SEED)
    sim_config = SimulationConfig(
        step_every_ms="auto",
        seed=SEED,
        max_steps=STEPS,
        path=OUT,
        events=get_metrics(),
        log_level="CRITICAL",
    )

    sim = Simulation(infr, simulation_config=sim_config)
    sim.register(app, strategy)

    print(f"Running UC2: {STEPS} steps, 187 nodes, SockShop ({len(list(app.nodes))} services)")
    print(f"Output → {OUT}/csv/\n")

    t0 = time()
    sim.run()
    elapsed = time() - t0

    print(f"\nDone. Elapsed: {elapsed:.1f}s ({elapsed/60:.1f} min)")
    print(f"Effective rate: {STEPS/elapsed:.2f} ticks/sec")
