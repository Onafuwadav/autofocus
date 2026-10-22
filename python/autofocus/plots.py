"""Focus-curve figures in the same 2x2, log-y layout as the dissertation."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

from .sweep import SweepResult  # noqa: E402


def plot_curves(res: SweepResult, title: str, path: str | Path) -> None:
    fig, axes = plt.subplots(2, 2, figsize=(10, 7.5))
    x = np.arange(1, len(res.names) + 1)  # MATLAB plots against image number 1..N
    for m, (ax, metric) in enumerate(zip(axes.flat, res.metrics)):
        for n, norm in enumerate(res.norms):
            ax.plot(x, res.scores[:, n, m], lw=2, label=norm)
        ax.set_yscale("log")
        ax.set_title(metric)
        ax.set_xlabel("Image Number")
        ax.set_ylabel("Focus Score")
        ax.grid(True, which="both", alpha=0.3)
        ax.legend(fontsize=8)
    fig.suptitle(title)
    fig.tight_layout()
    fig.savefig(path, dpi=120)
    plt.close(fig)
