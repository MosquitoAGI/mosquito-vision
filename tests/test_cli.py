from fruitfly_vision.cli import main
from fruitfly_vision.packets import read_jsonl
from fruitfly_vision.visualize import render_reading, sparkline


def test_run_exports_a_session(tmp_path, capsys):
    out = tmp_path / "session.jsonl"
    code = main(["run", "--source", "synthetic", "--frames", "40", "--export", str(out)])
    assert code == 0
    assert out.exists()
    packets = read_jsonl(out)
    assert len(packets) == 40
    assert "left_motion" in capsys.readouterr().out


def test_summary_reads_a_session(tmp_path, capsys):
    out = tmp_path / "session.jsonl"
    main(["run", "--source", "synthetic", "--frames", "40", "--export", str(out), "--quiet"])
    capsys.readouterr()
    assert main(["summary", str(out)]) == 0
    printed = capsys.readouterr().out
    assert "left_motion" in printed and "packets" in printed


def test_summary_on_a_missing_file(capsys):
    assert main(["summary", "/nonexistent/session.jsonl"]) == 2
    assert "error" in capsys.readouterr().err


def test_calibrate_needs_enough_packets(tmp_path, capsys):
    quiet = tmp_path / "quiet.jsonl"
    main(["run", "--source", "synthetic", "--sweep", "quiet", "--frames", "10",
          "--export", str(quiet), "--quiet"])
    assert main(["calibrate", str(quiet), "--out", str(tmp_path / "cal.json")]) == 2
    assert "at least" in capsys.readouterr().err


def test_calibrate_writes_a_calibration(tmp_path, capsys):
    quiet, sweep = tmp_path / "quiet.jsonl", tmp_path / "sweep.jsonl"
    main(["run", "--source", "synthetic", "--sweep", "quiet", "--frames", "60",
          "--export", str(quiet), "--quiet"])
    main(["run", "--source", "synthetic", "--sweep", "right", "--frames", "60",
          "--export", str(sweep), "--quiet"])
    cal = tmp_path / "cal.json"
    assert main(["calibrate", str(quiet), str(sweep), "--out", str(cal)]) == 0
    assert cal.exists()
    assert "motion_gain" in capsys.readouterr().out


def test_run_with_calibration(tmp_path):
    quiet, sweep = tmp_path / "quiet.jsonl", tmp_path / "sweep.jsonl"
    main(["run", "--source", "synthetic", "--sweep", "quiet", "--frames", "60",
          "--export", str(quiet), "--quiet"])
    main(["run", "--source", "synthetic", "--sweep", "right", "--frames", "60",
          "--export", str(sweep), "--quiet"])
    cal = tmp_path / "cal.json"
    main(["calibrate", str(quiet), str(sweep), "--out", str(cal)])
    out = tmp_path / "calibrated.jsonl"
    code = main(["run", "--source", "synthetic", "--sweep", "right", "--frames", "40",
                 "--calibration", str(cal), "--export", str(out), "--quiet"])
    assert code == 0
    packets = read_jsonl(out)
    assert max(p.channels["right_motion"] for p in packets) > 0.5


def test_ascii_smoke(capsys):
    assert main(["ascii", "--source", "synthetic", "--frames", "20", "--every", "10"]) == 0
    out = capsys.readouterr().out
    assert "centroid_x" in out


def test_sparkline_and_bars():
    line = sparkline([0, 1, 2, 3, 4, 5, 6, 7])
    assert len(line) == 8 and line[0] != line[-1]
    text = render_reading({"left_motion": 2.0, "coverage": 0.25})
    assert "left_motion" in text and "#" in text
