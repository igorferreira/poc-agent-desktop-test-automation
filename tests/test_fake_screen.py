import pathlib
import subprocess
import time

import pytest

RAIZ = pathlib.Path(__file__).resolve().parent.parent
TMUX = ["tmux", "-L", "cadcli"]


def tela():
    out = subprocess.run([str(RAIZ / "scripts/oracle_capture.sh")], capture_output=True, text=True).stdout
    return out.split("\n")[:24]


def envia(*teclas, literal=False):
    subprocess.run(TMUX + ["send-keys", "-t", "cadcli"] + (["-l"] if literal else []) + list(teclas), check=True)


def espera(linha, esperado, timeout=3.0):
    fim = time.monotonic() + timeout
    while time.monotonic() < fim:
        t = tela()
        if t[linha - 1] == esperado:
            return t
        time.sleep(0.02)
    pytest.fail(f"linha {linha}: esperado {esperado!r}, obtido {tela()[linha - 1]!r}")


@pytest.fixture(autouse=True)
def sessao():
    subprocess.run([str(RAIZ / "scripts/fake-screen-up.sh")], check=True)
    fim = time.monotonic() + 3
    while "TELA FALSA DE SONDAGEM" not in tela()[0] and time.monotonic() < fim:
        time.sleep(0.02)
    yield
    subprocess.run([str(RAIZ / "scripts/fake-screen-down.sh")], check=True)


def test_layout():
    t = tela()
    assert len(t) == 24
    assert t[0][1:7] == "CADCLI" and t[0][30:52] == "TELA FALSA DE SONDAGEM" and t[0][77:80] == "T00"
    assert t[22] == " F3=SAIR"


def test_teclas():
    envia("AB1", literal=True)
    espera(21, "ENTRADA: AB1")
    envia("BSpace")
    espera(21, "ENTRADA: AB")
    envia("Enter", "Tab", "F3", "F12")
    espera(22, "TECLAS: BACKSPACE ENTER TAB F3 F12")
    t = espera(24, "ULTIMA: F12")
    assert t[20] == "ENTRADA: AB"
    envia("F3")  # F3 so registra: tela continua viva
    espera(24, "ULTIMA: F3")
