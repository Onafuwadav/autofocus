"""Closed-loop autofocus on real hardware: camera -> score on the PC -> serial -> MCU.

Talks to ``firmware/autofocus_controller`` over USB serial. Two modes:

* ``--mode host``: the PC runs the coarse + fine hill climb from
  ``autofocus.control`` and sends absolute move commands.
* ``--mode mcu``:  the PC only scores frames and sends each score to the
  microcontroller, which runs the fine hill climb itself (``A`` / ``S``
  commands). This is the split described in the dissertation.

After focusing, ``--track`` keeps tracking drift until Ctrl+C.

    pip install -e ".[hardware]"
    python demo/hardware_loop.py --port COM5 --camera 0 --mode host --track

Rebuilt to match the rebuilt firmware; not tested against the original rig.
Check lead screw pitch, microstepping and piezo travel before running.
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "python"))

from autofocus import to_gray  # noqa: E402
from autofocus.control import AutofocusController, ClimbSettings, default_score  # noqa: E402


class SerialStage:
    """``autofocus.control.Stage`` backed by the firmware and an OpenCV camera."""

    def __init__(self, port: str, camera: int, um_per_step: float, piezo_range_um: float = 100.0,
                 settle_s: float = 0.05, flush_frames: int = 2, roi: int = 512):
        import serial  # pyserial

        self.ser = serial.Serial(port, 115200, timeout=5)
        time.sleep(2.0)  # most boards reset when the port opens
        self.ser.reset_input_buffer()
        self.cam = cv2.VideoCapture(camera)
        if not self.cam.isOpened():
            raise RuntimeError(f"cannot open camera {camera}")
        self.um_per_step = um_per_step
        self.fine_range = (0.0, piezo_range_um)
        self.settle_s = settle_s
        self.flush_frames = flush_frames
        self.roi = roi
        self._fine = self._query()[1]

    def _cmd(self, text: str) -> str:
        self.ser.write((text + "\n").encode())
        reply = self.ser.readline().decode().strip()
        if not reply or reply.startswith("ERR"):
            raise RuntimeError(f"{text!r} -> {reply!r}")
        return reply

    def _query(self) -> tuple[int, float]:
        _, steps, nm = self._cmd("?").split()
        return int(steps), int(nm) / 1000

    def move_coarse(self, delta_um: float) -> None:
        steps = round(delta_um / self.um_per_step)
        if steps:
            self._cmd(f"C {steps}")
            time.sleep(self.settle_s)

    def set_fine(self, position_um: float) -> None:
        self._fine = float(self._cmd(f"F {round(position_um * 1000)}").split()[-1]) / 1000
        time.sleep(self.settle_s)

    def get_fine(self) -> float:
        return self._fine

    def capture(self) -> np.ndarray:
        # Drop buffered frames so the image reflects the current position.
        for _ in range(self.flush_frames):
            self.cam.grab()
        ok, frame = self.cam.read()
        if not ok:
            raise RuntimeError("camera read failed")
        gray = to_gray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        h, w = gray.shape
        r = min(self.roi, h, w)
        y, x = (h - r) // 2, (w - r) // 2
        return gray[y : y + r, x : x + r]

    def mcu_fine_climb(self, step_um: float, min_step_um: float, max_frames: int = 100) -> float:
        """Run the fine hill climb on the microcontroller; the PC only supplies scores."""
        self._cmd(f"A {round(step_um * 1000)} {round(min_step_um * 1000)}")
        for _ in range(max_frames):
            reply = self._cmd(f"S {default_score(self.capture()):.6g}")
            kind, _, nm = reply.split()
            self._fine = int(nm) / 1000
            time.sleep(self.settle_s)
            if kind == "DONE":
                return self._fine
        self._cmd("X")
        raise RuntimeError("fine climb did not converge")

    def close(self) -> None:
        self.cam.release()
        self.ser.close()


def main(argv=None) -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--port", required=True, help="serial port, e.g. COM5 or /dev/ttyACM0")
    p.add_argument("--camera", type=int, default=0)
    p.add_argument("--mode", choices=["host", "mcu"], default="host")
    p.add_argument("--um-per-step", type=float, default=0.15625,
                   help="lead screw travel per microstep (default: 0.5 mm pitch, 200 steps/rev, 16x)")
    p.add_argument("--piezo-range", type=float, default=100.0, help="piezo travel in um")
    p.add_argument("--settle", type=float, default=0.05, help="seconds to wait after each move")
    p.add_argument("--skip-coarse", action="store_true")
    p.add_argument("--track", action="store_true", help="keep tracking drift after focusing")
    args = p.parse_args(argv)

    stage = SerialStage(args.port, args.camera, args.um_per_step, args.piezo_range, args.settle)
    cfg = ClimbSettings()
    ctrl = AutofocusController(stage, settings=cfg)
    try:
        t0 = time.perf_counter()
        if not args.skip_coarse:
            ctrl.coarse_search()
            print(f"coarse done, score {ctrl.measure():.4g}")
        if args.mode == "host":
            ctrl.fine_search()
        else:
            stage.mcu_fine_climb(cfg.fine_step, cfg.fine_min_step)
        print(f"focused in {time.perf_counter() - t0:.1f} s, piezo at {stage.get_fine():.2f} um, "
              f"score {ctrl.measure():.4g}")
        while args.track:
            s = ctrl.track_step()
            print(f"\rtracking: piezo {stage.get_fine():7.2f} um  score {s:.4g}   ", end="", flush=True)
    except KeyboardInterrupt:
        print()
    finally:
        stage.close()


if __name__ == "__main__":
    main()
