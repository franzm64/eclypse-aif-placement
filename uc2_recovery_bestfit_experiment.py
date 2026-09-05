"""
UC2-Recovery BestFit experiment: static BestFit placement under calendar load
with oscillating node kill/recovery dynamics.

Revival rate sampled each tick from N(mu=kill_probability, sigma=REVIVE_SIGMA),
creating realistic churn: some ticks the infrastructure degrades, some it recovers.
Long-run equilibrium: ~50% nodes alive on average.

Directly comparable to uc2_recovery_aif_experiment.py (same infrastructure,
same seed, only strategy differs).
"""
import sys
sys.path.insert(0, "eclypse")

from pathlib import Path
from time import time

from examples.user_distribution.infrastructure import get_calendar_infrastructure
from examples.user_distribution.metric import get_calendar_metrics
from examples.user_distribution.calendar_policy import TICKS_PER_MONTH
from examples.user_distribution.application import get_replicated_sock_shop

from eclypse.placement.strategies import BestFitStrategy
from eclypse.simulation import Simulation, SimulationConfig

SEED             = 42
MONTHS           = 3
STEPS            = MONTHS * TICKS_PER_MONTH   # 900
KILL_PROBABILITY = 0.02
REVIVE_SIGMA     = 0.01    # revival ~ N(0.02, 0.01) per tick
N_REPLICAS       = 2
OUT              = Path("results/uc2_recovery_bestfit")

if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)

    app      = get_replicated_sock_shop(n_replicas=N_REPLICAS, seed=SEED)
    strategy = BestFitStrategy()
    infr     = get_calendar_infrastructure(seed=SEED, load_seed=0,
                                           kill_probability=KILL_PROBABILITY,
                                           revive_sigma=REVIVE_SIGMA)

    sim_config = SimulationConfig(
        step_every_ms="auto",
        seed=SEED,
        max_steps=STEPS,
        path=OUT,
        events=get_calendar_metrics(),
        log_level="CRITICAL",
    )

    sim = Simulation(infr, simulation_config=sim_config)
    sim.register(app, strategy)

    print(f"Running UC2-Recovery BestFit ({MONTHS} months = {STEPS} steps)")
    print(f"Infrastructure: 187-node hierarchical, kill={KILL_PROBABILITY}, "
          f"revive~N({KILL_PROBABILITY},{REVIVE_SIGMA})")
    print(f"Application: SockShop with {N_REPLICAS}× FrontendService replicas")
    print(f"Output → {OUT}/\n")

    t0 = time()
    sim.run()
    elapsed = time() - t0

    print(f"\nDone. Elapsed: {elapsed:.1f}s  ({elapsed/60:.1f} min)")
    print(f"Effective rate: {STEPS/elapsed:.1f} ticks/s")
