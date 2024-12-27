import numpy as np
import pytest

from fruitfly_vision.config import Settings, SettingsError
from fruitfly_vision.encoder import OpticalEncoder, to_gray
from fruitfly_vision.sources import SyntheticConfig, SyntheticSource


def read_all(source, frames):
    return [source.read() for _ in range(frames)]


def encode_all(frames, settings=None):
    encoder = OpticalEncoder(settings)
    return [encoder.update(frame) for frame in frames]


def test_first_frame_is_zeroed():
    encoder = OpticalEncoder()
    out = encoder.update(np.zeros((120, 160), dtype=np.uint8) + 40)
    assert out["left_motion"] == 0.0
    assert out["right_motion"] == 0.0
    assert out["coverage_growth"] == 0.0


def test_motion_in_the_right_half_reads_right():
    frames = read_all(SyntheticSource(SyntheticConfig(sweep="right", blob_speed=4.0)), 60)
    readings = encode_all(frames)[1:]
    left = np.mean([r["left_motion"] for r in readings])
    right = np.mean([r["right_motion"] for r in readings])
    assert right > left * 2.0


def test_motion_in_the_left_half_reads_left():
    frames = read_all(SyntheticSource(SyntheticConfig(sweep="left", blob_speed=4.0)), 60)
    readings = encode_all(frames)[1:]
    left = np.mean([r["left_motion"] for r in readings])
    right = np.mean([r["right_motion"] for r in readings])
    assert left > right * 2.0


def test_quiet_scene_is_quiet():
    frames = read_all(SyntheticSource(SyntheticConfig(sweep="quiet")), 30)
    readings = encode_all(frames)[1:]
    assert max(r["left_motion"] for r in readings) < 0.05
    assert max(r["right_motion"] for r in readings) < 0.05


def test_growth_sign_follows_area():
    frames = read_all(SyntheticSource(SyntheticConfig(sweep="loom", loom_every=20)), 40)
    growth = [r["coverage_growth"] for r in encode_all(frames)[1:]]
    assert max(growth) > 0.02, "a growing blob must read as positive growth"
    assert min(growth) < -0.02, "a shrinking blob must read as negative growth"


def test_shrinking_blob_reads_negative_growth():
    frames = []
    for radius in range(40, 18, -2):
        frame = np.zeros((120, 160), dtype=np.uint8)
        yy, xx = np.ogrid[:120, :160]
        frame[(xx - 80) ** 2 + (yy - 60) ** 2 <= radius**2] = 220
        frames.append(frame)
    growth = [r["coverage_growth"] for r in encode_all(frames)[1:]]
    assert all(g < 0 for g in growth)


def test_centroid_follows_the_blob():
    frames = read_all(SyntheticSource(SyntheticConfig(sweep="right", blob_speed=4.0)), 40)
    readings = encode_all(frames)
    assert np.mean([r["centroid_x"] for r in readings]) > 0.2
    assert all(abs(r["centroid_y"]) <= 0.5 for r in readings)


def test_motion_is_clipped():
    frames = read_all(SyntheticSource(SyntheticConfig(sweep="both", blob_speed=60.0)), 20)
    readings = encode_all(frames)
    assert max(max(r["left_motion"], r["right_motion"]) for r in readings) <= 8.0


def test_to_gray_accepts_gray_and_colour():
    assert to_gray(np.zeros((4, 4), dtype=np.uint8)).shape == (4, 4)
    assert to_gray(np.zeros((4, 4, 3), dtype=np.uint8)).shape == (4, 4)
    with pytest.raises(ValueError):
        to_gray(np.zeros((4, 4, 7), dtype=np.uint8))


def test_settings_validation():
    with pytest.raises(SettingsError):
        Settings(width=8).validate()
    with pytest.raises(SettingsError):
        Settings(blur=4).validate()
    with pytest.raises(SettingsError):
        Settings(motion_gain=0).validate()
    with pytest.raises(SettingsError):
        Settings.from_dict({"nope": 1})


def test_reset_clears_the_previous_frame():
    frames = read_all(SyntheticSource(SyntheticConfig(sweep="right", blob_speed=4.0)), 10)
    encoder = OpticalEncoder()
    encode_all(frames)
    encoder.reset()
    out = encoder.update(frames[-1])
    assert out["left_motion"] == 0.0
