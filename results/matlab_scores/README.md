# MATLAB reference scores

Output of `matlab/focus_metric_comparison_original.m` (run in MATLAB R2026a), saved with

```matlab
writematrix(reshape(results.(cond), 41, []), [lower(cond) '.csv'])
```

Each CSV has 41 rows (frames `bottom_000` to `bottom_040`) and 16 columns. Column `n + 4*(m-1)` holds
normalisation `n` and metric `m`, with normalisations ordered Raw, Mean, MinMax, ContrastStretch and metrics
ordered Laplacian, Tenengrad, Brenner, FFT. In NumPy:
`np.loadtxt(f, delimiter=",").reshape(41, 4, 4, order="F")` gives `[frame, norm, metric]`.

`tests/test_dataset.py` checks the Python port against these files.
