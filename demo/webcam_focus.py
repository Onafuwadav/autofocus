"""Live focus scores from a webcam.

Shows the camera feed with all four metrics (on the chosen normalisation),
the time each one takes, and a rolling plot of the selected metric. Turn a
lens or move the camera towards and away from something textured to watch
the score peak at focus.

    pip install opencv-python        # the GUI build; the headless build has no imshow
    python demo/webcam_focus.py --camera 0

Keys: q quit | m next metric for the plot | n next normalisation
"""

from __future__ import annotations

import argparse
import sys
import time
from collections import deque
from pathlib import Path

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "python"))

from autofocus import METRICS, NORMALISERS, to_gray  # noqa: E402


def draw_plot(values, width: int, height: int, label: str) -> np.ndarray:
    panel = np.full((height, width, 3), 30, np.uint8)
    if len(values) > 1:
        v = np.asarray(values)
        lo, hi = v.min(), v.max()
        span = hi - lo if hi > lo else 1.0
        xs = np.linspace(0, width - 1, len(v)).astype(int)
        ys = (height - 10 - (v - lo) / span * (height - 20)).astype(int)
        cv2.polylines(panel, [np.stack([xs, ys], 1)], False, (80, 220, 80), 2)
        peak = int(np.argmax(v))
        cv2.circle(panel, (int(xs[peak]), int(ys[peak])), 5, (0, 200, 255), -1)
    cv2.putText(panel, label, (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (220, 220, 220), 1)
    return panel


def main(argv=None) -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--camera", type=int, default=0)
    p.add_argument("--roi", type=int, default=400, help="side of the centre square that is scored (px)")
    p.add_argument("--history", type=int, default=200)
    args = p.parse_args(argv)

    cam = cv2.VideoCapture(args.camera)
    if not cam.isOpened():
        sys.exit(f"cannot open camera {args.camera}")

    metric_names, norm_names = list(METRICS), list(NORMALISERS)
    mi, ni = 1, 2  # Tenengrad on Min-Max, the dissertation's choice
    history = deque(maxlen=args.history)

    while True:
        ok, frame = cam.read()
        if not ok:
            break
        h, w = frame.shape[:2]
        r = min(args.roi, h, w)
        y, x = (h - r) // 2, (w - r) // 2
        gray = to_gray(cv2.cvtColor(frame[y : y + r, x : x + r], cv2.COLOR_BGR2RGB))
        img = NORMALISERS[norm_names[ni]](gray)

        lines = []
        for name in metric_names:
            t0 = time.perf_counter()
            s = METRICS[name](img)
            ms = (time.perf_counter() - t0) * 1000
            if name == metric_names[mi]:
                history.append(s)
            marker = ">" if name == metric_names[mi] else " "
            lines.append(f"{marker} {name:<9} {s:12.5g}  {ms:5.1f} ms")

        cv2.rectangle(frame, (x, y), (x + r, y + r), (0, 200, 255), 1)
        cv2.rectangle(frame, (0, 0), (360, 30 + 22 * len(lines)), (0, 0, 0), -1)
        cv2.putText(frame, f"normalisation: {norm_names[ni]}", (8, 20),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1)
        for i, text in enumerate(lines):
            cv2.putText(frame, text, (8, 44 + 22 * i), cv2.FONT_HERSHEY_PLAIN, 1.1, (255, 255, 255), 1)
        plot = draw_plot(history, w, 150, f"{metric_names[mi]} ({norm_names[ni]}), orange = peak so far")
        cv2.imshow("autofocus - focus score", np.vstack([frame, plot]))

        key = cv2.waitKey(1) & 0xFF
        if key == ord("q"):
            break
        if key == ord("m"):
            mi = (mi + 1) % len(metric_names)
            history.clear()
        if key == ord("n"):
            ni = (ni + 1) % len(norm_names)
            history.clear()

    cam.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
