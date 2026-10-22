"""The four focus metrics compared in the dissertation.

All metrics take a 2-D float image and return a scalar where larger means
sharper. Each one follows the MATLAB implementation exactly (kernels, border
handling, variance normalisation) so the ported results line up.
"""

from __future__ import annotations

import cv2
import numpy as np

# fspecial('laplacian', 0.2)
_ALPHA = 0.2
_LAPLACIAN = (4 / (_ALPHA + 1)) * np.array(
    [
        [_ALPHA / 4, (1 - _ALPHA) / 4, _ALPHA / 4],
        [(1 - _ALPHA) / 4, -1.0, (1 - _ALPHA) / 4],
        [_ALPHA / 4, (1 - _ALPHA) / 4, _ALPHA / 4],
    ]
)

# fspecial('sobel'), as used by imgradientxy(..., 'sobel'). Sign does not
# matter because the gradients are squared.
_SOBEL_Y = np.array([[1.0, 2.0, 1.0], [0.0, 0.0, 0.0], [-1.0, -2.0, -1.0]])
_SOBEL_X = _SOBEL_Y.T


def _filter(img: np.ndarray, kernel: np.ndarray) -> np.ndarray:
    # imfilter(..., 'replicate') is correlation with edge replication.
    return cv2.filter2D(img, cv2.CV_64F, kernel, borderType=cv2.BORDER_REPLICATE)


def laplacian(img: np.ndarray) -> float:
    """Variance of the Laplacian (sample variance, as MATLAB ``var``)."""
    return float(np.var(_filter(img, _LAPLACIAN), ddof=1))


def tenengrad(img: np.ndarray, threshold: float = 0.0) -> float:
    """Mean squared Sobel gradient magnitude.

    ``threshold`` is the gradient-magnitude threshold T. The dissertation used
    T = 0, which reduces to ``mean(Gx.^2 + Gy.^2)``. With T > 0, pixels whose
    magnitude is at or below T contribute zero.
    """
    gx = _filter(img, _SOBEL_X)
    gy = _filter(img, _SOBEL_Y)
    g2 = gx * gx + gy * gy
    if threshold > 0:
        g2 = np.where(g2 > threshold * threshold, g2, 0.0)
    return float(g2.mean())


def brenner(img: np.ndarray) -> float:
    """Sum of squared differences between pixels two columns apart."""
    d = img[:, 2:] - img[:, :-2]
    return float(np.sum(d * d))


def fft(img: np.ndarray, radius: int = 30) -> float:
    """Sum of FFT magnitude after zeroing a low-frequency square at the centre.

    The square is (2 * radius + 1) pixels wide, centred where MATLAB's
    ``round(size/2)`` lands, matching the original script.
    """
    mag = np.abs(np.fft.fftshift(np.fft.fft2(img)))
    rows, cols = mag.shape
    # MATLAB round() is half away from zero; convert from 1-based to 0-based.
    cy = int(np.floor(rows / 2 + 0.5)) - 1
    cx = int(np.floor(cols / 2 + 0.5)) - 1
    mag[max(cy - radius, 0) : cy + radius + 1, max(cx - radius, 0) : cx + radius + 1] = 0
    return float(mag.sum())


METRICS = {
    "Laplacian": laplacian,
    "Tenengrad": tenengrad,
    "Brenner": brenner,
    "FFT": fft,
}
