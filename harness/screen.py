"""Leitura da tela do CADCLI (L2 area de transferencia, L3 OCR) e fidelidade contra o oraculo."""
import difflib
import os
import subprocess
import tempfile

from harness.ad import run_ad

ROWS = 24


def normalize(text: str) -> list[str]:
    """Exatamente 24 linhas, sem espacos a direita; completa com vazias e descarta o excesso."""
    lines = [ln.rstrip() for ln in text.replace("\r\n", "\n").split("\n")]
    if lines and lines[-1] == "":  # \n final nao e linha
        lines.pop()
    return (lines + [""] * ROWS)[:ROWS]


def fidelity(read: list[str], oracle: list[str]) -> dict:
    """{exact, ratio, lines_equal} entre a leitura e o oraculo (ambos normalizados)."""
    a, b = "\n".join(read), "\n".join(oracle)
    return {"exact": read == oracle,
            "ratio": difflib.SequenceMatcher(None, a, b).ratio(),
            "lines_equal": sum(x == y for x, y in zip(read, oracle))}


def _ad(session, argv, timeout=15.0):
    e = run_ad(argv, binary=session.binary, env=session.env, timeout=timeout, **(getattr(session, "trace", None) or {}))
    if not e.ok:
        raise RuntimeError(f"agent-desktop {' '.join(argv)}: {e.error_code} {e.error_message}")
    return e


def _find_ref(session, role, name):
    """Ref (do snapshot que o find acabou de criar) de `role` com nome exato `name`."""
    e = _ad(session, ["find", "--window-id", session.window_id, "--role", role, "--name", name,
                      "--exact", "--first"])
    ref = ((e.data or {}).get("match") or {}).get("ref_id")
    if not ref:
        raise RuntimeError(f"ref de {role} {name!r} nao encontrada: {e.data}")
    return ref


def read_l2(session) -> list[str]:
    """Editar > Selecionar tudo, Editar > Copiar (clique semantico, sem --headed), clipboard-get.

    Os itens so ficam clicaveis com o menu aberto, e a ref vale so para o snapshot que a criou:
    por isso cada passo e click(Editar) + find(item) + click(item).
    Sobrescreve a area de transferencia: so no display isolado (build_env ja garante :2).
    """
    _ad(session, ["clipboard-clear"])
    for item in ("Selecionar tudo", "Copiar"):
        _ad(session, ["click", _find_ref(session, "menu", "Editar")])
        _ad(session, ["click", _find_ref(session, "menuitem", item)])
    e = _ad(session, ["clipboard-get", "--format", "text"])
    return normalize((e.data or {}).get("text") or "")


def read_l3(session, crop="812x504+12+72") -> list[str]:
    """screenshot da janela + recorte/2x/negativo (ImageMagick) + tesseract --psm 6. Aproximada, nunca exata. crop = geometria do mate-terminal 80x24 (G0)."""
    with tempfile.TemporaryDirectory() as d:
        raw, prep = os.path.join(d, "raw.png"), os.path.join(d, "prep.png")
        _ad(session, ["screenshot", "--window-id", session.window_id, raw])
        cmd = ["convert", raw] + (["-crop", crop, "+repage"] if crop else []) + \
              ["-resize", "200%", "-negate", "-colorspace", "Gray", prep]
        subprocess.run(cmd, check=True, capture_output=True, timeout=30)
        out = subprocess.run(["tesseract", prep, "stdout", "--psm", "6"], check=True,
                             capture_output=True, text=True, timeout=60).stdout
    return normalize(out)
