"""Synthetic focal sweeps: a sharp image blurred as a function of stage position z.

Used by the tests (where the right answer is known) and by the simulated
hill-climb demo.
"""

from __future__ import annotations

import cv2
import numpy as np


def make_pattern(size: int = 256, seed: int = 0) -> np.ndarray:
    """A textured image in [0, 1] with edges at many scales."""
    rng = np.random.default_rng(seed)
    img = np.zeros((size, size))
    # Random rectangles give sharp edges...
    for _ in range(40):
        x0, y0 = rng.integers(0, size - 8, 2)
        w, h = rng.integers(4, size // 4, 2)
        img[y0 : y0 + h, x0 : x0 + w] = rng.random()
    # ...and a checkerboard gives fine detail.
    yy, xx = np.mgrid[:size, :size]
    img += 0.25 * (((xx // 4) + (yy // 4)) % 2)
    img -= img.min()
    return img / img.max()


def gaussian_blur(img: np.ndarray, sigma: float) -> np.ndarray:
    """Gaussian blur; sigma <= 0 returns the image unchanged."""
    if sigma <= 0:
        return img.copy()
    k = 2 * int(np.ceil(3 * sigma)) + 1
    return cv2.GaussianBlur(img, (k, k), sigma, borderType=cv2.BORDER_REPLICATE)


def defocus_sigma(z: float, z_focus: float, sigma0: float = 0.7, sigma_per_um: float = 0.25) -> float:
    """Gaussian blur radius (pixels) for stage position z (micrometres).

    ``sigma0`` is the in-focus blur of the optics; away from focus the blur
    grows by ``sigma_per_um`` per micrometre. Adding the two in quadrature
    gives a smooth peak, so a hill climb sees a gradient right up to focus.
    """
    return float(np.hypot(sigma0, sigma_per_um * (z - z_focus)))


def render(sharp: np.ndarray, z: float, z_focus: float, noise: float = 0.0, gain: float = 1.0, rng=None, **kw) -> np.ndarray:
    """Image seen by the camera at position z, with optional brightness gain and noise."""
    img = gain * gaussian_blur(sharp, defocus_sigma(z, z_focus, **kw))
    if noise > 0:
        rng = rng if rng is not None else np.random.default_rng()
        img = img + rng.normal(0.0, noise, img.shape)
    return img


def blur_sweep(sharp: np.ndarray, z_positions, z_focus: float, noise: float = 0.0, seed: int = 0, **kw):
    """Render a whole focal sweep, one image per position."""
    rng = np.random.default_rng(seed)
    return [render(sharp, z, z_focus, noise=noise, rng=rng, **kw) for z in z_positions]
