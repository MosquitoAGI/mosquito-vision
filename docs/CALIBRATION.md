# Calibration

Two sessions. One measures what "nothing is happening" looks like, the other
measures what a known motion produces.

```bash
# 1. what does this camera see when the scene is still?
fruitfly-vision run --source synthetic --sweep quiet --frames 300 --export quiet.jsonl

# 2. what does a known motion produce?
fruitfly-vision run --source synthetic --sweep right --frames 300 --export right.jsonl

# 3. fit
fruitfly-vision calibrate quiet.jsonl right.jsonl --out calibration.json

# 4. use it (scales and gates every reading)
fruitfly-vision run --source webcam --frames 300 --calibration calibration.json --export live.jsonl
```

## What the two refusals mean

`calibrate` refuses a session with fewer than 30 packets, and refuses a sweep
whose peak motion is at or below the noise floor. Both messages are deliberate:
a calibration fitted to twelve frames of noise, or to a "sweep" where nothing
moved, produces a file that is worse than no calibration at all — the numbers
look authoritative and are meaningless. If you see either message, capture a
longer session; do not lower the constant.

## What the numbers mean

- `noise_floor`: the 95th percentile of absolute motion and growth on the quiet
  session. Everything below three times this value is treated as nothing.
- `motion_gain`: peak sweep motion divided by 3.0 — the number of encoder units
  the bridge expects from a full-speed sweep. A session calibrated this way
  reports the same units for the same physical motion no matter which camera
  produced it.
- `growth_gain`: the same idea for the approach cue.
- `thresholds`: the gates `apply()` uses. `motion` gates the two motion
  channels; `growth` gates the approach cue. Values below the gate are zeroed
  rather than passed through, so a quiet scene reports *zero* instead of a
  drifting small number.

## Worked example

The synthetic quiet preset, 120 frames, no added noise:

```text
sweep      mean L    mean R   max grw   min grw  mean cov   mean cx
quiet       0.000     0.000     0.000     0.000    0.0196    -0.043
left        1.401     0.027     0.012    -0.011    0.0196    -0.527
right       0.040     1.401     0.012    -0.011    0.0195     0.472
```

The quiet session's floor is 0.0 (exact, because the synthetic preset is
deterministic), so `calibrate` floors it to 1e-3 and the resulting gate is
3e-3. On a real camera the floor is never zero — expect somewhere between 0.05
and 0.3 encoder units for a webcam in a lit room, and rerun the quiet capture
when the lighting changes.

## When to recalibrate

- The camera or lens changed.
- The lighting changed enough that the thresholded coverage differs noticeably.
- The scene moved (a different room, a different rig).
