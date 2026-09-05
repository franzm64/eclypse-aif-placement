"""
UC3 experiment: computer-vision ML pipeline (MNIST image prediction).
Reproduces the paper's UC3: 600 steps, star infrastructure (5 clients),
RandomStrategy with spread, DegradePolicy degrading link latency from
tick 450 onward.

Three services run as real Ray Actors:
  EndService    – streams test images, records accuracy
  PredictorService – CNN inference (REST /predict)
  TrainerService   – trains MNIST model in a background thread, serves
                     model snapshots via REST /get_model

Trainer patched to use CPU when CUDA is unavailable.
"""
import os
import sys

# Must be set before Ray starts so all worker processes inherit it.
_eclypse_abs = str((lambda p: p / "eclypse")(
    __import__("pathlib").Path(__file__).parent
).resolve())
os.environ["PYTHONPATH"] = _eclypse_abs + os.pathsep + os.environ.get("PYTHONPATH", "")
sys.path.insert(0, _eclypse_abs)

from pathlib import Path
from time import time

from examples.image_prediction.application import image_app as app
from examples.image_prediction.metrics import get_metrics
from examples.image_prediction.services.utils import STEPS, STEP_EVERY_MS
from examples.image_prediction.update_policy import DegradePolicy

from eclypse.builders.infrastructure import get_star
from eclypse.placement.strategies import RandomStrategy
from eclypse.remote.bootstrap import RemoteBootstrap
from eclypse.simulation import Simulation, SimulationConfig

SEED = 2
OUT  = Path("results/uc3")
OUT.mkdir(parents=True, exist_ok=True)

_bootstrap = RemoteBootstrap()  # PYTHONPATH already set in os.environ above

if __name__ == "__main__":
    sim_config = SimulationConfig(
        seed=SEED,
        max_steps=STEPS,
        step_every_ms=STEP_EVERY_MS,
        include_default_metrics=False,
        events=get_metrics(),
        log_to_file=True,
        path=OUT,
        remote=_bootstrap,
    )

    infr = get_star(
        infrastructure_id="IPInfr",
        n_clients=5,
        seed=SEED,
        update_policies=DegradePolicy(epochs=STEPS),
        include_default_assets=True,
        resource_init="max",
        symmetric=True,
    )

    sim = Simulation(infr, simulation_config=sim_config)
    sim.register(app, RandomStrategy(spread=True))

    print(f"Running UC3: {STEPS} steps × {STEP_EVERY_MS}ms, "
          f"star infrastructure (5 clients)")
    print(f"DegradePolicy fires at tick {int(0.75*STEPS)} (latency → 1000ms)")
    print(f"Output → {OUT}/\n")

    t0 = time()
    sim.run()
    elapsed = time() - t0

    print(f"\nDone. Elapsed: {elapsed:.1f}s ({elapsed/60:.1f} min)")
