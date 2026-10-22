"""Command-line entry point.

    autofocus compare data/Magnification-2(size)      # results table + figures
    autofocus score data/sample/bottom_018.png        # score one image
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from .metrics import METRICS
from .normalise import NORMALISERS
from .sweep import CONDITIONS, SweepResult, evaluate_folder, frame_number, load_image

NORM_LABELS = {"Raw": "Raw", "Mean": "Mean", "MinMax": "Min-Max", "ContrastStretch": "Contrast Stretch"}


def summary_table(results: dict[str, SweepResult]) -> str:
    """Markdown version of the dissertation's best-focus summary table."""
    conds = list(results)
    lines = ["| Metric | Normalisation | " + " | ".join(conds) + " |",
             "|---|---|" + "---|" * len(conds)]
    for metric in METRICS:
        for norm in NORMALISERS:
            cells = [frame_number(results[c].best_frame(norm, metric)) for c in conds]
            lines.append(f"| {metric} | {NORM_LABELS[norm]} | " + " | ".join(cells) + " |")
    return "\n".join(lines)


def full_table(name: str, res: SweepResult) -> str:
    """Best frame, best score and mean score for every combination (dissertation Appendix B layout)."""
    lines = [f"#### {name}", "", "| Metric | Norm. | Best Image | Best Score | Mean |", "|---|---|---|---|---|"]
    for m, metric in enumerate(res.metrics):
        for n, norm in enumerate(res.norms):
            col = res.scores[:, n, m]
            k = int(np.argmax(col))
            lines.append(f"| {metric} | {NORM_LABELS[norm]} | {frame_number(res.names[k])} | {col[k]:.4f} | {col.mean():.4f} |")
    return "\n".join(lines)


def timing_table(results: dict[str, SweepResult]) -> str:
    lines = ["| Method | Avg. time per image (s) |", "|---|---|"]
    for metric in METRICS:
        t = np.mean([r.mean_time(metric) for r in results.values()])
        lines.append(f"| {metric} | {t:.4f} |")
    return "\n".join(lines)


def cmd_compare(args) -> None:
    base = Path(args.dataset)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    results = {}
    for cond in args.conditions:
        folder = base / cond
        print(f"scoring {folder} ...", flush=True)
        results[cond] = evaluate_folder(folder, exclude=args.exclude)
        np.savez_compressed(out / f"scores_{cond.lower()}.npz", scores=results[cond].scores,
                            times=results[cond].times, names=np.array(results[cond].names))

    table = summary_table(results)
    print("\nBest-focus frame per combination:\n")
    print(table)
    print("\nMean time per metric call (this machine):\n")
    print(timing_table(results))

    md = [f"# {args.title}", "", f"Dataset: `{base.as_posix()}`"]
    if args.exclude:
        md.append(f"Excluded frames: {', '.join(f'`{e}`' for e in args.exclude)}")
    md += ["", "## Best-focus frame", "", table, "",
           "## Mean time per metric call", "",
           "Measured with the Python port on the machine that generated this file; "
           "not comparable with the MATLAB timings in the dissertation.", "",
           timing_table(results), "", "## Full scores", ""]
    md += [full_table(c, r) + "\n" for c, r in results.items()]
    (out / args.table_name).write_text("\n".join(md), encoding="utf-8")

    if not args.no_plots:
        from .plots import plot_curves
        for cond, res in results.items():
            plot_curves(res, cond, out / f"{cond.lower()}.png")
    print(f"\nwrote {out}")


def cmd_score(args) -> None:
    img = load_image(args.image)
    scores = {f"{norm}/{metric}": METRICS[metric](NORMALISERS[norm](img))
              for norm in NORMALISERS for metric in METRICS}
    print(json.dumps(scores, indent=2))


def main(argv=None) -> None:
    p = argparse.ArgumentParser(prog="autofocus", description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)

    c = sub.add_parser("compare", help="score every normalisation x metric combination over a dataset")
    c.add_argument("dataset", help="folder containing Bright/, Normal/, Dim/ subfolders of PNGs")
    c.add_argument("--conditions", nargs="+", default=list(CONDITIONS))
    c.add_argument("--exclude", nargs="*", default=[], help="frame file names to skip, e.g. bottom_028.png")
    c.add_argument("--out", default="results")
    c.add_argument("--table-name", default="results_table.md")
    c.add_argument("--title", default="Focus metric comparison (Python port)")
    c.add_argument("--no-plots", action="store_true")
    c.set_defaults(func=cmd_compare)

    s = sub.add_parser("score", help="print all 16 scores for one image")
    s.add_argument("image")
    s.set_defaults(func=cmd_score)

    args = p.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
