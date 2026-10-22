"""Run every normalisation x metric combination over a focal sweep."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from pathlib import Path

import cv2
import numpy as np

from .metrics import METRICS
from .normalise import NORMALISERS, to_gray

CONDITIONS = ("Bright", "Normal", "Dim")


def load_image(path: str | Path) -> np.ndarray:
    """Read an image file and return grayscale float64 (MATLAB-equivalent)."""
    img = cv2.imread(str(path), cv2.IMREAD_UNCHANGED)
    if img is None:
        raise FileNotFoundError(path)
    if img.ndim == 3:
        img = cv2.cvtColor(img, cv2.COLOR_BGRA2RGB if img.shape[2] == 4 else cv2.COLOR_BGR2RGB)
    return to_gray(img)


def list_frames(folder: str | Path) -> list[Path]:
    """PNG files in a folder, sorted by name (the MATLAB ``dir`` order)."""
    files = sorted(Path(folder).glob("*.png"))
    if not files:
        raise FileNotFoundError(f"no PNG files in {folder}")
    return files


@dataclass
class SweepResult:
    """Focus curves for one image stack.

    ``scores[k, n, m]`` is the score of frame ``k`` under normaliser ``n`` and
    metric ``m``; ``times`` has the same shape and holds seconds per metric call.
    """

    names: list[str]
    scores: np.ndarray
    times: np.ndarray
    norms: list[str] = field(default_factory=lambda: list(NORMALISERS))
    metrics: list[str] = field(default_factory=lambda: list(METRICS))

    def best_index(self, norm: str, metric: str) -> int:
        n, m = self.norms.index(norm), self.metrics.index(metric)
        return int(np.argmax(self.scores[:, n, m]))

    def best_frame(self, norm: str, metric: str) -> str:
        return self.names[self.best_index(norm, metric)]

    def mean_time(self, metric: str) -> float:
        return float(self.times[:, :, self.metrics.index(metric)].mean())


def evaluate(images, names=None, norms=None, metrics=None) -> SweepResult:
    """Score a sequence of grayscale images with every combination.

    Only the metric call is timed, as in the original script.
    """
    norms = list(norms or NORMALISERS)
    metrics = list(metrics or METRICS)
    images = list(images)
    names = list(names) if names is not None else [f"{i:03d}" for i in range(len(images))]
    scores = np.zeros((len(images), len(norms), len(metrics)))
    times = np.zeros_like(scores)
    for k, img in enumerate(images):
        for n, norm in enumerate(norms):
            img_n = NORMALISERS[norm](img)
            for m, metric in enumerate(metrics):
                t0 = time.perf_counter()
                scores[k, n, m] = METRICS[metric](img_n)
                times[k, n, m] = time.perf_counter() - t0
    return SweepResult(names, scores, times, norms, metrics)


def evaluate_folder(folder: str | Path, exclude=()) -> SweepResult:
    """Load every PNG in ``folder`` (minus any names in ``exclude``) and score it."""
    files = [f for f in list_frames(folder) if f.name not in set(exclude)]
    return evaluate((load_image(f) for f in files), names=[f.stem for f in files])


def frame_number(name: str) -> str:
    """'bottom_018' -> '018'."""
    return name.rsplit("_", 1)[-1]
