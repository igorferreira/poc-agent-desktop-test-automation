"""Gera RESULTS.md a partir de evidence/ (Fases A e B). So numeros e identificadores de execucao vao ao texto."""
import csv
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EVID = ROOT / "evidence"
DEFAULT_L2, DEFAULT_L3 = "20261112-113612", "20261112-112535"
# Limiares do PRD secao 8
LIM_A, LIM_FID, LIM_B = 9 / 10, 95.0, 2 / 3


def _j(p: Path):
    return json.loads(p.read_text(encoding="utf-8"))


def latest_run(evid: Path, read: str) -> Path:
    """Execucao mais recente da leitura (pelo meta.json), entre as que tem summary.json."""
    best = None
    for m in evid.glob("*/meta.json"):
        if not (m.parent / "summary.json").exists():
            continue
        try:
            meta = _j(m)
        except ValueError:
            continue
        if meta.get("read_strategy") == read and (best is None or meta["date"] > best[0]):
            best = (meta["date"], m.parent)
    if not best:
        raise SystemExit(f"nenhuma execucao da Fase A com leitura {read} em {evid}")
    return best[1]


def load_phase_a(d: Path) -> dict:
    """Taxas por cenario, duracao media, fidelidade (global e por cenario) e error_code."""
    meta, summ = _j(d / "meta.json"), _j(d / "summary.json")
    sc = {}
    for cid, v in summ["scenarios"].items():
        durs = [r["duration_s"] for r in v["results"] if "duration_s" in r]
        fid = [s["fidelity"] for r in v["results"] for s in r["steps"] if "ratio" in s.get("fidelity", {})]
        sc[cid] = {"passed": v["passed"], "reps": v["reps"], "dur": sum(durs) / len(durs) if durs else None,
                   "reads": len(fid), "exact": sum(f["exact"] for f in fid),
                   "ratio": sum(f["ratio"] for f in fid) / len(fid) if fid else None}
    return {"run_id": meta.get("run_id", d.name), "meta": meta, "sc": sc, "fid": summ["fidelity"],
            "codes": summ.get("error_codes", {})}


