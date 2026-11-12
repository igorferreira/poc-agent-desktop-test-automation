import json

from harness import report


def _run(evid, rid, read, passed, exact):
    d = evid / rid
    d.mkdir(parents=True)
    (d / "meta.json").write_text(json.dumps({"run_id": rid, "date": "2026-01-01T00:00:00", "read_strategy": read}))
    steps = [{"fidelity": {"exact": e, "ratio": 1.0 if e else 0.5, "lines_equal": 24}} for e in exact]
    res = [{"passed": p, "steps": steps, "duration_s": 2.0} for p in passed]
    (d / "summary.json").write_text(json.dumps({
        "scenarios": {"C1": {"passed": sum(passed), "reps": len(passed), "results": res}},
        "fidelity": {"reads": 4, "mean_ratio": 0.75, "exact_pct": 50.0}, "error_codes": {"X": 2}}))
    return d


def test_phase_a(tmp_path):
    a = report.load_phase_a(_run(tmp_path, "r1", "l2", [True, True, False, True], [True, False]))
    c = a["sc"]["C1"]
    assert (c["passed"], c["reps"], c["dur"], c["reads"], c["exact"], c["ratio"]) == (3, 4, 2.0, 8, 4, 0.75)
    assert a["codes"] == {"X": 2}


def test_latest_run(tmp_path):
    _run(tmp_path, "old", "l2", [True], [True])
    new = _run(tmp_path, "new", "l2", [True], [True])
    (new / "meta.json").write_text(json.dumps({"date": "2027-01-01", "read_strategy": "l2"}))
    assert report.latest_run(tmp_path, "l2").name == "new"


def test_phase_b_ignora_na(tmp_path):
    (tmp_path / "phase-b-ledger.tsv").write_text(
        "run_id\tcase\tpassed\tsubagent_tokens\ttool_uses\tduration_s\n"
        "B-C1-r1-x\tC1\ttrue\t100\t6\t10\n"
        "B-C1-r2-x\tC1\ttrue\t200\t8\t30\n"
        "B-C1-r3-x\tC1\tfalse\tNA\t10\tNA (interrompido)\n")
    c = report.load_phase_b(tmp_path)["C1"]
    assert (c["passed"], c["total"], c["tokens"], c["calls"], c["dur"]) == (2, 3, 150, 8, 20)
    assert c["n_cost"] == 2


def test_generate(tmp_path):
    l2 = _run(tmp_path, "a", "l2", [True] * 10, [True])
    l3 = _run(tmp_path, "b", "l3", [True] * 10, [False])
    (tmp_path / "phase-b-ledger.tsv").write_text(
        "run_id\tcase\tpassed\tsubagent_tokens\ttool_uses\tduration_s\nB-C1-r1-x\tC1\ttrue\t1\t1\t1\n")
    out = report.generate(l2, l3, evid=tmp_path, out=tmp_path / "R.md")
    assert "VEREDITO PROPOSTO" not in out.read_text() and "Veredito PROPOSTO" in out.read_text()
