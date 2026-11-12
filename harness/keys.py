"""Entrada no CADCLI (I2): texto por `type --headed` no no Terminal, teclas por `press --window-id`.

Toda funcao de envio chama focus_guard antes. Sem foco confirmado, levanta FocusError e nada e enviado.
"""
import time

from harness.ad import run_ad

# Nomes logicos -> nomes do agent-desktop (SPEC-TECH 6.3; "delete" e o Backspace).
KEYS = {"ENTER": "return", "TAB": "tab", "BACKSPACE": "delete", "F3": "f3", "F12": "f12"}


class FocusError(RuntimeError):
    """A janela CADCLI nao esta confirmada como focada; nada foi enviado."""


def _run(session, argv, timeout=15.0):
    return run_ad(argv, binary=session.binary, env=session.env, timeout=timeout)


def focus_guard(session, timeout=3.0):
    """focus-window na CADCLI e confirma is_focused em list-windows (condicao, com timeout)."""
    f = _run(session, ["focus-window", "--window-id", session.window_id])
    if not f.ok:
        raise FocusError(f"focus-window falhou: {f.error_code} {f.error_message}")
    fim = time.monotonic() + timeout
    while True:
        e = _run(session, ["list-windows", "--app", session.app_name])
        if e.ok and isinstance(e.data, list) and any(
                w.get("id") == session.window_id and w.get("is_focused") is True for w in e.data):
            return
        if time.monotonic() >= fim:
            raise FocusError(f"janela {session.window_id} nao confirmou foco")
        time.sleep(0.1)


def send_text(session, text):
    """Texto por `--headed type <ref Terminal>`. Sem Tab/nova linha (use press)."""
    if not text or any(ord(c) < 32 or ord(c) == 127 for c in text):
        raise ValueError("texto vazio ou com caractere de controle; use press para TAB/ENTER")
    focus_guard(session)
    f = _run(session, ["find", "--window-id", session.window_id, "--role", "textfield",
                       "--name", "Terminal", "--exact", "--first"])
    ref = ((f.data or {}).get("match") or {}).get("ref_id") if f.ok else None
    if not ref:
        raise RuntimeError(f"no Terminal nao encontrado: {f.error_code} {f.error_message}")
    e = _run(session, ["--headed", "type", ref, text])
    if not e.ok:
        raise RuntimeError(f"type falhou: {e.error_code} {e.error_message}")
    return e


def press(session, key):
    """Tecla logica (ENTER, TAB, BACKSPACE, F3, F12) por `press --window-id`, sem --headed."""
    if key not in KEYS:
        raise ValueError(f"tecla desconhecida: {key!r}; validas: {sorted(KEYS)}")
    focus_guard(session)
    e = _run(session, ["press", KEYS[key], "--window-id", session.window_id])
    if not e.ok:
        raise RuntimeError(f"press {key} falhou: {e.error_code} {e.error_message}")
    return e
