import pytest

from fruitfly_vision import CHANNELS
from fruitfly_vision.calibration import (
    MIN_PACKETS,
    Calibration,
    CalibrationError,
    calibrate,
    noise_floor,
)
from fruitfly_vision.packets import SensoryPacket


def make(count, source="test", left=0.0, right=0.0, growth=0.0, jitter=0.0):
    packets = []
    for i in range(count):
        channels = {name: 0.0 for name in CHANNELS}
        wobble = jitter * (1 if i % 2 else -1)
        channels.update(
            left_motion=left + wobble,
            right_motion=right + wobble,
            coverage_growth=growth,
            centroid_x=0.5,
        )
        packets.append(SensoryPacket(frame=i, t_ms=i * 33.0, source=source, channels=channels))
    return packets


def test_short_quiet_session_is_refused():
    with pytest.raises(CalibrationError) as exc:
        calibrate(make(MIN_PACKETS - 1))
    assert "at least" in str(exc.value)


def test_noise_floor_tracks_the_jitter():
    quiet = make(MIN_PACKETS + 10, jitter=0.4)
    floor = noise_floor(quiet)
    assert 0.3 <= floor <= 0.5


def test_calibrate_without_sweep_keeps_unit_gains():
    calibration = calibrate(make(60, jitter=0.05))
    assert calibration.motion_gain == 1.0
    assert calibration.growth_gain == 1.0
    assert calibration.thresholds["motion"] > 0


def test_calibrate_scales_to_the_expected_sweep():
    calibration = calibrate(make(60, jitter=0.05), make(60, left=6.0, right=6.0))
    assert 1.8 < calibration.motion_gain < 2.2
    assert calibration.source == "test"


def test_sweep_without_motion_is_refused():
    with pytest.raises(CalibrationError) as exc:
        calibrate(make(60, jitter=0.05), make(60, left=0.01, right=0.01))
    assert "no motion" in str(exc.value)


def test_apply_gates_below_the_threshold():
    calibration = Calibration(noise_floor=0.1, motion_gain=2.0, growth_gain=2.0,
                              thresholds={"motion": 0.3, "growth": 0.1})
    out = calibration.apply({"left_motion": 0.2, "right_motion": 8.0, "coverage_growth": 4.0,
                             "coverage": 0.1, "centroid_x": 0.0, "centroid_y": 0.0})
    assert out["left_motion"] == 0.0  # scaled 0.1, below the 0.3 gate
    assert out["right_motion"] == 4.0
    assert out["coverage_growth"] == 2.0
    assert out["coverage"] == 0.1


def test_save_load_roundtrip(tmp_path):
    calibration = calibrate(make(60, jitter=0.05), make(60, left=5.0, right=5.0))
    path = calibration.save(tmp_path / "cal.json")
    back = Calibration.load(path)
    assert back.to_dict() == calibration.to_dict()


def test_load_rejects_bad_file(tmp_path):
    path = tmp_path / "cal.json"
    path.write_text('{"spec_version": "1.0"}', encoding="utf-8")
    with pytest.raises(CalibrationError):
        Calibration.load(path)
    with pytest.raises(CalibrationError):
        Calibration.load(tmp_path / "missing.json")
