"""CLI do harness: python3 -m harness env up|down | run | verify | report."""
import argparse
import json
import sys
from pathlib import Path

from harness import launcher, oracle, scenarios
from harness.ad import build_env, load_display_env

ROOT = launcher.ROOT

CLAIMS = {  # TEST-PLAN secao 6; texto comparado em maiusculas, espacos colapsados
    "C1": {"titulo": "CADASTRO DE CLIENTES", "opcoes": ["INCLUIR", "CONSULTAR", "SAIR"]},
    "C2": {"telas": ["T01", "T02", "T01"]},
    "C3": {"mensagem": "CLIENTE INCLUIDO"},
    "C4": {"nome": "MARIA DA SILVA", "cpf": "11111111111", "cidade": "RIO DE JANEIRO", "uf": "RJ",
           "mensagem": "CLIENTE NAO ENCONTRADO"},
    "C5": {"mensagens": ["OPCAO INVALIDA", "CODIGO JA CADASTRADO", "UF INVALIDA"]},
}


def _n(x):
    return " ".join(str(x).upper().split())


def _dedup(xs):
    return [x for i, x in enumerate(xs) if i == 0 or x != xs[i - 1]]


def check_claims(cid, claims) -> list[str]:
    """Lista de divergencias (vazia = confere). Opcoes de C1: cada esperada aparece em alguma declarada.
    Telas de C2: ignora repeticoes consecutivas (T01, T02, T02, T01 vale)."""
    want, errs = CLAIMS[cid], []
    for k, v in want.items():
        got = claims.get(k)
        if got is None:
            errs.append(f"claim ausente: {k}")
        elif k == "titulo":
            if v not in _n(got):
                errs.append(f"titulo: {got!r}")
        elif k == "opcoes":
            g = [_n(x) for x in got] if isinstance(got, list) else []
            if len(g) != len(v) or not all(any(e in x for x in g) for e in v):
                errs.append(f"opcoes: {got!r}")
        elif k == "telas":
            g = _dedup([_n(x) for x in got]) if isinstance(got, list) else []
            if g != v:
                errs.append(f"telas: {got!r}")
        elif k == "mensagens":
            if not isinstance(got, list) or [_n(x) for x in got] != v:
                errs.append(f"mensagens: {got!r}")
        elif _n(got) != v:
            errs.append(f"{k}: {got!r}, esperado {v!r}")
    return errs


def cmd_verify(a) -> int:
    ok_state, why = scenarios.final_state(a.cenario)
    try:
        r = json.loads(Path(a.result).read_text(encoding="utf-8"))
        claims = r.get("claims") if isinstance(r, dict) else None
        errs = check_claims(a.cenario, claims) if isinstance(claims, dict) else ["claims ausente ou invalido"]
        if isinstance(r, dict) and r.get("case") != a.cenario:
            errs.append(f"case do resultado: {r.get('case')!r}")
    except (OSError, ValueError) as e:
        errs = [f"agent-result ilegivel: {e}"]
    passed = ok_state and not errs
    print(json.dumps({"case": a.cenario, "passed": passed, "state": {"ok": ok_state, "detail": why},
                      "claims": {"ok": not errs, "errors": errs}}, indent=2, ensure_ascii=False))
    return 0 if passed else 1


def attach() -> launcher.Session:
    """Session a partir do ambiente ja no ar (display env + window-id da CADCLI)."""
    env = build_env(load_display_env())
    wid = launcher.find_window_id(env)
    if not wid:
        sys.exit("janela CADCLI nao encontrada; rode `python3 -m harness env up`")
    return launcher.Session(window_id=wid, env=env, trace={})


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="harness")
    sub = p.add_subparsers(dest="cmd", required=True)
    e = sub.add_parser("env").add_subparsers(dest="action", required=True)
    up = e.add_parser("up")
    up.add_argument("--display", choices=["isolated", "real"], default="isolated")
    up.add_argument("--terminal", choices=["mate-terminal", "xterm"], default="mate-terminal")
    e.add_parser("down")
    r = sub.add_parser("run")
    r.add_argument("--scenario", choices=sorted(scenarios.SCENARIOS))
    r.add_argument("--reps", type=int, default=1)
    r.add_argument("--read", choices=["l2", "l3"], default="l2")
    r.add_argument("--timeout", type=float, default=scenarios.STEP_TIMEOUT)
    v = sub.add_parser("verify")
    v.add_argument("cenario", choices=sorted(CLAIMS))
    v.add_argument("--result", required=True)
    rp = sub.add_parser("report")
    rp.add_argument("--phase-a-l2")
    rp.add_argument("--phase-a-l3")
    a = p.parse_args(argv)

    if a.cmd == "env":
        if a.action == "down":
            launcher.env_down()
            return 0
        if a.display != "isolated":
            sys.exit("--display real nao suportado pelo harness (exige autorizacao do Igor)")
        if not (ROOT / "bin" / "cadcli").exists():
            sys.exit("bin/cadcli ausente; rode app/build.sh")
        s = launcher.env_up(terminal=a.terminal, app_cmd=scenarios.RUN_SH)
        print(json.dumps({"window_id": s.window_id, "display": s.env["DISPLAY"], "terminal": s.app_name}))
        return 0
    if a.cmd == "run":
        if a.reps < 1:
            sys.exit("--reps >= 1")
        cids = [a.scenario] if a.scenario else sorted(scenarios.SCENARIOS)
        out = scenarios.run_all(attach(), cids, a.reps, a.read, a.timeout)
        s = json.loads((out / "summary.json").read_text())
        for c, d in s["scenarios"].items():
            print(c, f"{d['passed']}/{d['reps']}", [r["duration_s"] for r in d["results"]])
        print("fidelidade", s["fidelity"], "erros", s["error_codes"], "->", out)
        return 0 if all(d["passed"] == d["reps"] for d in s["scenarios"].values()) else 1
    if a.cmd == "verify":
        return cmd_verify(a)
    from harness import report
    print(report.generate(a.phase_a_l2, a.phase_a_l3))
    return 0


if __name__ == "__main__":
    sys.exit(main())
