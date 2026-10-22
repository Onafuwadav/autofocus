"""Grayscale conversion and the four per-image normalisation schemes.

Each function mirrors the MATLAB code in
``matlab/focus_metric_comparison_original.m`` so the Python port selects the
same best-focus frames.
"""

from __future__ import annotations

import numpy as np

# Coefficients used by MATLAB's rgb2gray (from its YIQ conversion).
_RGB2GRAY = np.array([0.298936021293775, 0.587043074451121, 0.114020904255103])


def to_gray(img: np.ndarray) -> np.ndarray:
    """Convert an image to grayscale float64, matching MATLAB ``double(rgb2gray(img))``.

    ``img`` is RGB channel order. For uint8 input, MATLAB rounds the weighted
    sum back to uint8 before ``double()``, so that is done here too.
    """
    if img.ndim == 3:
        gray = img[..., :3].astype(np.float64) @ _RGB2GRAY
        if np.issubdtype(img.dtype, np.integer):
            info = np.iinfo(img.dtype)
            gray = np.clip(np.round(gray), info.min, info.max)
        return gray
    return img.astype(np.float64)


def raw(img: np.ndarray) -> np.ndarray:
    """No normalisation."""
    return img


def mean(img: np.ndarray) -> np.ndarray:
    """Divide the image by its own mean intensity."""
    return img / img.mean()


def minmax(img: np.ndarray) -> np.ndarray:
    """Linearly rescale the image to [0, 1] using its own min and max."""
    lo, hi = img.min(), img.max()
    if hi - lo == 0:
        return np.zeros_like(img)
    return (img - lo) / (hi - lo)


def _stretchlim(img01: np.ndarray, tol=(0.01, 0.99), nbins: int = 65536) -> tuple[float, float]:
    """MATLAB ``stretchlim`` for a double image in [0, 1].

    MATLAB builds the histogram of a double image with 65536 bins here, not
    256; the limits it returns (checked against R2026a) fall on that grid.
    """
    # imhist puts value x into bin round(x * (nbins - 1)).
    idx = np.round(img01.ravel() * (nbins - 1)).astype(np.int64)
    counts = np.bincount(idx, minlength=nbins)
    cdf = np.cumsum(counts) / counts.sum()
    ilow = int(np.argmax(cdf > tol[0]))
    ihigh = int(np.argmax(cdf >= tol[1]))
    if ilow == ihigh:
        ilow, ihigh = 0, nbins - 1
    return ilow / (nbins - 1), ihigh / (nbins - 1)


def contrast_stretch(img: np.ndarray, tol=(0.01, 0.99)) -> np.ndarray:
    """Rescale to [0, 1], then stretch between the 1st and 99th percentiles.

    Equivalent to MATLAB ``imadjust(mat2gray(I), stretchlim(mat2gray(I), tol), [])``.
    """
    scaled = minmax(img)
    lo, hi = _stretchlim(scaled, tol)
    return (np.clip(scaled, lo, hi) - lo) / (hi - lo)


NORMALISERS = {
    "Raw": raw,
    "Mean": mean,
    "MinMax": minmax,
    "ContrastStretch": contrast_stretch,
}
