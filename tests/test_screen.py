from harness.screen import fidelity, normalize


def test_normalize_completa_24_e_faz_rstrip():
    r = normalize("ABC   \n  X \n")
    assert len(r) == 24 and r[0] == "ABC" and r[1] == "  X" and set(r[2:]) == {""}


def test_normalize_corta_excesso_e_trata_crlf():
    r = normalize("\n".join(f"L{i}  " for i in range(30)).replace("\n", "\r\n"))
    assert len(r) == 24 and r[0] == "L0" and r[23] == "L23"


def test_normalize_vazio():
    assert normalize("") == [""] * 24


def test_fidelity_exata():
    a = normalize("A\nB")
    assert fidelity(a, list(a)) == {"exact": True, "ratio": 1.0, "lines_equal": 24}


def test_fidelity_parcial():
    f = fidelity(normalize("A\nX"), normalize("A\nB"))
    assert not f["exact"] and f["lines_equal"] == 23 and 0.9 < f["ratio"] < 1.0
