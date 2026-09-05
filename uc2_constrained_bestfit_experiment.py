"""
UC2-Constrained BestFit experiment: static BestFit under calendar load,
oscillating kill/recovery, AND realistic resource constraints.

Nodes have heterogeneous cpu (2–8 cores) and ram (1–8 GB).  SockShop
service requirements are enabled (FrontendService: cpu=2 ram=1.5 GB,
OrderService: cpu=2 ram=3.0 GB, etc.), so placement decisions are
genuinely resource-constrained.

Directly comparable to uc2_constrained_aif_experiment.py.
"""

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
OUT              = Path("results/uc2_constrained_bestfit")

if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)

    app      = get_replicated_sock_shop(n_replicas=N_REPLICAS, seed=SEED,
                                        include_assets=True)
    strategy = BestFitStrategy()
    infr     = get_calendar_infrastructure(seed=SEED, load_seed=0,
                                           kill_probability=KILL_PROBABILITY,
                                           revive_sigma=REVIVE_SIGMA,
                                           constrained=True)

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

    print(f"Running UC2-Constrained BestFit ({MONTHS} months = {STEPS} steps)")
    print(f"Infrastructure: 187-node hierarchical, kill={KILL_PROBABILITY}, "
          f"revive~N({KILL_PROBABILITY},{REVIVE_SIGMA}), constrained cpu/ram")
    print(f"Application: SockShop with {N_REPLICAS}× FrontendService replicas "
          f"(service requirements enabled)")
    print(f"Output → {OUT}/\n")

    t0 = time()
    sim.run()
    elapsed = time() - t0

    print(f"\nDone. Elapsed: {elapsed:.1f}s  ({elapsed/60:.1f} min)")
    print(f"Effective rate: {STEPS/elapsed:.1f} ticks/s")
