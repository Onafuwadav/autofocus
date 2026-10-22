"""Simulated two-stage hill-climb autofocus.

A sharp image is blurred as a function of the distance between the stage
position z and a hidden focal plane. The controller from
``autofocus.control`` runs a stepper search, a piezo search, and then tracks
a slow focal drift. The run is saved as a figure.

    python demo/simulate_hill_climb.py                  # uses data/sample/bottom_018.png
    python demo/simulate_hill_climb.py --start-offset 70 --drift 0.03
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "python"))

from autofocus import load_image, minmax  # noqa: E402
from autofocus.control import AutofocusController, ClimbSettings  # noqa: E402
from autofocus.synthetic import make_pattern, render  # noqa: E402


class SimulatedStage:
    """Stepper + piezo axis in front of a synthetic sample.

    Total focus position is ``z = coarse + (fine - fine_centre)``, all in
    micrometres. Stepper moves are quantised to ``coarse_resolution``.

    The default blur of 0.5 px per micrometre was chosen so that, on a crop of
    the real in-focus frame, Tenengrad (Min-Max) falls to about 75% of its
    peak 4 um from focus. That is roughly what the real Normal-condition
    sweep shows (frames 014 and 022 relative to 018).
    """

    def __init__(self, z_focus: float, sharp: np.ndarray | None = None, noise: float = 0.003,
                 fine_range=(0.0, 100.0), coarse_resolution: float = 0.5,
                 sigma0: float = 0.3, sigma_per_um: float = 0.5, seed: int = 0):
        self.z_focus = z_focus
        self.blur = {"sigma0": sigma0, "sigma_per_um": sigma_per_um}
        self.sharp = make_pattern(256) if sharp is None else sharp
        self.noise = noise
        self.fine_range = fine_range
        self.coarse_resolution = coarse_resolution
        self.coarse = 0.0
        self.fine = sum(fine_range) / 2
        self.rng = np.random.default_rng(seed)
        self.frames = 0

    @property
    def z(self) -> float:
        return self.coarse + self.fine - sum(self.fine_range) / 2

    def move_coarse(self, delta_um: float) -> None:
        steps = round(delta_um / self.coarse_resolution)
        self.coarse += steps * self.coarse_resolution

    def set_fine(self, position_um: float) -> None:
        lo, hi = self.fine_range
        self.fine = float(np.clip(position_um, lo, hi))

    def get_fine(self) -> float:
        return self.fine

    def capture(self) -> np.ndarray:
        self.frames += 1
        return render(self.sharp, self.z, self.z_focus, noise=self.noise, rng=self.rng, **self.blur)


def load_sharp(path: Path, size: int = 256) -> np.ndarray:
    img = minmax(load_image(path))
    h, w = img.shape
    y, x = (h - size) // 2, (w - size) // 2
    return img[y : y + size, x : x + size]


def main(argv=None) -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--image", type=Path, default=ROOT / "data" / "sample" / "bottom_018.png")
    p.add_argument("--start-offset", type=float, default=-45.0, help="true focus minus start position (um)")
    p.add_argument("--drift", type=float, default=0.02, help="focal drift per tracking step (um)")
    p.add_argument("--track-steps", type=int, default=200)
    p.add_argument("--noise", type=float, default=0.003)
    p.add_argument("--out", type=Path, default=ROOT / "results" / "hill_climb_simulation.png")
    p.add_argument("--show", action="store_true")
    args = p.parse_args(argv)

    sharp = load_sharp(args.image) if args.image.exists() else None
    if sharp is None:
        print(f"{args.image} not found, using a synthetic test pattern")
    stage = SimulatedStage(z_focus=args.start_offset, sharp=sharp, noise=args.noise)
    ctrl = AutofocusController(stage, settings=ClimbSettings())

    ctrl.coarse_search()
    after_coarse = (stage.frames, stage.z)
    ctrl.fine_search()
    after_fine = (stage.frames, stage.z)
    print(f"coarse search: {after_coarse[0]} frames, error {after_coarse[1] - stage.z_focus:+.2f} um")
    print(f"fine search:   {after_fine[0] - after_coarse[0]} frames, error {after_fine[1] - stage.z_focus:+.2f} um")

    errors, focus_track, z_track = [], [], []
    for _ in range(args.track_steps):
        stage.z_focus += args.drift
        ctrl.track_step()
        errors.append(stage.z - stage.z_focus)
        focus_track.append(stage.z_focus)
        z_track.append(stage.z)
    errors = np.array(errors)
    print(f"tracking:      {args.track_steps} steps, {args.drift * args.track_steps:.1f} um total drift, "
          f"RMS error {np.sqrt(np.mean(errors ** 2)):.3f} um, max {np.abs(errors).max():.3f} um")

    import matplotlib
    if not args.show:
        matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, (a1, a2) = plt.subplots(1, 2, figsize=(12, 4.5))
    ev = ctrl.trace.events
    colours = {"coarse": "tab:blue", "fine": "tab:orange"}
    for axis in ("coarse", "fine"):
        idx = [i for i, e in enumerate(ev) if e[0] == axis]
        a1.plot(idx, [ev[i][2] for i in idx], "o-", ms=3, color=colours[axis], label=f"{axis} search")
    a1.set_xlabel("Frame")
    a1.set_ylabel("Tenengrad (Min-Max)")
    a1.set_title(f"Search from {-args.start_offset:+.0f} um defocus")
    a1.legend()
    a1.grid(alpha=0.3)

    a2.plot(focus_track, label="true focal plane", color="k", lw=1)
    a2.plot(z_track, label="stage position", color="tab:green", lw=1.5)
    a2.set_xlabel("Tracking step")
    a2.set_ylabel("z (um)")
    a2.set_title(f"Drift tracking, RMS error {np.sqrt(np.mean(errors ** 2)):.2f} um")
    a2.legend()
    a2.grid(alpha=0.3)
    fig.suptitle("Simulated two-stage hill-climb autofocus (synthetic blur vs z)")
    fig.tight_layout()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.out, dpi=120)
    print(f"wrote {args.out}")
    if args.show:
        plt.show()


if __name__ == "__main__":
    main()
