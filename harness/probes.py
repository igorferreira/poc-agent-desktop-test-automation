"""Sondagens P2-P8 com a tela falsa (scripts/fake_screen.py), reproduzindo a matriz do G0-VIABILIDADE.md.

Resultado de cada sondagem: funciona / nao / parcial, comparado com o esperado do G0.
Evidencia em evidence/probes-<run_id>/<sondagem>.json. So display isolado (:2).
"""
import importlib.util
import json
import subprocess
import time
from pathlib import Path

from harness import keys, launcher, oracle
from harness.ad import run_ad
from harness.screen import fidelity, normalize, read_l2, read_l3

ROOT = launcher.ROOT
GROUPS = ("P2", "P3", "P4", "P5", "P6", "P7", "P8a", "P8b", "P8c")
ESPERADO = {"P2": "funciona", "P3": "nao", "P4": "nao", "P5": "funciona", "P6": "funciona",
            "P7": "parcial", "P8a": "nao", "P8b": None}  # P8b e variante nova: sem esperado no G0
P8C_MSG = "P8c requer autorização e execução manual (T-029)"
KEY_NAMES = ["ENTER", "TAB", "BACKSPACE", "F3", "F12"]  # nomes que a tela falsa mostra em "ULTIMA:"


def _ad(s, argv, timeout=15.0):
    return run_ad(argv, binary=s.binary, env=s.env, timeout=timeout)


def _terminal_ref(s):
    f = _ad(s, ["find", "--window-id", s.window_id, "--role", "textfield", "--name", "Terminal",
                "--exact", "--first"])
    return ((f.data or {}).get("match") or {}).get("ref_id") if f.ok else None


def _code(e):
    return e.error_code


def expected_fake_screen() -> list[str]:
    """Tela da fake_screen.py sem teclas, calculada do TEXTO dela (deterministica)."""
    spec = importlib.util.spec_from_file_location("fake_screen", ROOT / "scripts" / "fake_screen.py")
    fs = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(fs)
    rows = [[" "] * 80 for _ in range(24)]

    def put(r, c, t):
        for i, ch in enumerate(t[:80 - c]):
            rows[r][c + i] = ch
    put(0, 1, "CADCLI"); put(0, 30, "TELA FALSA DE SONDAGEM"); put(0, 77, "T00")  # noqa: E702
    for i, t in enumerate(fs.TEXTO):
        put(2 + i, 0, t)
    put(20, 0, "ENTRADA: "); put(21, 0, "TECLAS: "); put(22, 0, " F3=SAIR"); put(23, 0, "ULTIMA: ")  # noqa: E702
    return normalize("\n".join("".join(r) for r in rows))


def _res(nome, obtido, **numeros):
    erros = numeros.pop("erros", [])
    esp = ESPERADO[nome]
    return {"sondagem": nome, "obtido": obtido, "esperado": esp,
            "diverge": esp is not None and obtido != esp,
            "erros": sorted({e for e in erros if e}), "numeros": numeros}


def p2(s, ctx):
    e = _ad(s, ["list-windows", "--app", s.app_name])
    ws = [w for w in (e.data if isinstance(e.data, list) else []) if w.get("title") == "CADCLI"]
    foco = None
    err = [_code(e)]
    if len(ws) == 1:
        try:
            keys.focus_guard(s)
            foco = True
        except keys.FocusError:
            foco = False
    ctx["pristine"] = oracle.capture() == expected_fake_screen()
    ok = len(ws) == 1 and ws[0]["id"] == s.window_id and foco
    return _res("P2", "funciona" if ok else "nao", erros=err, janelas_cadcli=len(ws), window_id=s.window_id,
                focus_confirmado=foco, tela_falsa_igual_ao_esperado=ctx["pristine"])


def p3(s, ctx):
    snap = _ad(s, ["snapshot", "--window-id", s.window_id])
    ref = _terminal_ref(s)
    vals, erros = {}, [_code(snap)]
    for prop in ("text", "value"):
        g = _ad(s, ["get", ref, "--property", prop]) if ref else None
        # o ref do find vale so para o snapshot do find; get logo em seguida
        vals[prop] = (g.data or {}).get("value") if g and g.ok else None
        erros.append(_code(g) if g else "SEM_REF")
    achou = "TELA FALSA" in json.dumps(snap.data, ensure_ascii=False) or any(
        isinstance(v, str) and "TELA FALSA" in v for v in vals.values())
    return _res("P3", "funciona" if achou else "nao", erros=erros, snapshot_ok=snap.ok,
                nos_no_snapshot=json.dumps(snap.data).count('"ref_id"'), get_text=vals["text"],
                get_value=vals["value"])


