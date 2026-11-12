"""Sobe e derruba o ambiente isolado: tmux (-L cadcli) + Xephyr :2 + mate-terminal CADCLI."""
import shlex
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path

from harness.ad import build_env, load_display_env, run_ad

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
SOCKET, SESSION = "cadcli", "cadcli"
DEFAULT_APP = f"python3 {shlex.quote(str(SCRIPTS / 'fake_screen.py'))}"
TERMINAL_APP = {"mate-terminal": "mate-terminal", "xterm": "xterm"}


@dataclass(frozen=True)
class Session:
    window_id: str
    env: dict
    app_name: str = "mate-terminal"
    binary: str = "agent-desktop"  # troca-se por binario falso nos testes
    trace: dict | None = None  # {"steps_path","scenario","rep","step"}: se presente, run_ad registra em steps.jsonl


def _tmux(*args, check=True):
    return subprocess.run(["tmux", "-L", SOCKET, *args], capture_output=True, text=True, check=check)


def _wait(cond, timeout, what):
    """Sincroniza por condicao: repete cond() ate devolver truthy ou estourar o timeout."""
    fim = time.monotonic() + timeout
    while True:
        v = cond()
        if v:
            return v
        if time.monotonic() >= fim:
            raise TimeoutError(f"timeout de {timeout}s esperando {what}")
        time.sleep(0.1)


def find_window_id(env, app_name="mate-terminal", title="CADCLI"):
    """window-id da janela `title` (list-windows so com --app: nunca lista outros apps)."""
    e = run_ad(["list-windows", "--app", app_name], env=env, timeout=15)
    if not e.ok or not isinstance(e.data, list):
        return None
    ids = [w["id"] for w in e.data if w.get("title") == title]
    return ids[0] if len(ids) == 1 else None


def env_up(terminal="mate-terminal", app_cmd=None, timeout=30.0) -> Session:
    """Sobe tmux + display e devolve Session(window_id, env). Em falha, derruba o que subiu."""
    if terminal not in TERMINAL_APP:
        raise ValueError(f"terminal invalido: {terminal!r}")
    if _tmux("has-session", "-t", SESSION, check=False).returncode == 0:
        raise RuntimeError("sessao tmux -L cadcli ja existe; rode env_down() antes")
    try:
        subprocess.run(
            ["setsid", "tmux", "-L", SOCKET, "-f", "/dev/null", "new-session", "-d", "-s", SESSION,
             "-x", "80", "-y", "24", app_cmd or DEFAULT_APP],
            check=True, capture_output=True, text=True)
        _wait(lambda: _tmux("has-session", "-t", SESSION, check=False).returncode == 0, 10, "sessao tmux")
        _tmux("set", "-g", "status", "off")
        # tamanho fixo: o terminal abre menor que 24 linhas por instantes e a tela falsa (curses) morreria
        _tmux("set", "-g", "window-size", "manual")
        _tmux("resize-window", "-t", SESSION, "-x", "80", "-y", "24")
        subprocess.run([str(SCRIPTS / "display-up.sh"), "--terminal", terminal],
                       check=True, capture_output=True, text=True)
        env = build_env(load_display_env())
        app = TERMINAL_APP[terminal]
        wid = _wait(lambda: find_window_id(env, app), timeout, "janela CADCLI")
        return Session(window_id=wid, env=env, app_name=app)
    except BaseException:
        env_down()
        raise


def env_down():
    """Derruba display (grupo da sessao + Xephyr) e o servidor tmux -L cadcli."""
    subprocess.run([str(SCRIPTS / "display-down.sh")], capture_output=True, text=True)
    _tmux("kill-server", check=False)


def restart_app(session: Session, app_cmd=None, timeout=15.0):
    """Reinicia so o pane (respawn-pane -k); confere que o window-id nao mudou."""
    _tmux("respawn-pane", "-k", "-t", SESSION, app_cmd or DEFAULT_APP)
    wid = _wait(lambda: find_window_id(session.env, session.app_name), timeout, "janela CADCLI")
    if wid != session.window_id:
        raise RuntimeError(f"window-id mudou: {session.window_id} -> {wid}")
    return session
