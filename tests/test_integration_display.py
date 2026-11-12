"""Integracao com display real isolado. So roda com CADCLI_INTEGRATION=1."""
import os

import pytest

from harness import oracle
from harness.keys import press, send_text
from harness.launcher import env_down, env_up
from harness.screen import fidelity, read_l2

pytestmark = pytest.mark.skipif(os.environ.get("CADCLI_INTEGRATION") != "1",
                                reason="defina CADCLI_INTEGRATION=1")


def test_texto_teclas_e_leitura_l2():
    s = env_up()
    try:
        send_text(s, "000123")
        press(s, "TAB")
        send_text(s, "AB")
        press(s, "BACKSPACE")
        press(s, "ENTER")
        tela = oracle.wait_for(lambda t: t[21] == "TECLAS: TAB BACKSPACE ENTER", 5)
        assert tela[20] == "ENTRADA: 000123A"
        f = fidelity(read_l2(s), oracle.capture())
        assert f == {"exact": True, "ratio": 1.0, "lines_equal": 24}
    finally:
        env_down()
