# Focus metric comparison (Python port)

Dataset: `data/Magnification-2(size)`

## Best-focus frame

| Metric | Normalisation | Bright | Normal | Dim |
|---|---|---|---|---|
| Laplacian | Raw | 018 | 017 | 017 |
| Laplacian | Mean | 018 | 028 | 018 |
| Laplacian | Min-Max | 018 | 028 | 014 |
| Laplacian | Contrast Stretch | 018 | 028 | 040 |
| Tenengrad | Raw | 018 | 018 | 018 |
| Tenengrad | Mean | 018 | 028 | 018 |
| Tenengrad | Min-Max | 018 | 018 | 018 |
| Tenengrad | Contrast Stretch | 018 | 017 | 017 |
| Brenner | Raw | 018 | 018 | 018 |
| Brenner | Mean | 018 | 028 | 018 |
| Brenner | Min-Max | 018 | 018 | 018 |
| Brenner | Contrast Stretch | 018 | 028 | 017 |
| FFT | Raw | 018 | 018 | 018 |
| FFT | Mean | 018 | 028 | 018 |
| FFT | Min-Max | 018 | 028 | 016 |
| FFT | Contrast Stretch | 018 | 028 | 018 |

## Mean time per metric call

Measured with the Python port on the machine that generated this file; not comparable with the MATLAB timings in the dissertation.

| Method | Avg. time per image (s) |
|---|---|
| Laplacian | 0.0197 |
| Tenengrad | 0.0334 |
| Brenner | 0.0146 |
| FFT | 0.1446 |

## Full scores

#### Bright

| Metric | Norm. | Best Image | Best Score | Mean |
|---|---|---|---|---|
| Laplacian | Raw | 018 | 39.0830 | 15.2206 |
| Laplacian | Mean | 018 | 0.0468 | 0.0155 |
| Laplacian | Min-Max | 018 | 0.0007 | 0.0003 |
| Laplacian | Contrast Stretch | 018 | 0.0007 | 0.0003 |
| Tenengrad | Raw | 018 | 3618.8324 | 1921.2468 |
| Tenengrad | Mean | 018 | 4.3355 | 1.8992 |
| Tenengrad | Min-Max | 018 | 0.0618 | 0.0326 |
| Tenengrad | Contrast Stretch | 018 | 0.0689 | 0.0370 |
| Brenner | Raw | 018 | 142421174.0000 | 75431219.2683 |
| Brenner | Mean | 018 | 170627.2055 | 74570.0681 |
| Brenner | Min-Max | 018 | 2431.8895 | 1281.2357 |
| Brenner | Contrast Stretch | 018 | 2710.1420 | 1450.5130 |
| FFT | Raw | 018 | 5664518652.6662 | 3882046556.6073 |
| FFT | Mean | 018 | 196064907.7972 | 119421667.1269 |
| FFT | Min-Max | 018 | 23407101.8705 | 15997765.8655 |
| FFT | Contrast Stretch | 018 | 24716840.3069 | 17031795.0164 |

#### Normal

| Metric | Norm. | Best Image | Best Score | Mean |
|---|---|---|---|---|
| Laplacian | Raw | 017 | 6.1270 | 3.3298 |
| Laplacian | Mean | 028 | 1.1639 | 0.0571 |
| Laplacian | Min-Max | 028 | 0.0031 | 0.0002 |
| Laplacian | Contrast Stretch | 028 | 0.0048 | 0.0003 |
| Tenengrad | Raw | 018 | 1110.4562 | 477.2316 |
| Tenengrad | Mean | 028 | 10.7405 | 4.3880 |
| Tenengrad | Min-Max | 018 | 0.0462 | 0.0197 |
| Tenengrad | Contrast Stretch | 017 | 0.0627 | 0.0291 |
| Brenner | Raw | 018 | 44475674.0000 | 19127555.3171 |
| Brenner | Mean | 028 | 589764.7434 | 179835.7904 |
| Brenner | Min-Max | 018 | 1851.2247 | 804.2948 |
| Brenner | Contrast Stretch | 028 | 2537.1171 | 1176.5847 |
| FFT | Raw | 018 | 2891075020.5086 | 1787241042.5805 |
| FFT | Mean | 028 | 589033835.4577 | 179937961.4185 |
| FFT | Min-Max | 028 | 30376270.2391 | 11963681.4492 |
| FFT | Contrast Stretch | 028 | 38019241.1597 | 14558449.8412 |

#### Dim

| Metric | Norm. | Best Image | Best Score | Mean |
|---|---|---|---|---|
| Laplacian | Raw | 017 | 1.9167 | 1.7147 |
| Laplacian | Mean | 018 | 0.2063 | 0.1841 |
| Laplacian | Min-Max | 014 | 0.0012 | 0.0009 |
| Laplacian | Contrast Stretch | 040 | 0.0016 | 0.0014 |
| Tenengrad | Raw | 018 | 82.0732 | 39.1342 |
| Tenengrad | Mean | 018 | 8.9025 | 4.1987 |
| Tenengrad | Min-Max | 018 | 0.0465 | 0.0214 |
| Tenengrad | Contrast Stretch | 017 | 0.0656 | 0.0325 |
| Brenner | Raw | 018 | 3477104.0000 | 1754668.8780 |
| Brenner | Mean | 018 | 377164.2611 | 188310.9866 |
| Brenner | Min-Max | 018 | 1971.1474 | 960.2259 |
| Brenner | Contrast Stretch | 017 | 2751.3446 | 1455.4978 |
| FFT | Raw | 018 | 1079084751.3801 | 811655376.2166 |
| FFT | Mean | 018 | 355395547.1161 | 265964798.1441 |
| FFT | Min-Max | 016 | 25773655.9170 | 18717063.4796 |
| FFT | Contrast Stretch | 018 | 30462554.1826 | 23501464.1147 |
