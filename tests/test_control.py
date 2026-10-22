import numpy as np
import pytest

from autofocus.control import AutofocusController, hill_climb

from demo.simulate_hill_climb import SimulatedStage


def test_hill_climb_finds_peak_of_parabola():
    pos, _ = hill_climb(lambda z: -(z - 3.7) ** 2, start=0.0, step=2.0, min_step=0.01)
    assert pos == pytest.approx(3.7, abs=0.02)


def test_hill_climb_respects_limits():
    pos, _ = hill_climb(lambda z: z, start=0.0, step=1.0, min_step=0.01, lo=-5, hi=2.5)
    assert pos == 2.5


@pytest.mark.parametrize("z_focus", [-55.0, 12.0, 80.0])
def test_controller_focuses_simulated_stage(z_focus):
    stage = SimulatedStage(z_focus=z_focus, noise=0.002, seed=1)
    ctrl = AutofocusController(stage)
    ctrl.focus()
    assert abs(stage.z - z_focus) < 0.5  # sub-micron, well inside the depth of field


def test_controller_tracks_drift():
    stage = SimulatedStage(z_focus=0.0, noise=0.002, seed=2)
    ctrl = AutofocusController(stage)
    ctrl.focus()
    for _ in range(80):
        stage.z_focus += 0.05  # 4 um of slow drift
        ctrl.track_step()
    assert abs(stage.z - stage.z_focus) < 0.75
