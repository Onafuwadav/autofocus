"""Checks against the real focal sweeps. Skipped when the dataset is not downloaded."""

from pathlib import Path

import numpy as np
import pytest

from autofocus import METRICS, NORMALISERS, evaluate_folder
from autofocus.sweep import frame_number

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "Magnification-2(size)"
MATLAB = ROOT / "results" / "matlab_scores"

pytestmark = pytest.mark.skipif(not DATA.exists(), reason="dataset not downloaded (see README)")

# Best-focus frames from the dissertation's summary table.
DISSERTATION = {
    "Bright": {m: ["018"] * 4 for m in METRICS},
    "Normal": {
        "Laplacian": ["017", "028", "028", "028"],
        "Tenengrad": ["018", "028", "018", "017"],
        "Brenner": ["018", "028", "018", "028"],
        "FFT": ["018", "028", "028", "028"],
    },
    "Dim": {
        "Laplacian": ["017", "018", "014", "040"],
        "Tenengrad": ["018", "018", "018", "017"],
        "Brenner": ["018", "018", "018", "017"],
        "FFT": ["018", "018", "016", "018"],
    },
}


@pytest.fixture(scope="module", params=list(DISSERTATION))
def condition(request):
    return request.param, evaluate_folder(DATA / request.param)


def test_reproduces_dissertation_table(condition):
    name, res = condition
    for metric, expected in DISSERTATION[name].items():
        got = [frame_number(res.best_frame(norm, metric)) for norm in NORMALISERS]
        assert got == expected, (name, metric)


def test_scores_match_matlab(condition):
    name, res = condition
    ml = np.loadtxt(MATLAB / f"{name.lower()}.csv", delimiter=",").reshape(41, 4, 4, order="F")
    # Raw, Mean and Min-Max agree to rounding error. Contrast Stretch differs
    # by up to ~5e-5 because a few pixels fall on stretchlim bin edges.
    np.testing.assert_allclose(res.scores[:, :3], ml[:, :3], rtol=1e-10)
    np.testing.assert_allclose(res.scores[:, 3], ml[:, 3], rtol=1e-4)
