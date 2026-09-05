"""
UC2-Capable BestFit — 12-month run.

Same infrastructure and application as uc2_capable_bestfit_experiment.py;
only MONTHS=12 (3600 ticks) for a full-year view of seasonal patterns,
more BestFit 100%-spike events, and statistically robust averages.
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
MONTHS           = 12
STEPS            = MONTHS * TICKS_PER_MONTH   # 3600
KILL_PROBABILITY = 0.005
REVIVE_MU        = 0.10
REVIVE_SIGMA     = 0.02
N_REPLICAS       = 2
OUT              = Path("results/uc2_capable_12m_bestfit")

if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)

    app      = get_replicated_sock_shop(n_replicas=N_REPLICAS, seed=SEED,
                                        include_assets=True)
    strategy = BestFitStrategy()
    infr     = get_calendar_infrastructure(seed=SEED, load_seed=0,
                                           kill_probability=KILL_PROBABILITY,
                                           revive_mu=REVIVE_MU,
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

    print(f"Running UC2-Capable BestFit 12-month ({MONTHS} months = {STEPS} steps)")
    print(f"Infrastructure: 187-node hierarchical, kill={KILL_PROBABILITY}, "
          f"revive~N({REVIVE_MU},{REVIVE_SIGMA}), capable nodes (ram 3–8 GB)")
    print(f"Application: SockShop with {N_REPLICAS}× FrontendService replicas")
    print(f"Output → {OUT}/\n")

    t0 = time()
    sim.run()
    elapsed = time() - t0

    print(f"\nDone. Elapsed: {elapsed:.1f}s  ({elapsed/60:.1f} min)")
    print(f"Effective rate: {STEPS/elapsed:.1f} ticks/s")
