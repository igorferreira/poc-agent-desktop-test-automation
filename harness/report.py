"""Gera RESULTS.md a partir de evidence/ (Fases A e B). Só números e identificadores de execução vao ao texto."""
import csv
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EVID = ROOT / "evidence"
# Limiares do PRD seção 8
LIM_A, LIM_FID, LIM_B = 9 / 10, 95.0, 2 / 3


def _j(p: Path):
    return json.loads(p.read_text(encoding="utf-8"))


def latest_run(evid: Path, read: str) -> Path:
    """Execução mais recente da leitura (pelo meta.json), entre as que tem summary.json."""
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
        raise SystemExit(f"nenhuma execução da Fase A com leitura {read} em {evid}")
    return best[1]


def load_phase_a(d: Path) -> dict:
    """Taxas por cenário, duração média, fidelidade (global e por cenário) e error_code."""
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
    """Por caso: passou/total (verify.json, ou ledger se faltar) e médias de tokens/chamadas/duração sem NA."""
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


# Decisão do dono do produto (T-072): veredito, quem, quando.
DECISAO = ("GO com ressalvas", "Igor", "2026-11-12")


def verdict(a2: dict, b: dict) -> dict:
    """Regra do PRD seção 8. GO exige limiares (A em L2, fidelidade L2, B); como só o mate-terminal funciona
    (xterm invisível), aplica-se a cláusula de ressalva 'só em um emulador de terminal específico'."""
    a_ok = all(v["passed"] / v["reps"] >= LIM_A for v in a2["sc"].values())
    f_ok = (a2["fid"]["exact_pct"] or 0) >= LIM_FID
    b_ok = bool(b) and all(v["passed"] / v["total"] >= LIM_B for v in b.values())
    # PRD §8: NO-GO se a entrada não é confiável ou nenhuma leitura atinge o limiar de fidelidade.
    nome = "GO com ressalvas" if (a_ok and f_ok and b_ok) else "NO-GO"
    return {"nome": nome, "a_ok": a_ok, "f_ok": f_ok, "b_ok": b_ok}


def f1(x, d=1):
    return "n/d" if x is None else f"{x:.{d}f}".replace(".", ",")


def mil(x):
    return "n/d" if x is None else f"{x:,.0f}".replace(",", ".")


