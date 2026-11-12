from pathlib import Path

import pytest

from harness import oracle
from harness.screen import normalize

G = Path(__file__).parent / "golden"


def tela(nome):
    return normalize((G / f"{nome}.txt").read_text())


def test_screen_id():
    assert [oracle.screen_id(tela(n)) for n in ("T01", "T02", "T03")] == ["T01", "T02", "T03"]
    assert oracle.screen_id(normalize("")) is None


def test_message_e_line():
    assert oracle.message(tela("T01_opcao_invalida")) == "OPCAO INVALIDA"
    assert oracle.message(tela("T01")) == ""
    assert "MARIA DA SILVA" in oracle.line(tela("T03_cliente_encontrado"), 6)
    assert oracle.message(tela("T03_cliente_nao_encontrado")) == "CLIENTE NAO ENCONTRADO"
    assert oracle.message(tela("T02_cliente_incluido")) == "CLIENTE INCLUIDO"
    assert oracle.message(tela("T02_codigo_duplicado")) == "CODIGO JA CADASTRADO"
    assert oracle.message(tela("T02_uf_invalida")) == "UF INVALIDA"


def test_line_fora_do_intervalo():
    with pytest.raises(ValueError):
        oracle.line(tela("T01"), 25)


def test_data(tmp_path):
    seed = oracle.SEED
    d = tmp_path / "c.dat"
    d.write_bytes(seed.read_bytes())
    assert oracle.data_equals_seed(d, seed) and len(oracle.read_data(d)) == 2
    assert oracle.data_has_record("000001", "MARIA DA SILVA", "11111111111", "RIO DE JANEIRO", "RJ", d)
    assert not oracle.data_has_record("000100", "ANA TESTE", "33333333333", "CURITIBA", "PR", d)
    d.write_text(d.read_text() + oracle.record_line("000100", "ANA TESTE", "33333333333", "CURITIBA", "PR") + "\n")
    assert not oracle.data_equals_seed(d, seed)
    assert oracle.data_has_record("000100", "ANA TESTE", "33333333333", "CURITIBA", "PR", d)
    assert len(oracle.record_line("000100", "ANA TESTE", "33333333333", "CURITIBA", "PR")) == 69
