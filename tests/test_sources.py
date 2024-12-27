import numpy as np
import pytest

from fruitfly_vision.sources import SyntheticConfig, SyntheticSource, make_source


def centroid_x(frame):
    ys, xs = np.nonzero(frame > 127)
    return xs.mean() if len(xs) else np.nan


def test_same_seed_same_frames():
    a = SyntheticSource(SyntheticConfig(seed=11, noise=5.0))
    b = SyntheticSource(SyntheticConfig(seed=11, noise=5.0))
    for _ in range(20):
        assert np.array_equal(a.read(), b.read())


def test_different_seed_differs():
    a = SyntheticSource(SyntheticConfig(seed=1, noise=5.0))
    b = SyntheticSource(SyntheticConfig(seed=2, noise=5.0))
    assert not np.array_equal(a.read(), b.read())


def test_quiet_sweep_does_not_move():
    source = SyntheticSource(SyntheticConfig(sweep="quiet"))
    first, second = source.read(), source.read()
    assert np.array_equal(first, second)


def test_right_sweep_stays_in_the_right_half():
    source = SyntheticSource(SyntheticConfig(sweep="right", blob_speed=4.0))
    xs = [centroid_x(source.read()) for _ in range(60)]
    assert min(xs) > 320 * 0.5
    assert max(xs) < 320 * 1.0


def test_left_sweep_stays_in_the_left_half():
    source = SyntheticSource(SyntheticConfig(sweep="left", blob_speed=4.0))
    xs = [centroid_x(source.read()) for _ in range(60)]
    assert max(xs) < 320 * 0.5


def test_loom_sweep_changes_size():
    source = SyntheticSource(SyntheticConfig(sweep="loom", loom_every=20, blob_radius=20))
    areas = [(source.read() > 127).sum() for _ in range(40)]
    assert max(areas) > min(areas) * 1.5


def test_validation_errors():
    with pytest.raises(ValueError):
        SyntheticConfig(sweep="diagonal").validate()
    with pytest.raises(ValueError):
        SyntheticConfig(blob_speed=-1).validate()
    with pytest.raises(ValueError):
        SyntheticConfig(blob_speed=1.0, noise=-1.0).validate()


def test_make_source_rejects_unknown_kind():
    with pytest.raises(SystemExit):
        make_source("lidar")
