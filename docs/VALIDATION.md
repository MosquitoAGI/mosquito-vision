# Validation

Measurements, not claims. Everything below came out of a script in this
repository on synthetic input.

## 1. Coverage growth replaced flow-based expansion

The first approach cue projected the flow onto the vector pointing away from the
frame centre and averaged it. Measured on a blob growing from radius 12 to 26 in
one frame (160x120 input):

| measurement | growing blob | shrinking blob | static blob |
|---|---|---|---|
| mean radial flow | −3.17 | +3.15 | 0.00 |
| covered-area delta (px) | +1680 | −1680 | 0 |

The sign is inverted, and the report is stable: Farneback estimates the flow
from spatial gradients, and at the boundary of a growing object the gradient
points into the object. Flow divergence at the same scale measured 0.00, so it
was not a usable substitute either. `coverage_growth` — the frame-to-frame
change in thresholded area — has the right sign and stays quiet on a static
scene. That is the shipped implementation.

## 2. Preset response table

`python examples/sweep_demo.py --frames 120` (synthetic camera, 320x240 input,
160x120 encoder input):

```text
sweep      mean L    mean R   max grw   min grw  mean cov   mean cx
quiet       0.000     0.000     0.000     0.000    0.0196    -0.043
left        1.401     0.027     0.012    -0.011    0.0196    -0.527
right       0.040     1.401     0.012    -0.011    0.0195     0.472
both        0.556     0.904     0.006    -0.006    0.0193     0.133
loom        0.690     0.761     0.002    -0.002    0.0195     0.005
```

Read it as the sign convention check it is: a blob confined to the left half
produces 52x more left_motion than right_motion, the mirror image holds on the
right preset, and the quiet preset produces exactly zero on both. The `both`
preset is deliberately not symmetric — the blob starts in the centre and the
120-frame window does not contain a whole cycle — which is also why its centroid
mean sits at +0.133.

`loom` shows motion on both halves because the blob sits in the middle and
breathes: growth alone does not move the halves, the radius *change* does. Its
growth column is small (0.002) because the preset's radius range is only
0.6–1.4x of a 22 px blob; the bridge's own camera grows its blob by 70 px over
ten frames to produce a cue worth reacting to.

## 3. Threshold sensitivity

`coverage` uses the midpoint between the frame's min and max intensity rather
than a fixed constant, which makes it independent of exposure but not of
contrast. A frame where nothing exceeds the midpoint (a uniform scene, an
unplugged camera) reports `coverage = 0.0` and zero centroid — checked in
`tests/test_encoder.py::test_first_frame_is_zeroed` and by the `quiet` preset.

The known failure mode is a scene where the brightest object *is* the noise: with
`--noise 30` the threshold tracks the noise and motion readings rise even though
nothing moves. The synthetic source exposes `--noise` so this can be reproduced
on demand; there is no automatic fix for it.

## 4. Test coverage

`pytest -q` runs 45 tests. The encoder tests are the ones worth reading: sign
conventions (left/right/growth), the clip at 8.0 encoder units, the first-frame
zeroing, and the settings validation. The CLI tests run the real capture path
end to end — synthetic source, encoder, packet write, packet read — which caught
three bugs during development (an unknown-argument path for webcam sources, a
missing `--fps` default for the `ascii` subcommand, and a centroid that sat
exactly on the ±0.5 boundary and failed a strict comparison).

## 5. What is not validated

- No real camera has been used. The webcam path is exercised only by
  `VideoSource` opening and closing.
- No real lighting, no motion blur, no rolling shutter.
- The noise floor on real hardware is unknown; the calibration procedure exists
  precisely because it has to be measured per rig.
