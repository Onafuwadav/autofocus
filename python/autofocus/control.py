"""Two-stage hill-climbing autofocus, as proposed in Chapter 6 of the dissertation.

The loop is: capture a frame, score it, step the axis in the direction that
increases the score, repeat. A stepper/lead-screw axis makes large initial
corrections; a piezo objective positioner does fine search and then tracks
drift during a scan. When the piezo nears the end of its travel, the stepper
takes up the offset so the piezo can return to the middle of its range.

The controller only talks to a ``Stage`` object, so the same code drives the
simulator in ``demo/simulate_hill_climb.py`` and the serial hardware link in
``demo/hardware_loop.py``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Protocol

import numpy as np

from .metrics import tenengrad
from .normalise import minmax


class Stage(Protocol):
    """What the controller needs from the hardware (all distances in micrometres)."""

    fine_range: tuple[float, float]

    def move_coarse(self, delta_um: float) -> None: ...
    def set_fine(self, position_um: float) -> None: ...
    def get_fine(self) -> float: ...
    def capture(self) -> np.ndarray: ...


def default_score(img: np.ndarray) -> float:
    """The metric selected in the dissertation: Tenengrad on a Min-Max normalised frame."""
    return tenengrad(minmax(img))


@dataclass
class ClimbSettings:
    coarse_step: float = 20.0      # first stepper step (um)
    coarse_min_step: float = 2.5   # stop coarse search below this step
    fine_step: float = 2.0         # first piezo step (um)
    fine_min_step: float = 0.1     # stop fine search below this step
    track_dither: float = 1.0      # probe distance either side when tracking (um)
    offload_margin: float = 0.2    # re-centre piezo when within this fraction of a range end
    max_iter: int = 60


@dataclass
class Trace:
    """Every (axis, position, score) the controller visited, for plotting."""

    events: list[tuple[str, float, float]] = field(default_factory=list)

    def log(self, axis: str, position: float, score: float) -> None:
        self.events.append((axis, position, score))


def hill_climb(score_at: Callable[[float], float], start: float, step: float, min_step: float,
               lo: float = -np.inf, hi: float = np.inf, max_iter: int = 60) -> tuple[float, float]:
    """1-D hill climb with step halving.

    Keep stepping while the score improves; on a worse score, reverse direction
    and halve the step. Stops when the step falls below ``min_step``. Returns
    ``(best_position, best_score)``. ``score_at`` is responsible for moving the
    axis and capturing a frame.
    """
    pos, best = start, score_at(start)
    direction = 1.0
    for _ in range(max_iter):
        if step < min_step:
            break
        cand = float(np.clip(pos + direction * step, lo, hi))
        if cand == pos:
            direction, step = -direction, step / 2
            continue
        s = score_at(cand)
        if s > best:
            pos, best = cand, s
        else:
            direction, step = -direction, step / 2
    score_at(pos)  # leave the axis at the best position
    return pos, best


class AutofocusController:
    def __init__(self, stage: Stage, score: Callable[[np.ndarray], float] = default_score,
                 settings: ClimbSettings | None = None):
        self.stage = stage
        self.score = score
        self.cfg = settings or ClimbSettings()
        self.trace = Trace()
        self._coarse_pos = 0.0  # stepper position relative to where we started

    def _fine_centre(self) -> float:
        lo, hi = self.stage.fine_range
        return (lo + hi) / 2

    def measure(self) -> float:
        return self.score(self.stage.capture())

    def coarse_search(self) -> float:
        """Stepper hill climb with the piezo parked mid-range."""
        self.stage.set_fine(self._fine_centre())

        def score_at(z: float) -> float:
            self.stage.move_coarse(z - self._coarse_pos)
            self._coarse_pos = z
            s = self.measure()
            self.trace.log("coarse", z, s)
            return s

        z, _ = hill_climb(score_at, self._coarse_pos, self.cfg.coarse_step, self.cfg.coarse_min_step,
                          max_iter=self.cfg.max_iter)
        return z

    def fine_search(self) -> float:
        """Piezo hill climb within its travel."""
        lo, hi = self.stage.fine_range

        def score_at(p: float) -> float:
            self.stage.set_fine(p)
            s = self.measure()
            self.trace.log("fine", p, s)
            return s

        p, _ = hill_climb(score_at, self.stage.get_fine(), self.cfg.fine_step, self.cfg.fine_min_step,
                          lo, hi, self.cfg.max_iter)
        return p

    def focus(self) -> None:
        """Full autofocus from an unknown starting point: coarse then fine."""
        self.coarse_search()
        self.fine_search()

    def track_step(self) -> float:
        """One drift-tracking iteration during a scan.

        Probe the piezo ``track_dither`` either side of its current position,
        fit a parabola through the three scores and move to its vertex,
        limited to one dither step. Near focus the score curve is flat, so
        fitting all three points is much less noise-sensitive than jumping to
        the single best probe. Returns the score at the centre probe.
        """
        lo, hi = self.stage.fine_range
        d = self.cfg.track_dither
        p = float(np.clip(self.stage.get_fine(), lo + d, hi - d))
        scores = []
        for x in (p - d, p, p + d):
            self.stage.set_fine(x)
            scores.append(self.measure())
        s_minus, s0, s_plus = scores
        curvature = s_minus - 2 * s0 + s_plus
        if curvature < 0:  # a peak: step to the vertex
            shift = 0.5 * d * (s_minus - s_plus) / curvature
        else:              # no peak in the window: step uphill
            shift = d if s_plus > s_minus else -d
        target = p + float(np.clip(shift, -d, d))
        self.stage.set_fine(target)
        self.trace.log("track", target, s0)
        self._offload_if_needed()
        return s0

    def _offload_if_needed(self) -> None:
        """Move the stepper so the piezo can return towards the centre of its travel."""
        lo, hi = self.stage.fine_range
        p = self.stage.get_fine()
        margin = self.cfg.offload_margin * (hi - lo)
        if lo + margin < p < hi - margin:
            return
        offset = p - self._fine_centre()
        self.stage.move_coarse(offset)
        self._coarse_pos += offset
        self.stage.set_fine(self._fine_centre())
        self.trace.log("offload", self._coarse_pos, self.measure())
