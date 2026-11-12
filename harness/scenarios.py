"""Cenarios C1-C5 (TEST-PLAN secao 4): acao (keys) + espera por condicao no oraculo + verificacao.

O julgamento e so do oraculo (tmux + arquivo). A leitura [L] so alimenta a fidelidade.
"""
import json
import subprocess
import time
from datetime import datetime
from pathlib import Path

from harness import keys, oracle, screen
from harness.launcher import ROOT, Session, env_down, env_up, restart_app

RUN_SH = str(ROOT / "app" / "run.sh")
RESET_SH = str(ROOT / "app" / "reset.sh")
STEP_TIMEOUT = 5.0
READERS = {"l2": screen.read_l2, "l3": screen.read_l3}

T = lambda s: ("t", s)  # noqa: E731  digitar texto
K = lambda k: ("k", k)  # noqa: E731  tecla logica


def L(n):
    return lambda s: oracle.line(s, n)


def has(n, *txt):
    return lambda s: all(t in oracle.line(s, n) for t in txt)


def hasnt(n, txt):
    return lambda s: txt not in oracle.line(s, n)


def allof(*ps):
    return lambda s: all(p(s) for p in ps)


def sid(x):
    return lambda s: oracle.screen_id(s) == x


def msg_empty(s):
    return oracle.message(s) == ""


# (nome, acoes, predicado, [L])
C1 = [("ler-menu", [], allof(has(1, "CADCLI", "CADASTRO DE CLIENTES", "T01"), has(5, "1-INCLUIR"),
                             has(7, "2-CONSULTAR"), has(9, "9-SAIR"), has(12, "OPCAO .:")), True)]
C2 = [("abrir-inclusao", [T("1"), K("ENTER")], sid("T02"), True),
      ("digitar-codigo", [T("000123")], has(4, "000123"), True),
      ("cancelar", [K("F12")], allof(sid("T02"), hasnt(4, "000123")), True),
      ("voltar", [K("F3")], sid("T01"), True),
      ("sair", [T("9"), K("ENTER")], lambda s: not oracle.session_alive(), False)]
C3 = [("abrir-inclusao", [T("1"), K("ENTER")], sid("T02"), False),
      ("codigo", [T("000100"), K("TAB")], has(4, "000100"), False),
      ("nome-backspace", [T("ANA TESTEX"), K("BACKSPACE"), K("TAB")],
       allof(has(5, "ANA TESTE"), hasnt(5, "TESTEX")), True),
      ("cpf", [T("33333333333"), K("TAB")], has(6, "33333333333"), False),
      ("cidade", [T("CURITIBA"), K("TAB")], has(7, "CURITIBA"), False),
      ("uf-confirmar", [T("PR"), K("ENTER")], has(24, "CLIENTE INCLUIDO"), True)]
C4 = [("abrir-consulta", [T("2"), K("ENTER")], sid("T03"), False),
      ("consulta-existente", [T("000001"), K("ENTER")],
       allof(has(6, "MARIA DA SILVA"), has(7, "11111111111"), has(8, "RIO DE JANEIRO"), has(9, "RJ"),
             msg_empty), True),
      ("consulta-inexistente", [T("000999"), K("ENTER")],
       allof(has(24, "CLIENTE NAO ENCONTRADO"), hasnt(6, "MARIA DA SILVA")), True),
      ("voltar", [K("F3")], sid("T01"), False)]
C5 = [("opcao-invalida", [T("5"), K("ENTER")], allof(sid("T01"), has(24, "OPCAO INVALIDA")), True),
      ("abrir-inclusao", [T("1"), K("ENTER")], sid("T02"), False),
      ("codigo-duplicado", [T("000001"), K("TAB"), T("DUPLICADO"), K("TAB"), T("44444444444"), K("TAB"),
                            T("NITEROI"), K("TAB"), T("RJ"), K("ENTER")], has(24, "CODIGO JA CADASTRADO"), True),
      ("cancelar", [K("F12")], allof(msg_empty, hasnt(4, "000001")), False),
      ("uf-invalida", [T("000101"), K("TAB"), T("UF ERRADA"), K("TAB"), T("55555555555"), K("TAB"),
                       T("RECIFE"), K("TAB"), T("XX"), K("ENTER")], has(24, "UF INVALIDA"), True)]

SCENARIOS = {"C1": C1, "C2": C2, "C3": C3, "C4": C4, "C5": C5}


def final_state(cid: str) -> tuple[bool, str]:
    """Estado final esperado (TEST-PLAN secao 4). Usado pelo harness e por `verify`."""
    if cid == "C2":
        return (not oracle.session_alive() and oracle.data_equals_seed(),
                "app encerrado e dados iguais ao seed")
    try:
        tela = oracle.capture()
    except subprocess.CalledProcessError:
        return False, "sessao tmux inexistente"
    want = {"C1": "T01", "C3": "T02", "C4": "T01", "C5": "T02"}[cid]
    if oracle.screen_id(tela) != want:
        return False, f"tela final {oracle.screen_id(tela)}, esperado {want}"
    if cid == "C3":
        d = oracle.read_data()
        ok = (len(d) == 3 and d[:2] == oracle.read_data(oracle.SEED)
              and d[2] == oracle.record_line("000100", "ANA TESTE", "33333333333", "CURITIBA", "PR"))
        return ok, "dados: seed + 000100 ANA TESTE" if ok else f"dados inesperados: {d}"
    ok = oracle.data_equals_seed()
    return ok, "dados iguais ao seed" if ok else "dados diferem do seed"


