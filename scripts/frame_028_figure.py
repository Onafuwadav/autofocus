"""Figure: why most normalised metrics pick frame 028 in the Normal stack.

Frame 028 is almost black (an under-exposed or dropped capture). Per-image
normalisation stretches its few grey levels to the full range, so
quantisation and sensor noise look like fine detail.

    python scripts/frame_028_figure.py
"""

import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "python"))

from autofocus import load_image, minmax, tenengrad  # noqa: E402

folder = ROOT / "data" / "Magnification-2(size)" / "Normal"
frames = ["bottom_018", "bottom_027", "bottom_028"]
imgs = [load_image(folder / f"{f}.png") for f in frames]
crop = (slice(400, 656), slice(500, 756))

fig, axes = plt.subplots(2, 3, figsize=(11, 7.4))
for i, (name, img) in enumerate(zip(frames, imgs)):
    axes[0, i].imshow(img[crop], cmap="gray", vmin=0, vmax=160)
    axes[0, i].set_title(f"{name}  raw\nmean {img.mean():.2f}, max {img.max():.0f}, "
                         f"{len(np.unique(img))} grey levels", fontsize=9)
    axes[1, i].imshow(minmax(img)[crop], cmap="gray", vmin=0, vmax=1)
    axes[1, i].set_title(f"Min-Max normalised\nTenengrad = {tenengrad(minmax(img)):.4f}", fontsize=9)
for ax in axes.flat:
    ax.set_xticks([])
    ax.set_yticks([])
fig.suptitle("Normal stack: frame 028 is nearly black; Min-Max stretches its noise to full range "
             "(256x256 crop, raw row on a shared 0-160 scale)", fontsize=10)
fig.tight_layout()
out = ROOT / "results" / "normal_frame_028.png"
fig.savefig(out, dpi=110)
print(f"wrote {out}")
