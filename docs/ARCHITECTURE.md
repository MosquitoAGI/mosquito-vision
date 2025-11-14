# Architecture

One pass, five stages, no state except the previous frame.

```text
frame ──► to_gray ──► resize (160x120) ──► blur (3x3) ──┬─► Farneback flow ─► halves ─► left/right_motion
                                                        ├─► threshold mask ─► coverage, coverage_growth
                                                        └─► threshold mask ─► centroid_x / centroid_y
```

## The channels

| channel | units | how it is computed | what it is not |
|---|---|---|---|
| `left_motion` | encoder units | mean flow magnitude in the left half, scaled by `motion_gain` | not "something moved left" — motion *inside* the left half |
| `right_motion` | encoder units | the same for the right half | not a velocity in m/s |
| `coverage` | fraction of the frame | fraction of pixels above the midpoint between the frame's min and max intensity | not a segmentation |
| `coverage_growth` | encoder units | change in coverage against the previous frame, scaled by `growth_gain`, signed | not distance to the object |
| `centroid_x`, `centroid_y` | −1..1 | centre of mass of the thresholded pixels, relative to the frame centre | not tracking across frames |

Six channels, because that is what the consumer (`fruitfly-brain`) actually
uses. Adding a seventh that nothing reads would just be a number to keep
consistent.

## Everything before the encoder matters

The transform order is fixed in `OpticalEncoder._prepare`: grayscale, then
resize, then blur. Resizing before blurring is what keeps the noise statistics
stable across input resolutions, and the blur is what keeps Farneback from
reporting single-pixel noise as motion. Change the order and every recorded
session becomes incomparable with the new one, which is why it lives in one
function instead of a chain of flags.

## Refused alternatives

**Frame differencing instead of optical flow.** Cheaper (no Farneback), but it
reports an approaching object and a brightening exposure as the same thing. The
version in `encoder.py` keeps a numpy-only fallback for the case where OpenCV is
not installed, and the fallback is documented as the weaker path.

**Flow-based approach cue.** The first version measured radial expansion as the
mean of the flow projected onto the vector pointing away from the frame centre.
On synthetic blobs it had the wrong sign: a growing disc produced a *negative*
projection (Farneback estimates the flow from spatial gradients, and at a growth
boundary the gradient points into the object). Covered-area growth replaced it —
see `docs/VALIDATION.md`, section 1.

**A learned encoder.** Out of scope, and it would make the packets impossible to
reason about on a bench. The whole point of this component is that a human can
read six numbers and know what the camera is looking at.

## Packets

`packets.py` owns the on-disk format: one JSON object per line, `spec_version`
first, channels closed. Same reasoning as the bridge's wire format — a reader
must be able to refuse a format it does not understand rather than misread it.