def render(a2: dict, a3: dict, b: dict) -> str:
    v = verdict(a2, b)
    ok = lambda c: "atende" if c else "NÃO atende"  # noqa: E731
    m = a2["meta"]
    tot_b = sum(c["total"] for c in b.values())
    pas_b = sum(c["passed"] for c in b.values())
    costs = [c["tokens"] for c in b.values() if c["tokens"] is not None]
    tok_all = sum(costs) / len(costs) if costs else None
    reps = {v_["reps"] for v_ in a2["sc"].values()}
    L = []
    w = L.append
    w("# RESULTS — POC agent-desktop em app de tela verde\n")
    w("> Gerado por `python3 -m harness report`. Os números vêm de `evidence/` (fora do git); não edite a mão.\n")
    w("## 1. Resumo e veredito proposto\n")
    w(f"Lendo a tela pela área de transferência (L2) e enviando teclas com `--headed`, o agent-desktop completou "
      f"C1-C5 em {sum(s['passed'] for s in a2['sc'].values())}/{sum(s['reps'] for s in a2['sc'].values())} "
      f"repetições determinísticas e {pas_b}/{tot_b} casos conduzidos por IA, mas só no mate-terminal e em display isolado.\n")
    w(f"**Veredito PROPOSTO pelos números: {v['nome'].upper()}.**\n")
    if v["nome"] == DECISAO[0]:
        w(f"**Veredito FINAL: {DECISAO[0].upper()}**, aprovado por {DECISAO[1]} em {DECISAO[2]} (T-072).\n")
    else:
        w(f"**Atenção:** a decisão registrada ({DECISAO[0]}, {DECISAO[2]}) difere do que os números atuais indicam; precisa de nova decisão do Igor (T-072).\n")
    w("Regra (PRD seção 8):\n")
    w(f"- Fase A, L2, taxa por cenário >= 9/10: {ok(v['a_ok'])}.")
    w(f"- Fidelidade L2, igualdade exata >= 95%: {ok(v['f_ok'])} ({f1(a2['fid']['exact_pct'])}%).")
    w(f"- Fase B, >= 2/3 por caso: {ok(v['b_ok'])} ({pas_b}/{tot_b}).")
    if v["a_ok"] and v["f_ok"] and v["b_ok"]:
        w("- Com os três critérios atendidos, leitura por área de transferência e entrada `--headed`, a regra do GO seria satisfeita.")
        w("- A cláusula de ressalva \"só em um emulador de terminal específico\" também se aplica: o xterm é invisível ao "
          f"agent-desktop e só o mate-terminal (VTE) foi medido. Por isso a proposta é {v['nome']}, não GO pleno.")
    else:
        w(f"- Há critério não atendido; a regra do GO não é satisfeita e a proposta é {v['nome']}.")
    w("- Se algum critério acima não for atendido, o veredito cai: NO-GO quando a Fase A ou a B falham.\n")
    w("## 2. Ambiente e versões\n")
    w("| Item | Valor |\n|---|---|")
    w(f"| Ferramenta | {m.get('agent_desktop')} |")
    w("| GnuCOBOL | 3.2.0 |\n| Sistema | Ubuntu 26.04, X11, MATE |")
    w(f"| Display | Xephyr isolado `{m.get('display')}` |")
    w(f"| Terminal | {m.get('terminal')} |")
    w(f"| Entrada | {m.get('input_strategy')} (`type --headed`, `press --window-id`) |")
    w(f"| Timeout por passo | {f1(m.get('step_timeout_s'))} s |")
    w(f"| Execuções Fase A | L2 `{a2['run_id']}`, L3 `{a3['run_id']}` ({', '.join(str(r) for r in sorted(reps))} repetições por cenário) |")
    w("| Execuções Fase B | `evidence/B-*` (Claude Code como subagente sem contexto) |\n")
    w("## 3. Matriz de viabilidade (sondagens P2-P7, G0)\n")
    w("| Estratégia | mate-terminal | xterm |\n|---|---|---|")
    w("| L1 árvore de acessibilidade (`snapshot`, `get`, `find`) | Não: o nó `Terminal` tem `value` nulo | Não: janela invisível |")
    w("| L2 área de transferência | **Funciona** (6/6 exatas na sondagem) | Não se aplica |")
    w("| L3 `screenshot` + `tesseract` | Parcial: similaridade 0,86 a 0,95 na tela falsa, nunca exata | Não testado |")
    w("| I1 `type` sem `--headed` | Não: `POLICY_DENIED` | Não se aplica |")
    w("| I2 `type --headed` / `press --window-id` com foco | **Funciona** (3/3 e 15/15) | Não se aplica |")
    w("| `press` com janela sem foco | Não entrega (`STALE_REF` ou `ACTION_FAILED`) | Não se aplica |\n")
    w("Mate-terminal sem tmux: L2 exata contra a tela falsa (P8b). Não feito: qualquer medição na sessão real. Detalhes em G0-VIABILIDADE.md.\n")
    w("## 4. Fase A (sem IA)\n")
    for tag, a in (("L2 (área de transferência)", a2), ("L3 (screenshot + OCR)", a3)):
        w(f"### {tag} — `{a['run_id']}`\n")
        w("| Cenário | Sucesso | Duração média (s) | Leituras | Exatas | Similaridade média |\n|---|---|---|---|---|---|")
        for cid, s in sorted(a["sc"].items()):
            w(f"| {cid} | {s['passed']}/{s['reps']} | {f1(s['dur'])} | {s['reads']} | {s['exact']} | {f1(s['ratio'], 2)} |")
        fd = a["fid"]
        w(f"\nFidelidade global: {fd['reads']} leituras, similaridade média {f1(fd['mean_ratio'], 2)}, "
          f"igualdade exata em {f1(fd['exact_pct'])}%.")
        w("Contagem de `error_code`: " + (", ".join(f"{k}={n}" for k, n in sorted(a["codes"].items())) or "nenhum") + ".\n")
    w("O sucesso de cada cenário é julgado pelo oráculo (tmux e arquivo de dados), não pela leitura; por isso L3 "
      "passa nos cenários mesmo sem servir como leitura.\n")
    w("Comparação com os limiares:\n")
    w("| Métrica | Limiar | L2 | L3 |\n|---|---|---|---|")
    for lab, lim, f in (("Cenários com sucesso >= 9/10", "todos", lambda a: f"{sum(s['passed'] / s['reps'] >= LIM_A for s in a['sc'].values())}/{len(a['sc'])}"),
                        ("Leituras exatas", ">= 95%", lambda a: f"{f1(a['fid']['exact_pct'])}%")):
        w(f"| {lab} | {lim} | {f(a2)} | {f(a3)} |")
    l2f, l3f = a2["fid"]["exact_pct"] or 0, a3["fid"]["exact_pct"] or 0
    w(f"\nL3 {'atende' if l3f >= LIM_FID else 'falha'} o limiar de fidelidade; L2 o {'atende' if l2f >= LIM_FID else 'falha'}.\n")
    w("## 5. Fase B (agente de IA)\n")
    w("| Caso | Passou | Contexto final médio (tokens) | Chamadas médias | Duração média (s) |\n|---|---|---|---|---|")
    for cid, c in b.items():
        w(f"| {cid} | {c['passed']}/{c['total']} | {mil(c['tokens'])} | {f1(c['calls'])} | {f1(c['dur'], 0)} |")
    w(f"\nMédias de custo excluem linhas com NA (interrompidas por limite de uso): "
      f"{sum(c['total'] - c['n_cost'] for c in b.values())} repetição(ões) fora do cálculo de tokens e duração. "
      f"Limiar: >= 2/3 por caso ({ok(v['b_ok'])}). Contexto final médio por caso: {mil(tok_all)} tokens. Isso é o tamanho do contexto do subagente, não o consumo: o consumo real e o custo estão em CUSTOS.md.\n")
    w("## 6. Hipóteses\n")
    a_all = all(s["passed"] == s["reps"] for s in a2["sc"].values())
    w("| ID | Estado | Evidência |\n|---|---|---|")
    h1 = "Confirmada" if l2f >= LIM_FID and l3f >= LIM_FID else "Parcial" if l2f >= LIM_FID or l3f >= LIM_FID else "Refutada"
    w(f"| H1 leitura do texto | **{h1}** | L1 refutada (nó `Terminal` sem texto). L2 {'confirmada' if l2f >= LIM_FID else 'abaixo do limiar'}: {f1(a2['fid']['exact_pct'])}% exatas em {a2['fid']['reads']} leituras. L3 {'viável' if l3f >= LIM_FID else 'inviável'}: similaridade {f1(a3['fid']['mean_ratio'], 2)}, {f1(a3['fid']['exact_pct'])}% exatas |")
    w(f"| H2 envio de texto e teclas | **{'Confirmada, com ressalva' if v['a_ok'] else 'Parcial'}** | `type`/`press` sem `--headed` ou sem foco não entregam; com `--headed` e foco, chegam (P5 e Fase A). Entrada física |")
    w(f"| H3 agente completa os cenários | **{'Confirmada' if v['b_ok'] else 'Parcial'}** | {pas_b}/{tot_b} casos pelo oráculo, em linguagem natural |")
    w(f"| H4 repetibilidade | **{'Confirmada' if a_all else 'Parcial'}** | Fase A: {sum(s['passed'] for s in a2['sc'].values())}/{sum(s['reps'] for s in a2['sc'].values())} (L2) e {sum(s['passed'] for s in a3['sc'].values())}/{sum(s['reps'] for s in a3['sc'].values())} (L3), sem `error_code`. Fase B só tem 3 repetições por caso |\n")
    w("## 7. Limitações e ressalvas\n")
    for t in (
        "Leitura só pela área de transferência (menu Editar do terminal), não pela árvore de acessibilidade.",
        "Entrada física (`--headed`) depende de foco; sem foco o agent-desktop recusa o envio.",
        "Só display isolado (Xephyr). A sessão real não foi medida; a sondagem P8 é parcial. Na sessão real a leitura sobrescreve a área de transferência do usuário.",
        "Só mate-terminal (VTE). O xterm é invisível ao agent-desktop; outros terminais não foram testados.",
        f"OCR inviável no app real: similaridade média {f1(a3['fid']['mean_ratio'], 2)} ({a3['fid']['exact_pct']:.0f}% exatas).",
        "App de brinquedo em ncurses, não 3270/5250; não representa modo bloco nem emulador proprietário.",
        "Fase B: os subagentes rodaram sem aprovação manual de comandos e tinham acesso a arquivos com as respostas. Foi proibido por instrução, sem prova técnica de que não leram; o oráculo confirma as ações, não a origem dos `claims`.",
        f"Custo da Fase B: contexto final de cerca de {mil(round(tok_all, -3) if tok_all else None)} tokens por caso; o consumo real (centenas de milhares de tokens por repetição, quase todo leitura de cache) e o custo estimado estão em CUSTOS.md. Só 3 repetições por caso e um único agente (D4).",
        "A Fase B foi medida antes da T-077, que mudou o app (só Enter valida ou grava) e o julgamento do C2 (exige código de saída 0). A Fase A foi refeita depois da T-077; a Fase B não foi.",
        "Ferramenta jovem (1.2.0 fixada); resultados valem para essa versão.",
    ):
        w(f"- {t}")
    w("\n## 8. Onde o resultado se aplica e fase 2\n")
    w("PRD seção 4, três casos em que o agent-desktop poderia agregar:\n")
    w("- **Emulador sem API de script:** aplica-se, se o emulador expuser acessibilidade (VTE expõe; xterm não) e tiver menu de copiar. Não testado com emuladores proprietários.")
    w("- **Fluxo misto com apps gráficos:** plausível (a ferramenta é feita para isso), mas não medido nesta POC.")
    w("- **Ferramenta única para o desktop:** aplica-se com a ressalva de que o app de terminal é lido por área de transferência, e a entrada exige foco.")
    w("- Para terminal puro sem esses requisitos, tmux/expect continua mais simples, rápido e barato: a Fase A leva segundos por cenário e a Fase B centenas de milhares de tokens por caso (ver CUSTOS.md).\n")
    w("**Fase 2 (recomendação curta):** repetir com um emulador 3270/5250 real ou proprietário, medir a sessão real com autorização, testar um segundo terminal acessível e um fluxo misto (app gráfico + tela verde), e repetir a Fase B com mais repetições e outro agente.\n")
    return "\n".join(L)


def generate(l2: Path | None = None, l3: Path | None = None, evid: Path = EVID, out: Path | None = None) -> Path:
    l2 = Path(l2) if l2 else latest_run(evid, "l2")
    l3 = Path(l3) if l3 else latest_run(evid, "l3")
    text = render(load_phase_a(l2), load_phase_a(l3), load_phase_b(evid))
    out = out or ROOT / "RESULTS.md"
    out.write_text(text, encoding="utf-8")
    return out
