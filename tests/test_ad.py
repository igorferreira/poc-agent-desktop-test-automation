import json
import sys

import pytest

from harness.ad import build_env, load_display_env, retry_safe, run_ad


@pytest.fixture
def fake(tmp_path):
    """Binario falso: o 1o argumento escolhe o comportamento."""
    script = tmp_path / "fake_ad.py"
    script.write_text(f"#!{sys.executable}\n" + '''
import json, sys, time
m = sys.argv[1]
if m == "ok":
    print(json.dumps({"version": "2.6", "ok": True, "command": "press", "data": {"x": 1}}))
elif m.startswith("err:"):
    _, dl, rt = m.split(":")
    print(json.dumps({"version": "2.6", "ok": False, "command": "press", "error": {
        "code": "ACTION_FAILED", "message": "boom", "disposition": {"delivery": dl, "retry": rt}}}))
    sys.exit(1)
elif m == "text":
    print("nao e json")
elif m == "badjson":
    print('{"ok": tru')
elif m == "sleep":
    time.sleep(5)
''')
    script.chmod(0o755)
    return str(script)


def test_sucesso(fake):
    e = run_ad(["ok"], binary=fake)
    assert e.ok and e.data == {"x": 1} and e.version == "2.6" and e.command == "press"
    assert e.returncode == 0 and e.argv == (fake, "ok") and e.duration_ms >= 0
    assert not retry_safe(e)
    with pytest.raises(AttributeError):
        e.ok = False


def test_erro_seguro_e_nao_seguro(fake):
    s = run_ad(["err:not_delivered:safe"], binary=fake)
    assert not s.ok and s.error_code == "ACTION_FAILED" and s.returncode == 1
    assert s.disposition == {"delivery": "not_delivered", "retry": "safe"}
    assert retry_safe(s)
    u = run_ad(["err:delivered_unverified:unsafe"], binary=fake)
    assert not retry_safe(u)
    # retry=safe com delivery diferente de not_delivered tambem nao vale
    assert not retry_safe(run_ad(["err:delivered_unverified:safe"], binary=fake))


@pytest.mark.parametrize("modo", ["text", "badjson"])
def test_saida_invalida(fake, modo):
    e = run_ad([modo], binary=fake)
    assert not e.ok and e.error_code == "HARNESS_BAD_ENVELOPE" and not retry_safe(e)


def test_timeout(fake):
    e = run_ad(["sleep"], binary=fake, timeout=0.3)
    assert not e.ok and e.error_code == "HARNESS_TIMEOUT" and e.returncode is None


def test_binario_inexistente(tmp_path):
    assert run_ad([], binary=str(tmp_path / "nope")).error_code == "HARNESS_SPAWN_FAILED"


def test_steps_jsonl(fake, tmp_path):
    p = tmp_path / "steps.jsonl"
    run_ad(["ok"], binary=fake, steps_path=p, scenario="C1", rep=2, step="s1")
    run_ad(["text"], binary=fake, steps_path=p, scenario="C1", rep=2, step="s2")
    a, b = [json.loads(x) for x in p.read_text().splitlines()]
    assert set(a) == {"ts", "scenario", "rep", "step", "argv", "ok", "error_code", "duration_ms"}
    assert (a["scenario"], a["rep"], a["step"], a["ok"], a["argv"][1:]) == ("C1", 2, "s1", True, ["ok"])
    assert b["ok"] is False and b["error_code"] == "HARNESS_BAD_ENVELOPE"


def test_guarda_display(tmp_path):
    f = tmp_path / "d.env"
    f.write_text("DISPLAY=:2\nDBUS_SESSION_BUS_ADDRESS=unix:path=/x\n")
    d = load_display_env(f)
    assert d == {"DISPLAY": ":2", "DBUS_SESSION_BUS_ADDRESS": "unix:path=/x"}
    env = build_env(d, base={"A": "1"})
    assert env == {"A": "1", **d}
    with pytest.raises(ValueError, match="allow_real_session"):
        build_env({"DISPLAY": ":0"}, base={})
    with pytest.raises(ValueError):
        build_env({}, base={})
    with pytest.raises(ValueError, match="DBUS"):  # sem D-Bus proprio herdaria o da sessao real
        build_env({"DISPLAY": ":2"}, base={"DBUS_SESSION_BUS_ADDRESS": "unix:path=/real"})
    with pytest.raises(ValueError, match="DBUS"):
        build_env({"DISPLAY": ":2", "DBUS_SESSION_BUS_ADDRESS": "unix:path=/real"},
                  base={"DBUS_SESSION_BUS_ADDRESS": "unix:path=/real"})
    assert "AT_SPI_BUS_ADDRESS" not in build_env(d, base={"AT_SPI_BUS_ADDRESS": "x"})
    assert build_env({"DISPLAY": ":0"}, base={}, allow_real_session=True) == {"DISPLAY": ":0"}
