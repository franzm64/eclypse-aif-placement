"""
UC2-Calendar AIF experiment: Active Inference placement under calendar load.

Identical setup to uc2_calendar_experiment.py (BestFit baseline) so results
are directly comparable:
  - 187-node hierarchical infrastructure
  - SockShop with 2× FrontendService replicas
  - kill_probability = 2 %
  - 900 ticks (3 × 30-day months)
  - Metrics: user_delay, user_count, CPU/memory, tick_phase

Only the placement strategy changes: BestFitStrategy → AIFStrategy.
"""

from pathlib import Path
from time import time

from examples.user_distribution.infrastructure import get_calendar_infrastructure
from examples.user_distribution.metric import get_calendar_metrics
from examples.user_distribution.calendar_policy import TICKS_PER_MONTH
from examples.user_distribution.application import get_replicated_sock_shop
from examples.user_distribution.aif_strategy import AIFStrategy

from eclypse.simulation import Simulation, SimulationConfig

SEED             = 42
MONTHS           = 3
STEPS            = MONTHS * TICKS_PER_MONTH   # 900
KILL_PROBABILITY = 0.02
N_REPLICAS       = 2
OUT              = Path("results/uc2_aif")

if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)

    app      = get_replicated_sock_shop(n_replicas=N_REPLICAS, seed=SEED)
    strategy = AIFStrategy(seed=SEED, verbose=False)
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

    print(f"Running UC2-Calendar AIF (Active Inference, {MONTHS} months = {STEPS} steps)")
    print(f"Infrastructure: 187-node hierarchical, kill_probability={KILL_PROBABILITY}")
    print(f"Application: SockShop with {N_REPLICAS}× FrontendService replicas")
    print(f"Output → {OUT}/\n")

    t0 = time()
    sim.run()
    elapsed = time() - t0

    print(f"\nDone. Elapsed: {elapsed:.1f}s  ({elapsed/60:.1f} min)")
    print(f"Effective rate: {STEPS/elapsed:.1f} ticks/s")
    print(f"\nAIF action selection summary:")
    for name, count in strategy.action_counts.items():
        print(f"  {name:<10}: {count:4d}  ({count/STEPS*100:.1f}%)")
