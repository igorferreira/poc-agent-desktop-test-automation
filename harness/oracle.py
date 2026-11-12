"""Oraculo minimo (T-042 fara o completo): tela via tmux, independente do agent-desktop."""
import subprocess
import time

from harness.screen import normalize


def capture(socket="cadcli", target="cadcli") -> list[str]:
    """24 linhas normalizadas do pane tmux."""
    out = subprocess.run(["tmux", "-L", socket, "capture-pane", "-p", "-t", target],
                         capture_output=True, text=True, check=True).stdout
    return normalize(out)


def wait_for(predicate, timeout=5.0, interval=0.05, capture_fn=capture):
    """Repete predicate(linhas) ate ser verdadeiro; devolve a tela. TimeoutError com a ultima tela."""
    fim = time.monotonic() + timeout
    while True:
        tela = capture_fn()
        if predicate(tela):
            return tela
        if time.monotonic() >= fim:
            raise TimeoutError("condicao nao atendida; ultima tela:\n" + "\n".join(tela))
        time.sleep(interval)
