import json
import math

import pytest

from fruitfly_vision import CHANNELS
from fruitfly_vision.packets import (
    PacketError,
    SensoryPacket,
    format_summary,
    read_jsonl,
    summarise,
    write_jsonl,
)


def packet(**overrides):
    channels = {name: 0.0 for name in CHANNELS}
    channels.update(overrides.pop("channels", {}))
    data = {"frame": 0, "t_ms": 0.0, "source": "test", "channels": channels}
    data.update(overrides)
    return SensoryPacket(**data)


def test_roundtrip(tmp_path):
    packets = [packet(frame=i, t_ms=i * 33.3) for i in range(5)]
    path = write_jsonl(tmp_path / "s.jsonl", packets)
    back = read_jsonl(path)
    assert [p.frame for p in back] == [0, 1, 2, 3, 4]
    assert back[1].to_dict()["channels"] == packets[1].to_dict()["channels"]


def test_rejects_unknown_channel():
    with pytest.raises(PacketError):
        packet(channels={"scent": 1.0})


def test_rejects_missing_channel():
    channels = {name: 0.0 for name in CHANNELS if name != "centroid_y"}
    with pytest.raises(PacketError):
        SensoryPacket(frame=0, t_ms=0.0, source="t", channels=channels)


def test_rejects_bool_and_nonfinite():
    with pytest.raises(PacketError):
        packet(channels={"left_motion": True})
    with pytest.raises(PacketError):
        packet(channels={"left_motion": math.inf})


def test_rejects_bad_version_and_frame():
    with pytest.raises(PacketError):
        packet(spec_version="9.9")
    with pytest.raises(PacketError):
        packet(frame=-1)
    with pytest.raises(PacketError):
        packet(frame=True)


def test_read_jsonl_reports_line_numbers(tmp_path):
    path = tmp_path / "bad.jsonl"
    path.write_text('{"frame": 0}\n', encoding="utf-8")
    with pytest.raises(PacketError) as exc:
        read_jsonl(path)
    assert "line 1" in str(exc.value)
    assert "missing" in str(exc.value)


def test_read_jsonl_missing_file(tmp_path):
    with pytest.raises(PacketError):
        read_jsonl(tmp_path / "nope.jsonl")


def test_summarise_and_format():
    packets = [packet(frame=i, t_ms=i * 33.0, channels={"left_motion": float(i)}) for i in range(10)]
    stats = summarise(packets)
    assert stats["left_motion"]["max"] == 9.0
    assert stats["_meta"]["packets"] == 10.0
    text = format_summary("s.jsonl", stats)
    assert "left_motion" in text and "10 packets" in text


def test_summarise_empty():
    with pytest.raises(PacketError):
        summarise([])


def test_packet_dict_is_json_serialisable():
    data = packet(channels={"coverage": 0.123456789}).to_dict()
    assert json.loads(json.dumps(data))["channels"]["coverage"] == 0.123457
