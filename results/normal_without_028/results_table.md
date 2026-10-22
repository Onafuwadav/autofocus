# Normal condition with frame 028 excluded

Dataset: `data/Magnification-2(size)`
Excluded frames: `bottom_028.png`

## Best-focus frame

| Metric | Normalisation | Normal |
|---|---|---|
| Laplacian | Raw | 017 |
| Laplacian | Mean | 017 |
| Laplacian | Min-Max | 017 |
| Laplacian | Contrast Stretch | 017 |
| Tenengrad | Raw | 018 |
| Tenengrad | Mean | 018 |
| Tenengrad | Min-Max | 018 |
| Tenengrad | Contrast Stretch | 017 |
| Brenner | Raw | 018 |
| Brenner | Mean | 018 |
| Brenner | Min-Max | 018 |
| Brenner | Contrast Stretch | 017 |
| FFT | Raw | 018 |
| FFT | Mean | 018 |
| FFT | Min-Max | 017 |
| FFT | Contrast Stretch | 017 |

## Mean time per metric call

Measured with the Python port on the machine that generated this file; not comparable with the MATLAB timings in the dissertation.

| Method | Avg. time per image (s) |
|---|---|
| Laplacian | 0.0198 |
| Tenengrad | 0.0338 |
| Brenner | 0.0149 |
| FFT | 0.1500 |

## Full scores

#### Normal

| Metric | Norm. | Best Image | Best Score | Mean |
|---|---|---|---|---|
| Laplacian | Raw | 017 | 6.1270 | 3.4081 |
| Laplacian | Mean | 017 | 0.0531 | 0.0294 |
| Laplacian | Min-Max | 017 | 0.0003 | 0.0001 |
| Laplacian | Contrast Stretch | 017 | 0.0003 | 0.0002 |
| Tenengrad | Raw | 018 | 1110.4562 | 489.1167 |
| Tenengrad | Mean | 018 | 9.6466 | 4.2292 |
| Tenengrad | Min-Max | 018 | 0.0462 | 0.0195 |
| Tenengrad | Contrast Stretch | 017 | 0.0627 | 0.0286 |
| Brenner | Raw | 018 | 44475674.0000 | 19603234.7000 |
| Brenner | Mean | 018 | 386361.9445 | 169587.5666 |
| Brenner | Min-Max | 018 | 1851.2247 | 785.1913 |
| Brenner | Contrast Stretch | 017 | 2488.0471 | 1142.5714 |
| FFT | Raw | 018 | 2891075020.5086 | 1825846814.5972 |
| FFT | Mean | 018 | 269460594.5984 | 169710564.5676 |
| FFT | Min-Max | 017 | 18730622.7058 | 11503366.7294 |
| FFT | Contrast Stretch | 017 | 21867753.8738 | 13971930.0583 |