def p4(s, ctx):
    ref = _terminal_ref(s)
    e = _ad(s, ["type", ref, "ZZ"]) if ref else None
    time.sleep(0.3)  # sem condicao possivel: queremos provar que NAO chegou
    chegou = "ZZ" in oracle.line(oracle.capture(), 21)
    if e and e.ok and chegou:
        obtido = "funciona"
    elif e and not e.ok and not chegou:
        obtido = "nao"
    else:
        obtido = "parcial"
    return _res("P4", obtido, erros=[_code(e) if e else "SEM_REF"], codigo=_code(e) if e else None,
                disposicao=e.disposition if e else None, chegou_ao_oraculo=chegou)


def _wait_line(n, pred, t=3.0):
    try:
        oracle.wait_for(lambda sc: pred(oracle.line(sc, n)), timeout=t)
        return True
    except TimeoutError:
        return False


def p5(s, ctx):
    erros, type_ok, key_ok = [], 0, {k: 0 for k in KEY_NAMES}
    for i in range(1, 4):
        try:
            keys.send_text(s, "XYZ")
            type_ok += _wait_line(21, lambda ln, i=i: ln.rstrip().endswith("XYZ" * i) and "XYZ" * i in ln)
        except (RuntimeError, ValueError) as ex:  # FocusError e subclasse
            erros.append(type(ex).__name__)
    logico = {"ENTER": "ENTER", "TAB": "TAB", "BACKSPACE": "BACKSPACE", "F3": "F3", "F12": "F12"}
    for _ in range(3):
        for k in KEY_NAMES:
            try:
                keys.press(s, k)
                key_ok[k] += _wait_line(24, lambda ln, k=k: ln.strip() == f"ULTIMA: {logico[k]}")
            except (RuntimeError, ValueError) as ex:
                erros.append(type(ex).__name__)
    # sem foco: janela estranha no :2 (so Xephyr isolado) toma o foco; press nao deve entregar
    outro = subprocess.Popen(["xterm", "-T", "OUTRO", "-e", "sleep", "60"], env=s.env,
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    perdeu, entregues, cod_sem_foco = False, 0, None
    try:
        def sem_foco():
            e = _ad(s, ["list-windows", "--app", s.app_name])
            return e.ok and any(w.get("id") == s.window_id and w.get("is_focused") is False for w in e.data)
        try:
            launcher._wait(sem_foco, 5, "CADCLI sem foco")
            perdeu = True
        except TimeoutError:
            pass
        if perdeu:
            antes = oracle.line(oracle.capture(), 24)
            e = _ad(s, ["press", "tab", "--window-id", s.window_id])
            cod_sem_foco = _code(e)
            time.sleep(0.3)
            entregues = int(e.ok or oracle.line(oracle.capture(), 24) != antes)
    finally:
        outro.terminate()
        outro.wait(5)
    ok = type_ok == 3 and all(v == 3 for v in key_ok.values()) and perdeu and entregues == 0
    parcial = type_ok or any(key_ok.values())
    return _res("P5", "funciona" if ok else "parcial" if parcial else "nao", erros=erros + [cod_sem_foco],
                type_headed=f"{type_ok}/3", teclas={k: f"{v}/3" for k, v in key_ok.items()},
                teclas_total=f"{sum(key_ok.values())}/15", foco_perdido=perdeu,
                press_sem_foco_entregues=entregues, press_sem_foco_codigo=cod_sem_foco)


def _classe(fids, exatas):
    if fids and all(f["exact"] for f in fids):
        return "funciona"
    return "parcial" if exatas is not None and exatas >= 0.5 else "nao"


def p6(s, ctx):
    keys.focus_guard(s)
    fids, erros = [], []
    for _ in range(3):
        try:
            fids.append(fidelity(read_l2(s), oracle.capture()))
        except RuntimeError as ex:
            erros.append(str(ex)[:160])
    r = min((f["ratio"] for f in fids), default=None)
    return _res("P6", _classe(fids, r) if len(fids) == 3 else "nao", erros=[e.split(":")[1].split()[0] for e in erros if ":" in e],
                leituras=len(fids), exatas=sum(f["exact"] for f in fids), razao_minima=r,
                linhas_iguais=[f["lines_equal"] for f in fids], falhas=erros)


def p7(s, ctx):
    try:
        f = fidelity(read_l3(s), oracle.capture())
    except (RuntimeError, subprocess.CalledProcessError, OSError) as ex:
        return _res("P7", "nao", erros=["L3_FALHOU"], falha=str(ex)[:160])
    return _res("P7", _classe([f], f["ratio"]), ratio=f["ratio"], exata=f["exact"], linhas_iguais=f["lines_equal"])


def p8a(s, ctx):
    apps = _ad(s, ["list-apps"])
    ws = None
    if s.window_id is None:
        try:
            launcher._wait(lambda: launcher.find_window_id(s.env, "xterm"), 5, "janela xterm")
            ws = True
        except TimeoutError:
            ws = False
    lw = _ad(s, ["list-windows", "--app", "xterm"])
    nomes = [a.get("name") for a in (apps.data if isinstance(apps.data, list) else [])]
    return _res("P8a", "funciona" if ws else "nao", erros=[_code(apps), _code(lw)],
                apps_visiveis=nomes, list_windows_xterm=lw.data if lw.ok else None, janela_cadcli_xterm=bool(ws))


def p8b(s, ctx):
    esperado = expected_fake_screen()
    try:
        f = fidelity(read_l2(s), esperado)
    except RuntimeError as ex:
        return _res("P8b", "nao", erros=["L2_FALHOU"], falha=str(ex)[:160])
    obtido = "funciona" if f["exact"] else "parcial" if f["ratio"] >= 0.5 else "nao"
    return _res("P8b", obtido, ratio=f["ratio"], exata=f["exact"], linhas_iguais=f["lines_equal"],
                oraculo="saida esperada da tela falsa (sem tmux)", gerador_validado_no_tmux=ctx.get("pristine"))


def run(selecionadas, evid=ROOT / "evidence") -> int:
    ids = [i for i in GROUPS if i in selecionadas]
    if oracle.session_alive():
        raise SystemExit("sessao tmux -L cadcli ja existe; rode `python3 -m harness env down` antes")
    out = Path(evid) / f"probes-{time.strftime('%Y%m%d-%H%M%S')}"
    out.mkdir(parents=True)
    resultados, ctx = [], {}

    def roda(fn, s, nome):
        try:
            r = fn(s, ctx)
        except Exception as ex:  # uma sondagem quebrada nao derruba as demais
            r = _res(nome, "nao", erros=[type(ex).__name__], falha=str(ex)[:200])
            r["obtido"] = "erro"; r["diverge"] = True  # noqa: E702
        (out / f"{nome}.json").write_text(json.dumps(r, indent=2, ensure_ascii=False), encoding="utf-8")
        resultados.append(r)

    def sessao(nomes, **kw):
        if not nomes:
            return
        try:
            s = launcher.env_up(**kw)
            for n in nomes:
                roda(FUNCS[n], s, n)
        finally:
            launcher.env_down()

    sessao([i for i in ids if i in ("P2", "P3", "P4", "P5", "P6", "P7")])
    sessao([i for i in ids if i == "P8a"], terminal="xterm", wait_window=False, timeout=6)
    sessao([i for i in ids if i == "P8b"], direct=True)
    if "P8c" in ids:
        print(P8C_MSG)
    print(f"{'sondagem':9}{'obtido':10}{'esperado G0':13}resultado")
    for r in resultados:
        print(f"{r['sondagem']:9}{r['obtido']:10}{str(r['esperado'] or '(novo)'):13}"
              f"{'DIVERGE' if r['diverge'] else 'ok'}")
    print("->", out)
    return 1 if any(r["diverge"] for r in resultados) else 0


FUNCS = {"P2": p2, "P3": p3, "P4": p4, "P5": p5, "P6": p6, "P7": p7, "P8a": p8a, "P8b": p8b}


def expandir(args) -> set:
    """['P2','P8'] -> {'P2','P8a','P8b','P8c'}; vazio = todas."""
    if not args:
        return set(GROUPS)
    sel = set()
    for a in args:
        a = a[0].upper() + a[1:].lower()
        sel |= {g for g in GROUPS if g == a or (a == "P8" and g.startswith("P8"))}
    if not sel:
        raise SystemExit(f"sondagem desconhecida: {args}; validas: P2..P8, P8a, P8b, P8c")
    return sel
