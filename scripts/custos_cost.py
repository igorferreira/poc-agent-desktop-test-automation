"""Turn usage.json into cost tables (markdown) for CUSTOS.md.

Usage: python3 -I scripts/custos_cost.py <usage.json>
Prices: USD per million tokens, from the claude-api skill model table (cached 2026-10-06).
Cache write = 1.25x input (5 min TTL) or 2x input (1 h TTL), per shared/prompt-caching.md.
claude-fable-5-2 is not in the table: priced as Claude Fable 5.1 (assumption, flagged in the doc).
"""
import json
import sys
from collections import defaultdict

PRICES = {  # input, output, cache read
    "claude-opus-5-5": (4.00, 20.00, 0.20),
    "claude-sonnet-5-5": (2.00, 10.00, 0.20),
    "claude-fable-5-2": (10.00, 50.00, 0.25),
}
K = ("input_tokens", "output_tokens", "cache_read_input_tokens", "cw5m", "cw1h", "requests")


def cost(model, u):
    i, o, r = PRICES[model]
    return (u["input_tokens"] * i + u["output_tokens"] * o + u["cache_read_input_tokens"] * r
            + u["cw5m"] * i * 1.25 + u["cw1h"] * i * 2.0) / 1e6


def total_tokens(u):
    return u["input_tokens"] + u["output_tokens"] + u["cache_read_input_tokens"] + u["cw5m"] + u["cw1h"]


def group(desc):
    if desc.startswith("Phase B"):
        return "Fase B (agente de IA executando casos)"
    return "Construção da POC (subagentes de tarefa)"


def fmt(n):
    return f"{n:,.0f}".replace(",", ".")


def usd(x):
    return f"US$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


r = json.load(open(sys.argv[1]))
rows = []
for model, u in r["main"]["models"].items():
    rows.append(("Sessão principal (orquestrador)", "—", model, u))
for s in r["subagents"]:
    for model, u in s["models"].items():
        rows.append((s["meta"].get("description", s["id"]), s["meta"].get("agentType", "?"), model, u))

# 1. per-model totals
by_model = defaultdict(lambda: dict.fromkeys(K, 0))
for _, _, m, u in rows:
    for k in K:
        by_model[m][k] += u[k]
print("## por modelo")
print("| Modelo | Requisições | Entrada | Saída | Leitura de cache | Escrita de cache 5 min | Escrita de cache 1 h | Total de tokens | Custo estimado |")
print("|---|---:|---:|---:|---:|---:|---:|---:|---:|")
grand = 0.0
gt = 0
for m, u in sorted(by_model.items()):
    c = cost(m, u)
    grand += c
    gt += total_tokens(u)
    print(f"| `{m}` | {u['requests']} | {fmt(u['input_tokens'])} | {fmt(u['output_tokens'])} | {fmt(u['cache_read_input_tokens'])} | {fmt(u['cw5m'])} | {fmt(u['cw1h'])} | {fmt(total_tokens(u))} | {usd(c)} |")
print(f"| **Total** | | | | | | | **{fmt(gt)}** | **{usd(grand)}** |")

# 2. per group
print("\n## por grupo")
by_group = defaultdict(lambda: [0.0, 0, 0])
for name, _, m, u in rows:
    g = "Sessão principal (orquestrador)" if name.startswith("Sessão") else group(name)
    by_group[g][0] += cost(m, u)
    by_group[g][1] += total_tokens(u)
    by_group[g][2] += u["output_tokens"]
print("| Grupo | Total de tokens | Tokens de saída | Custo estimado | % do custo |")
print("|---|---:|---:|---:|---:|")
for g, (c, t, o) in sorted(by_group.items(), key=lambda x: -x[1][0]):
    print(f"| {g} | {fmt(t)} | {fmt(o)} | {usd(c)} | {100 * c / grand:.0f}% |")

# 3. per subagent
print("\n## por subagente")
print("| Subagente | Tipo | Modelo | Requisições | Total de tokens | Saída | Custo estimado |")
print("|---|---|---|---:|---:|---:|---:|")
for name, typ, m, u in sorted(rows, key=lambda x: x[0]):
    if name.startswith("Sessão"):
        continue
    print(f"| {name} | `{typ}` | `{m}` | {u['requests']} | {fmt(total_tokens(u))} | {fmt(u['output_tokens'])} | {usd(cost(m, u))} |")

# 4. Phase B per case
print("\n## fase B por caso")
pb = defaultdict(list)
for name, _, m, u in rows:
    if name.startswith("Phase B"):
        case = name.split()[2]
        pb[case].append((name, cost(m, u), total_tokens(u)))
print("| Caso | Repetições | Custo médio por repetição | Total de tokens médio | Custo total |")
print("|---|---:|---:|---:|---:|")
allc = []
for case in sorted(pb):
    v = pb[case]
    cs = [x[1] for x in v]
    allc += cs
    print(f"| {case} | {len(v)} | {usd(sum(cs) / len(cs))} | {fmt(sum(x[2] for x in v) / len(v))} | {usd(sum(cs))} |")
print(f"| **Todos** | {len(allc)} | {usd(sum(allc) / len(allc))} | | **{usd(sum(allc))}** |")

# 5. sensitivity: what if everything were billed at plain input price (no cache discount)
nocache = 0.0
for _, _, m, u in rows:
    i, o, _r = PRICES[m]
    nocache += ((u["input_tokens"] + u["cache_read_input_tokens"] + u["cw5m"] + u["cw1h"]) * i + u["output_tokens"] * o) / 1e6
print(f"\n## sensibilidade\nsem cache (tudo como entrada normal): {usd(nocache)}; cache economizou {usd(nocache - grand)}")
fable = by_model.get("claude-fable-5-2")
if fable:
    print(f"fable-5-2 custo: {usd(cost('claude-fable-5-2', fable))}")
print(f"periodo sessao principal: {r['main']['first']} -> {r['main']['last']}")
