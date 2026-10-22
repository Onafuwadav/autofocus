import numpy as np
import pytest

from autofocus import METRICS, NORMALISERS, evaluate
from autofocus.synthetic import blur_sweep, gaussian_blur, make_pattern

SIGMAS = [0, 0.5, 1, 1.5, 2, 3, 4, 6]


@pytest.fixture(scope="module")
def sharp():
    return make_pattern(128)


@pytest.mark.parametrize("metric", METRICS)
@pytest.mark.parametrize("norm", NORMALISERS)
def test_blur_lowers_every_metric_monotonically(sharp, metric, norm):
    scores = [METRICS[metric](NORMALISERS[norm](gaussian_blur(sharp, s))) for s in SIGMAS]
    assert all(a > b for a, b in zip(scores, scores[1:])), scores


@pytest.mark.parametrize("metric", METRICS)
@pytest.mark.parametrize("norm", NORMALISERS)
def test_argmax_of_synthetic_sweep_is_sharp_frame(sharp, metric, norm):
    z = np.arange(30, 71)  # 41 positions, 1 um apart, like the real sweep
    z_focus = 48.0         # frame 18
    images = blur_sweep(sharp * 200, z, z_focus, noise=0.5, sigma0=0.3, sigma_per_um=0.5)
    res = evaluate(images, metrics=[metric], norms=[norm])
    assert res.best_index(norm, metric) == 18


def test_metrics_are_brightness_invariant_after_minmax(sharp):
    for name, f in METRICS.items():
        a = f(NORMALISERS["MinMax"](sharp))
        b = f(NORMALISERS["MinMax"](3 * sharp + 10))
        assert a == pytest.approx(b, rel=1e-9), name


def test_flat_image_scores_zero():
    flat = np.full((64, 64), 7.0)
    norm = NORMALISERS["MinMax"](flat)
    for name in ("Laplacian", "Tenengrad", "Brenner"):
        assert METRICS[name](norm) == 0.0


def test_tenengrad_threshold_ignores_weak_gradients(sharp):
    from autofocus.metrics import tenengrad

    assert tenengrad(sharp, threshold=1e6) == 0.0
    assert 0 < tenengrad(sharp, threshold=0.5) < tenengrad(sharp)
