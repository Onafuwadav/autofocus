"""Checks that the port follows the MATLAB definitions in the original script."""

from pathlib import Path

import numpy as np
import pytest

from autofocus import load_image
from autofocus.metrics import _LAPLACIAN, brenner, fft, laplacian, tenengrad
from autofocus.normalise import contrast_stretch, minmax, to_gray

SAMPLE = Path(__file__).resolve().parents[1] / "data" / "sample"


def test_laplacian_kernel_matches_fspecial():
    # fspecial('laplacian', 0.2) from its documented formula, to 4 d.p.
    expected = np.array([[0.1667, 0.6667, 0.1667], [0.6667, -3.3333, 0.6667], [0.1667, 0.6667, 0.1667]])
    np.testing.assert_allclose(_LAPLACIAN, expected, atol=1e-4)
    assert _LAPLACIAN.sum() == pytest.approx(0.0, abs=1e-12)


def test_rgb2gray_rounds_like_matlab():
    rgb = np.array([[[255, 0, 0], [0, 255, 0], [0, 0, 255], [10, 20, 30]]], dtype=np.uint8)
    # rounded weighted sums with the rgb2gray coefficients
    np.testing.assert_array_equal(to_gray(rgb), [[76, 150, 29, 18]])


def test_brenner_uses_columns_two_apart():
    img = np.tile(np.arange(5.0), (2, 1))  # each row 0 1 2 3 4
    assert brenner(img) == 2 * 3 * 4.0     # 2 rows x 3 diffs x 2^2


def test_tenengrad_of_ramp():
    img = np.tile(np.arange(8.0), (8, 1))
    # interior Sobel x response of a unit ramp is 8; replicated borders give 4
    gx = np.full(8, 8.0)
    gx[[0, -1]] = 4.0
    assert tenengrad(img) == pytest.approx(np.mean(gx**2))


def test_fft_ignores_constant_image():
    assert fft(np.ones((100, 120))) == pytest.approx(0.0, abs=1e-6)


def test_contrast_stretch_output_range():
    rng = np.random.default_rng(1)
    out = contrast_stretch(rng.normal(100, 20, (64, 64)))
    assert out.min() == 0.0 and out.max() == 1.0


@pytest.mark.skipif(not (SAMPLE / "bottom_018.png").exists(), reason="sample images not present")
def test_sample_images_match_dissertation_ordering():
    """Normal-condition frame 018 (in focus) must outscore frame 000 on every metric."""
    blurred = load_image(SAMPLE / "bottom_000.png")
    focused = load_image(SAMPLE / "bottom_018.png")
    for f in (laplacian, tenengrad, brenner, fft):
        assert f(minmax(focused)) > f(minmax(blurred))