class StepFail(Exception):
    pass


def ensure_app(session: Session, app_cmd=RUN_SH) -> Session:
    """reset.sh + app mostrando T01. Sessao morta (C2) => recria pane, janela e display."""
    subprocess.run([RESET_SH], check=True, capture_output=True)
    if oracle.session_alive():
        restart_app(session, app_cmd)
    else:
        env_down()
        new = env_up(terminal=session.app_name, app_cmd=app_cmd)
        session = Session(window_id=new.window_id, env=new.env, app_name=new.app_name,
                          binary=session.binary, trace=session.trace)
    oracle.wait_for(lambda s: oracle.screen_id(s) == "T01", timeout=15)
    return session


def run_rep(session, cid, rep, out: Path, read="l2", timeout=STEP_TIMEOUT) -> dict:
    """Uma repeticao. Devolve {passed, failed_step, error, duration_s, steps:[...]}."""
    (out / "screens").mkdir(parents=True, exist_ok=True)
    t0 = time.monotonic()
    res = {"passed": False, "failed_step": None, "error": None, "steps": []}
    trace = session.trace
    try:
        for i, (name, acoes, pred, do_read) in enumerate(SCENARIOS[cid], 1):
            trace.update(scenario=cid, rep=rep, step=i)
            ts = time.monotonic()
            for kind, v in acoes:
                (keys.send_text if kind == "t" else keys.press)(session, v)
            try:
                tela = oracle.wait_for(pred, timeout=timeout)
            except TimeoutError as e:
                res.update(failed_step=i, error=str(e))
                _save(out, cid, rep, i, "oracle", oracle.capture() if oracle.session_alive() else [])
                return res
            info = {"step": i, "name": name, "ok": True}
            if do_read:
                info["fidelity"] = _read_step(session, read, out, cid, rep, i, tela)
            info["duration_s"] = round(time.monotonic() - ts, 3)
            res["steps"].append(info)
        ok, why = final_state(cid)
        res["passed"] = ok
        if not ok:
            res.update(failed_step="final", error=why)
    except Exception as e:  # FocusError, falha de envio, etc.: repeticao falha, harness segue
        res.update(failed_step=res["failed_step"] or "erro", error=f"{type(e).__name__}: {e}")
    finally:
        res["duration_s"] = round(time.monotonic() - t0, 3)
    return res


def _save(out, cid, rep, i, kind, lines):
    (out / "screens" / f"{cid}-{rep}-{i}.{kind}.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")


def _read_step(session, read, out, cid, rep, i, tela):
    """Le pela estrategia e compara com o tmux. Falha de leitura nao afeta o julgamento."""
    try:
        lido = READERS[read](session)
    except Exception as e:
        return {"error": f"{type(e).__name__}: {e}"}
    orac = oracle.capture()
    _save(out, cid, rep, i, "read", lido)
    _save(out, cid, rep, i, "oracle", orac)
    return screen.fidelity(lido, orac)


def _version(binary="agent-desktop"):
    try:
        return subprocess.run([binary, "--version"], capture_output=True, text=True, timeout=15).stdout.strip()
    except (OSError, subprocess.TimeoutExpired):
        return None


def run_all(session, cids, reps, read="l2", timeout=STEP_TIMEOUT, evidence_root=None, terminal=None) -> Path:
    """Roda cenarios x repeticoes, grava meta.json, steps.jsonl e summary.json. Devolve a pasta."""
    root = Path(evidence_root) if evidence_root else ROOT / "evidence"
    run_id = datetime.now().strftime("%Y%m%d-%H%M%S")
    out = root / run_id
    (out / "screens").mkdir(parents=True)
    session.trace.update(steps_path=str(out / "steps.jsonl"))
    (out / "meta.json").write_text(json.dumps({
        "run_id": run_id, "date": datetime.now().astimezone().isoformat(), "agent_desktop": _version(session.binary),
        "terminal": terminal or session.app_name, "display": session.env.get("DISPLAY"), "read_strategy": read,
        "input_strategy": "I2", "step_timeout_s": timeout, "scenarios": cids, "reps": reps}, indent=2) + "\n")
    results = {c: [] for c in cids}
    for cid in cids:
        for rep in range(1, reps + 1):
            session = ensure_app(session)
            session.trace.update(scenario=cid, rep=rep, step=0)
            results[cid].append(run_rep(session, cid, rep, out, read, timeout))
    (out / "summary.json").write_text(json.dumps(summarize(results, out), indent=2, ensure_ascii=False) + "\n")
    return out


def summarize(results, out: Path) -> dict:
    ratios, exact, n = [], 0, 0
    for reps in results.values():
        for r in reps:
            for s in r["steps"]:
                f = s.get("fidelity")
                if f and "ratio" in f:
                    ratios.append(f["ratio"])
                    exact += f["exact"]
                    n += 1
    codes: dict = {}
    sp = out / "steps.jsonl"
    if sp.exists():
        for ln in sp.read_text().splitlines():
            c = json.loads(ln).get("error_code")
            if c:
                codes[c] = codes.get(c, 0) + 1
    return {"scenarios": {c: {"passed": sum(r["passed"] for r in rs), "reps": len(rs), "results": rs}
                          for c, rs in results.items()},
            "fidelity": {"reads": n, "mean_ratio": sum(ratios) / n if n else None,
                         "exact_pct": 100 * exact / n if n else None},
            "error_codes": codes}