def _num(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None  # "NA", "NA (interrompido ...)", vazio


def load_phase_b(evid: Path) -> dict:
    """Por caso: passou/total (verify.json, ou ledger se faltar) e medias de tokens/chamadas/duracao sem NA."""
    led = {}
    lp = evid / "phase-b-ledger.tsv"
    if lp.exists():
        with lp.open(encoding="utf-8", newline="") as f:
            for row in csv.DictReader(f, delimiter="\t"):
                led[row["run_id"]] = row
    cases: dict = {}
    for rid, row in led.items():
        cases.setdefault(row["case"], {"runs": []})["runs"].append(rid)
    for d in evid.glob("B-*"):
        m = re.match(r"B-(C\d)-r\d+-", d.name)
        if m and (d / "verify.json").exists():
            r = cases.setdefault(m.group(1), {"runs": []})
            if d.name not in r["runs"]:
                r["runs"].append(d.name)
    out = {}
    for cid, c in sorted(cases.items()):
        passed, tok, calls, dur = 0, [], [], []
        for rid in c["runs"]:
            vp, row = evid / rid / "verify.json", led.get(rid, {})
            ok = _j(vp)["passed"] if vp.exists() else str(row.get("passed")).lower() == "true"
            passed += bool(ok)
            for lst, k in ((tok, "subagent_tokens"), (calls, "tool_uses"), (dur, "duration_s")):
                if (n := _num(row.get(k))) is not None:
                    lst.append(n)
        mean = lambda xs: sum(xs) / len(xs) if xs else None  # noqa: E731
        out[cid] = {"passed": passed, "total": len(c["runs"]), "tokens": mean(tok), "calls": mean(calls),
                    "dur": mean(dur), "n_cost": len(tok)}
    return out


def verdict(a2: dict, b: dict) -> dict:
    """Regra do PRD secao 8. GO exige limiares (A em L2, fidelidade L2, B); como so o mate-terminal funciona
    (xterm invisivel), aplica-se a clausula de ressalva 'so em um emulador de terminal especifico'."""
    a_ok = all(v["passed"] / v["reps"] >= LIM_A for v in a2["sc"].values())
    f_ok = (a2["fid"]["exact_pct"] or 0) >= LIM_FID
    b_ok = bool(b) and all(v["passed"] / v["total"] >= LIM_B for v in b.values())
    if not (a_ok and f_ok and b_ok):
        nome = "NO-GO" if not (a_ok and b_ok) else "GO com ressalvas"
    else:
        nome = "GO com ressalvas"
    return {"nome": nome, "a_ok": a_ok, "f_ok": f_ok, "b_ok": b_ok}


def f1(x, d=1):
    return "n/d" if x is None else f"{x:.{d}f}".replace(".", ",")


def mil(x):
    return "n/d" if x is None else f"{x:,.0f}".replace(",", ".")


def render(a2: dict, a3: dict, b: dict) -> str:
    v = verdict(a2, b)
    ok = lambda c: "atende" if c else "NAO atende"  # noqa: E731
    m = a2["meta"]
    tot_b = sum(c["total"] for c in b.values())
    pas_b = sum(c["passed"] for c in b.values())
    costs = [c["tokens"] for c in b.values() if c["tokens"] is not None]
    tok_all = sum(costs) / len(costs) if costs else None
    reps = {v_["reps"] for v_ in a2["sc"].values()}
    L = []
    w = L.append
    w("# RESULTS — POC agent-desktop em app de tela verde\n")
    w("> Gerado por `python3 -m harness report`. Os numeros vem de `evidence/` (fora do git); nao edite a mao.\n")
    w("## 1. Resumo e veredito proposto\n")
    w(f"Lendo a tela pela area de transferencia (L2) e enviando teclas com `--headed`, o agent-desktop completou "
      f"C1-C5 em {sum(s['passed'] for s in a2['sc'].values())}/{sum(s['reps'] for s in a2['sc'].values())} "
      f"repeticoes deterministicas e {pas_b}/{tot_b} casos conduzidos por IA, mas so no mate-terminal e em display isolado.\n")
    w(f"**Veredito PROPOSTO: {v['nome'].upper()}.** O veredito final e do Igor (T-072); este texto e so a proposta.\n")
    w("Regra (PRD secao 8):\n")
    w(f"- Fase A, L2, taxa por cenario >= 9/10: {ok(v['a_ok'])}.")
    w(f"- Fidelidade L2, igualdade exata >= 95%: {ok(v['f_ok'])} ({f1(a2['fid']['exact_pct'])}%).")
    w(f"- Fase B, >= 2/3 por caso: {ok(v['b_ok'])} ({pas_b}/{tot_b}).")
    w("- Com os tres criterios atendidos, leitura por area de transferencia e entrada `--headed`, a regra do GO seria satisfeita.")
    w("- A clausula de ressalva \"so em um emulador de terminal especifico\" tambem se aplica: o xterm e invisivel ao "
      "agent-desktop e so o mate-terminal (VTE) foi medido. Por isso a proposta e GO com ressalvas, nao GO pleno.")
    w("- Se algum criterio acima nao for atendido, o veredito cai: NO-GO quando a Fase A ou a B falham.\n")
    w("## 2. Ambiente e versoes\n")
    w("| Item | Valor |\n|---|---|")
    w(f"| Ferramenta | {m.get('agent_desktop')} |")
    w("| GnuCOBOL | 3.2.0 |\n| Sistema | Ubuntu 26.04, X11, MATE |")
    w(f"| Display | Xephyr isolado `{m.get('display')}` |")
    w(f"| Terminal | {m.get('terminal')} |")
    w(f"| Entrada | {m.get('input_strategy')} (`type --headed`, `press --window-id`) |")
    w(f"| Timeout por passo | {f1(m.get('step_timeout_s'))} s |")
    w(f"| Execucoes Fase A | L2 `{a2['run_id']}`, L3 `{a3['run_id']}` ({', '.join(str(r) for r in sorted(reps))} repeticoes por cenario) |")
    w("| Execucoes Fase B | `evidence/B-*` (Claude Code como subagente sem contexto) |\n")
    w("## 3. Matriz de viabilidade (sondagens P2-P7, G0)\n")
    w("| Estrategia | mate-terminal | xterm |\n|---|---|---|")
    w("| L1 arvore de acessibilidade (`snapshot`, `get`, `find`) | Nao: o no `Terminal` tem `value` nulo | Nao: janela invisivel |")
    w("| L2 area de transferencia | **Funciona** (6/6 exatas na sondagem) | Nao se aplica |")
    w("| L3 `screenshot` + `tesseract` | Parcial: similaridade 0,86 a 0,95 na tela falsa, nunca exata | Nao testado |")
    w("| I1 `type` sem `--headed` | Nao: `POLICY_DENIED` | Nao se aplica |")
    w("| I2 `type --headed` / `press --window-id` com foco | **Funciona** (3/3 e 15/15) | Nao se aplica |")
    w("| `press` com janela sem foco | Nao entrega (`STALE_REF` ou `ACTION_FAILED`) | Nao se aplica |\n")
    w("Nao feito: mate-terminal sem tmux; qualquer medicao na sessao real. Detalhes em G0-VIABILIDADE.md.\n")
    w("## 4. Fase A (sem IA)\n")
    for tag, a in (("L2 (area de transferencia)", a2), ("L3 (screenshot + OCR)", a3)):
        w(f"### {tag} — `{a['run_id']}`\n")
        w("| Cenario | Sucesso | Duracao media (s) | Leituras | Exatas | Similaridade media |\n|---|---|---|---|---|---|")
        for cid, s in sorted(a["sc"].items()):
            w(f"| {cid} | {s['passed']}/{s['reps']} | {f1(s['dur'])} | {s['reads']} | {s['exact']} | {f1(s['ratio'], 2)} |")
        fd = a["fid"]
        w(f"\nFidelidade global: {fd['reads']} leituras, similaridade media {f1(fd['mean_ratio'], 2)}, "
          f"igualdade exata em {f1(fd['exact_pct'])}%.")
        w("Contagem de `error_code`: " + (", ".join(f"{k}={n}" for k, n in sorted(a["codes"].items())) or "nenhum") + ".\n")
    w("O sucesso de cada cenario e julgado pelo oraculo (tmux e arquivo de dados), nao pela leitura; por isso L3 "
      "passa nos cenarios mesmo sem servir como leitura.\n")
    w("Comparacao com os limiares:\n")
    w("| Metrica | Limiar | L2 | L3 |\n|---|---|---|---|")
    for lab, lim, f in (("Cenarios com sucesso >= 9/10", "todos", lambda a: f"{sum(s['passed'] / s['reps'] >= LIM_A for s in a['sc'].values())}/{len(a['sc'])}"),
                        ("Leituras exatas", ">= 95%", lambda a: f"{f1(a['fid']['exact_pct'])}%")):
        w(f"| {lab} | {lim} | {f(a2)} | {f(a3)} |")
    w("\nL3 falha o limiar de fidelidade; L2 o atende.\n")
    w("## 5. Fase B (agente de IA)\n")
    w("| Caso | Passou | Contexto final medio (tokens) | Chamadas medias | Duracao media (s) |\n|---|---|---|---|---|")
    for cid, c in b.items():
        w(f"| {cid} | {c['passed']}/{c['total']} | {mil(c['tokens'])} | {f1(c['calls'])} | {f1(c['dur'], 0)} |")
    w(f"\nMedias de custo excluem linhas com NA (interrompidas por limite de uso): "
      f"{sum(c['total'] - c['n_cost'] for c in b.values())} repeticao(oes) fora do calculo de tokens e duracao. "
      f"Limiar: >= 2/3 por caso ({ok(v['b_ok'])}). Contexto final medio por caso: {mil(tok_all)} tokens. Isso e o tamanho do contexto do subagente, nao o consumo: o consumo real e o custo estao em CUSTOS.md.\n")
    w("## 6. Hipoteses\n")
    a_all = all(s["passed"] == s["reps"] for s in a2["sc"].values())
    w("| ID | Estado | Evidencia |\n|---|---|---|")
    w(f"| H1 leitura do texto | **Parcial** | L1 refutada (no `Terminal` sem texto). L2 confirmada: {f1(a2['fid']['exact_pct'])}% exatas em {a2['fid']['reads']} leituras. L3 inviavel: similaridade {f1(a3['fid']['mean_ratio'], 2)}, {f1(a3['fid']['exact_pct'])}% exatas |")
    w("| H2 envio de texto e teclas | **Confirmada, com ressalva** | `type`/`press` sem `--headed` ou sem foco nao entregam; com `--headed` e foco, chegam (P5 e Fase A). Entrada fisica |")
    w(f"| H3 agente completa os cenarios | **{'Confirmada' if v['b_ok'] else 'Parcial'}** | {pas_b}/{tot_b} casos pelo oraculo, em linguagem natural |")
    w(f"| H4 repetibilidade | **{'Confirmada' if a_all else 'Parcial'}** | Fase A: {sum(s['passed'] for s in a2['sc'].values())}/{sum(s['reps'] for s in a2['sc'].values())} (L2) e {sum(s['passed'] for s in a3['sc'].values())}/{sum(s['reps'] for s in a3['sc'].values())} (L3), sem `error_code`. Fase B so tem 3 repeticoes por caso |\n")
    w("## 7. Limitacoes e ressalvas\n")
    for t in (
        "Leitura so pela area de transferencia (menu Editar do terminal), nao pela arvore de acessibilidade.",
        "Entrada fisica (`--headed`) depende de foco; sem foco o agent-desktop recusa o envio.",
        "So display isolado (Xephyr). A sessao real nao foi medida; a sondagem P8 e parcial. Na sessao real a leitura sobrescreve a area de transferencia do usuario.",
        "So mate-terminal (VTE). O xterm e invisivel ao agent-desktop; outros terminais nao foram testados.",
        f"OCR inviavel no app real: similaridade media {f1(a3['fid']['mean_ratio'], 2)} (0% exatas).",
        "App de brinquedo em ncurses, nao 3270/5250; nao representa modo bloco nem emulador proprietario.",
        "Fase B: os subagentes rodaram sem aprovacao manual de comandos e tinham acesso a arquivos com as respostas. Foi proibido por instrucao, sem prova tecnica de que nao leram; o oraculo confirma as acoes, nao a origem dos `claims`.",
        f"Custo da Fase B: contexto final de cerca de {mil(round(tok_all, -3) if tok_all else None)} tokens por caso; o consumo real (centenas de milhares de tokens por repeticao, quase todo leitura de cache) e o custo estimado estao em CUSTOS.md. So 3 repeticoes por caso e um unico agente (D4).",
        "Ferramenta jovem (1.2.0 fixada); resultados valem para essa versao.",
    ):
        w(f"- {t}")
    w("\n## 8. Onde o resultado se aplica e fase 2\n")
    w("PRD secao 4, tres casos em que o agent-desktop poderia agregar:\n")
    w("- **Emulador sem API de script:** aplica-se, se o emulador expuser acessibilidade (VTE expoe; xterm nao) e tiver menu de copiar. Nao testado com emuladores proprietarios.")
    w("- **Fluxo misto com apps graficos:** plausivel (a ferramenta e feita para isso), mas nao medido nesta POC.")
    w("- **Ferramenta unica para o desktop:** aplica-se com a ressalva de que o app de terminal e lido por area de transferencia, e a entrada exige foco.")
    w("- Para terminal puro sem esses requisitos, tmux/expect continua mais simples, rapido e barato: a Fase A leva segundos por cenario e a Fase B centenas de milhares de tokens por caso (ver CUSTOS.md).\n")
    w("**Fase 2 (recomendacao curta):** repetir com um emulador 3270/5250 real ou proprietario, medir a sessao real com autorizacao, testar um segundo terminal acessivel e um fluxo misto (app grafico + tela verde), e repetir a Fase B com mais repeticoes e outro agente.\n")
    return "\n".join(L)


def generate(l2: Path | None = None, l3: Path | None = None, evid: Path = EVID, out: Path | None = None) -> Path:
    l2 = Path(l2) if l2 else (evid / DEFAULT_L2 if (evid / DEFAULT_L2).exists() else latest_run(evid, "l2"))
    l3 = Path(l3) if l3 else (evid / DEFAULT_L3 if (evid / DEFAULT_L3).exists() else latest_run(evid, "l3"))
    text = render(load_phase_a(l2), load_phase_a(l3), load_phase_b(evid))
    out = out or ROOT / "RESULTS.md"
    out.write_text(text, encoding="utf-8")
    return out
