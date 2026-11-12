"""Oraculo: tela via tmux e arquivo de dados, independente do agent-desktop e do agente.

So verificacoes por posicao (linha n, contem X). Nunca compara a tela inteira: campo numerico vazio
mostra zeros e o repintar com erro troca espaco por `_` (SCREENS secao 8).
"""
import re
import subprocess
import time
from pathlib import Path

from harness.screen import normalize

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "clientes.dat"
SEED = ROOT / "app" / "seed" / "clientes.dat"
EXIT_FILE = ROOT / "bin" / "cadcli.exit"  # gravado por app/run.sh quando o app termina


def capture(socket="cadcli", target="cadcli") -> list[str]:
    """24 linhas normalizadas do pane tmux."""
    out = subprocess.run(["tmux", "-L", socket, "capture-pane", "-p", "-t", target],
                         capture_output=True, text=True, check=True).stdout
    return normalize(out)


def wait_for(predicate, timeout=5.0, interval=0.05, capture_fn=capture):
    """Repete predicate(linhas) ate ser verdadeiro; devolve a tela. TimeoutError com a ultima tela."""
    fim = time.monotonic() + timeout
    while True:
        try:
            tela = capture_fn()
        except subprocess.CalledProcessError:  # sessao ainda nao existe / acabou de morrer
            tela = [""] * 24
        if predicate(tela):
            return tela
        if time.monotonic() >= fim:
            raise TimeoutError("condicao nao atendida; ultima tela:\n" + "\n".join(tela))
        time.sleep(interval)


def line(screen: list[str], n: int) -> str:
    """Linha n (1 a 24) da tela."""
    if not 1 <= n <= 24:
        raise ValueError(f"linha fora de 1..24: {n}")
    return screen[n - 1]


def screen_id(screen: list[str]) -> str | None:
    """T01/T02/T03 lido da linha 1, ou None."""
    m = re.search(r"\bT0[123]\s*$", line(screen, 1))
    return m.group(0).strip() if m else None


def message(screen: list[str]) -> str:
    """Linha de mensagem (24), sem espacos nas pontas."""
    return line(screen, 24).strip()


def session_alive(socket="cadcli", session="cadcli") -> bool:
    return subprocess.run(["tmux", "-L", socket, "has-session", "-t", session],
                          capture_output=True).returncode == 0


def exited_ok() -> bool:
    """True se o app terminou com codigo 0 (saida normal); False se caiu, foi morto ou ainda roda."""
    try:
        return EXIT_FILE.read_text().strip() == "0"
    except OSError:
        return False


def read_data(path=DATA) -> list[str]:
    """Linhas de data/clientes.dat (vazio se o arquivo nao existe)."""
    p = Path(path)
    return p.read_text(encoding="utf-8").splitlines() if p.exists() else []


def data_equals_seed(path=DATA, seed=SEED) -> bool:
    return Path(path).read_bytes() == Path(seed).read_bytes()


def record_line(codigo: str, nome: str, cpf: str, cidade: str, uf: str) -> str:
    """Registro de 69 colunas: 6+30+11+20+2 (SCREENS secao 4)."""
    return f"{codigo:<6}{nome:<30}{cpf:<11}{cidade:<20}{uf:<2}"


def data_has_record(codigo, nome, cpf, cidade, uf, path=DATA) -> bool:
    return record_line(codigo, nome, cpf, cidade, uf) in read_data(path)
