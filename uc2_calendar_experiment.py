"""
UC2-Calendar experiment: BestFit baseline under synthetic calendar load.

Refinements vs first run (results/uc2_calendar-20260823_153717):
  - kill_probability reduced 10 % → 2 % per tick (realistic government infra)
  - FrontendService replicated on 2 nodes (FrontendService_0, FrontendService_1)
  - user_delay metric takes min latency to any FrontendService replica

900 steps  =  3 months × 30 days × 10 ticks/day
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
N_REPLICAS       = 2
OUT              = Path("results/uc2_calendar")

if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)

    app      = get_replicated_sock_shop(n_replicas=N_REPLICAS, seed=SEED)
    strategy = BestFitStrategy()
    infr     = get_calendar_infrastructure(seed=SEED, load_seed=0,
                                           kill_probability=KILL_PROBABILITY)

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

    print(f"Running UC2-Calendar baseline (BestFit, {MONTHS} months = {STEPS} steps)")
    print(f"Infrastructure: 187-node hierarchical, kill_probability={KILL_PROBABILITY}")
    print(f"Application: SockShop with {N_REPLICAS}× FrontendService replicas")
    print(f"Output → {OUT}/\n")

    t0 = time()
    sim.run()
    elapsed = time() - t0

    print(f"\nDone. Elapsed: {elapsed:.1f}s  ({elapsed/60:.1f} min)")
    print(f"Effective rate: {STEPS/elapsed:.1f} ticks/s")
