import sys

import pytest

from harness.keys import FocusError, focus_guard, press, send_text
from harness.launcher import Session

WID = "w-1"


@pytest.fixture
def sess(tmp_path):
    """Binario falso: registra argv em log; MODE (env) escolhe se a janela fica focada."""
    log = tmp_path / "log.txt"
    script = tmp_path / "fake_ad.py"
    script.write_text(f"#!{sys.executable}\n" + f'''
import json, os, sys
a = sys.argv[1:]
open({str(log)!r}, "a").write(" ".join(a) + "\\n")
mode = os.environ["FAKE_MODE"]
def out(data, ok=True):
    print(json.dumps({{"version": "2.6", "ok": ok, "command": "x", "data": data}}))
if "focus-window" in a:
    if mode == "focus_fail":
        print(json.dumps({{"version": "2.6", "ok": False, "command": "focus-window",
              "error": {{"code": "ACTION_FAILED", "message": "no"}}}})); sys.exit(1)
    out({{}})
elif "list-windows" in a:
    out([{{"id": "w-1", "title": "CADCLI", "is_focused": mode == "ok"}}])
elif "find" in a:
    out({{"match": {{"ref_id": "@s:e9"}}}})
else:
    out({{}})
''')
    script.chmod(0o755)

    def make(mode):
        return Session(window_id=WID, env={"FAKE_MODE": mode}, binary=str(script))
    make.log = log
    return make


def enviados(sess):
    if not sess.log.exists():
        return []
    return [ln for ln in sess.log.read_text().splitlines() if "type" in ln.split() or "press" in ln.split()]


@pytest.mark.parametrize("mode", ["unfocused", "focus_fail"])
def test_sem_foco_nao_envia(sess, mode):
    s = sess(mode)
    with pytest.raises(FocusError):
        press(s, "ENTER")
    with pytest.raises(FocusError):
        send_text(s, "abc")
    assert enviados(sess) == []


def test_guard_ok_e_envio(sess):
    s = sess("ok")
    focus_guard(s)
    sess.log.write_text("")
    press(s, "BACKSPACE")
    send_text(s, "000123")
    linhas = [ln.split()[0] if ln.split()[0] != "--headed" else ln.split()[1] for ln in sess.log.read_text().splitlines()]
    # a guarda (focus-window + list-windows) vem antes de cada envio
    assert linhas == ["focus-window", "list-windows", "press", "focus-window", "list-windows", "find", "type"]
    assert enviados(sess) == [f"press delete --window-id {WID}", "--headed type @s:e9 000123"]


def test_entradas_invalidas_nao_enviam(sess):
    s = sess("ok")
    with pytest.raises(ValueError):
        press(s, "ESC")
    for t in ("", "a\tb", "a\nb"):
        with pytest.raises(ValueError):
            send_text(s, t)
    assert enviados(sess) == []
