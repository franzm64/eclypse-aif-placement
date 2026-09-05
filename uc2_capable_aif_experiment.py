"""
UC2-Capable AIF experiment: Active Inference placement under calendar load with
redesigned infrastructure — capable nodes, realistic failure rate.

Identical setup to uc2_capable_bestfit_experiment.py — only strategy differs.
With realistic uptime (~95 % alive), AIF's pack/spread/balance actions have room
to optimise latency: spread places FrontendService replicas closer to edge users
(shorter paths), while pack co-locates services on high-capacity cloud nodes.

Directly comparable to uc2_capable_bestfit_experiment.py.
"""
import sys
sys.path.insert(0, "eclypse")

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
KILL_PROBABILITY = 0.005   # 0.5 % per tick — rare hardware fault
REVIVE_MU        = 0.10    # 10 % per tick — fast automated recovery
REVIVE_SIGMA     = 0.02    # small jitter around mean
N_REPLICAS       = 2
OUT              = Path("results/uc2_capable_aif")

if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)

    app      = get_replicated_sock_shop(n_replicas=N_REPLICAS, seed=SEED,
                                        include_assets=True)
    strategy = AIFStrategy(seed=SEED, verbose=False)
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

    print(f"Running UC2-Capable AIF ({MONTHS} months = {STEPS} steps)")
    print(f"Infrastructure: 187-node hierarchical, kill={KILL_PROBABILITY}, "
          f"revive~N({REVIVE_MU},{REVIVE_SIGMA}), capable nodes (ram 3–8 GB)")
    print(f"Application: SockShop with {N_REPLICAS}× FrontendService replicas "
          f"(cpu/ram/availability requirements enabled)")
    print(f"Output → {OUT}/\n")

    t0 = time()
    sim.run()
    elapsed = time() - t0

    print(f"\nDone. Elapsed: {elapsed:.1f}s  ({elapsed/60:.1f} min)")
    print(f"Effective rate: {STEPS/elapsed:.1f} ticks/s")
    print(f"\nAIF action selection summary:")
    for name, count in strategy.action_counts.items():
        print(f"  {name:<10}: {count:4d}  ({count/STEPS*100:.1f}%)")
