# CUSTOS — Consumo de tokens e custo estimado da POC

Versão 1 · 2026-11-12 · Tarefa T-074. Fotografia tirada às 19:07 UTC de 12/11/2026, antes do fechamento (T-071 a T-073). O trabalho feito depois dessa hora não está nas tabelas.

## 1. Resumo

| | |
|---|---|
| Tokens processados, no total | **54,9 milhões** |
| Custo estimado em preço de API | **US$ 44,80** |
| Sem cache de prompt, o mesmo trabalho custaria | US$ 224,00 (o cache economizou US$ 179,20, 80%) |
| Custo por repetição da Fase B (um agente executando um caso) | **US$ 0,71 em média** (de US$ 0,50 a US$ 1,35) |
| Parte do custo que é do orquestrador | 61% |

**O que este número é:** o custo que o mesmo consumo teria se fosse cobrado pela API da Anthropic, pela tabela de preços da seção 5. **O que não é:** a cobrança real. A POC rodou no Claude Code com plano por assinatura: o limite de uso foi atingido duas vezes ("5-hour limit") e não houve cobrança por token. O valor serve para comparar abordagens e para estimar quanto custaria rodar isto pela API.

## 2. Onde foi o consumo

| Grupo | Total de tokens | Tokens de saída | Custo estimado | % do custo |
|---|---:|---:|---:|---:|
| Sessão principal (orquestrador) | 30.946.953 | 153.182 | US$ 27,24 | 61% |
| Fase B (agente de IA executando casos) | 12.140.342 | 88.133 | US$ 10,67 | 24% |
| Construção da POC (subagentes de tarefa) | 11.771.819 | 191.964 | US$ 6,89 | 15% |
| **Total** | **54.859.114** | **433.279** | **US$ 44,80** | |

Por modelo:

| Modelo | Requisições | Entrada | Saída | Leitura de cache | Escrita de cache 5 min | Escrita de cache 1 h | Total de tokens | Custo estimado |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `claude-fable-5-2` | 22 | 44 | 83.019 | 2.640.770 | 0 | 393.499 | 3.117.332 | US$ 12,68 |
| `claude-opus-5-5` | 273 | 550 | 199.127 | 38.256.364 | 1.508.321 | 849.107 | 40.813.469 | US$ 25,97 |
| `claude-sonnet-5-5` | 190 | 384 | 151.133 | 9.871.448 | 640.844 | 264.504 | 10.928.313 | US$ 6,15 |
| **Total** | 485 | | | | | | **54.859.114** | **US$ 44,80** |

## 3. Por subagente

O modelo de cada subagente vem da definição do agente: os agentes `devsquad-*`, `python-senior` e `ubuntu-mate-doc` rodaram em `claude-sonnet-5-5`; `general-purpose` e `ai-solution-architect`, em `claude-opus-5-5`.

| Subagente | Tarefa | Tipo | Modelo | Requisições | Total de tokens | Saída | Custo estimado |
|---|---|---|---|---:|---:|---:|---:|
| T-012 + T-014 isolated display | T-012, T-014 | `ubuntu-mate-doc` | `claude-sonnet-5-5` | 18 | 631.742 | 10.222 | US$ 0,33 |
| T-013 read agent-desktop guides | T-013 | `devsquad-architect` | `claude-sonnet-5-5` | 40 | 2.935.483 | 27.361 | US$ 1,14 |
| T-020 fake screen in tmux | T-020 | `devsquad-backend` | `claude-sonnet-5-5` | 6 | 175.722 | 6.334 | US$ 0,18 |
| F2 probes P2-P8 isolated display | T-021 a T-027 | `devsquad-qa` | `claude-sonnet-5-5` | 45 | 2.920.952 | 27.951 | US$ 1,25 |
| T-030/T-031 COBOL app CADCLI | T-030 a T-032 | `devsquad-backend` | `claude-sonnet-5-5` | 16 | 617.712 | 14.773 | US$ 0,37 |
| T-040 ad.py envelope wrapper | T-040 | `python-senior` | `claude-sonnet-5-5` | 5 | 140.631 | 5.685 | US$ 0,16 |
| T-041/T-043/T-044 harness modules | T-041, T-043, T-044 | `python-senior` | `claude-sonnet-5-5` | 35 | 2.121.729 | 26.427 | US$ 0,87 |
| T-042/T-050/T-061 oracle, scenarios, CLI | T-042, T-050, T-061 | `python-senior` | `claude-sonnet-5-5` | 10 | 429.505 | 16.889 | US$ 0,36 |
| T-060 Phase B cases | T-060 | `ai-solution-architect` | `claude-opus-5-5` | 15 | 1.103.863 | 34.830 | US$ 1,44 |
| T-070 report.py and RESULTS.md | T-070 | `python-senior` | `claude-sonnet-5-5` | 9 | 388.467 | 12.869 | US$ 0,34 |
| Fix cases/AGENT.md ambiguities | T-064 | `ai-solution-architect` | `claude-opus-5-5` | 8 | 306.013 | 8.623 | US$ 0,45 |

A Fase A (T-051) não aparece: ela é o harness em Python, sem modelo de IA. Custo de tokens: zero.

## 4. Fase B: custo por caso

Cada repetição é um subagente `general-purpose` novo, em `claude-opus-5-5`, que lê `cases/AGENT.md` e o caso e opera o app pelo `agent-desktop`.

| Caso | Repetições | Custo médio por repetição | Tokens médios por repetição | Custo total |
|---|---:|---:|---:|---:|
| C1 — ler o menu | 3 | US$ 0,52 | 400.220 | US$ 1,55 |
| C2 — navegar | 3 | US$ 0,73 | 881.991 | US$ 2,18 |
| C3 — incluir | 3 | US$ 0,64 | 716.315 | US$ 1,93 |
| C4 — consultar | 3 | US$ 0,73 | 880.009 | US$ 2,18 |
| C5 — erros de validação | 3 | US$ 0,94 | 1.168.245 | US$ 2,83 |
| **Todos** | 15 | **US$ 0,71** | | **US$ 10,67** |

Detalhe por repetição:

| Repetição | Requisições | Total de tokens | Saída | Custo estimado |
|---|---:|---:|---:|---:|
| C1 r1 / r2 / r3 | 5 / 5 / 5 | 400.123 / 400.362 / 400.176 | 2.258 / 2.429 / 2.305 | US$ 0,55 / 0,50 / 0,50 |
| C2 r1 / r2 / r3 | 10 / 10 / 10 | 886.983 / 879.654 / 879.335 | 7.725 / 7.073 / 6.790 | US$ 0,74 / 0,72 / 0,71 |
| C3 r1 / r2 / r3 | 8 / 9 / 8 | 685.003 / 775.804 / 688.138 | 5.255 / 4.880 / 5.906 | US$ 0,64 / 0,65 / 0,65 |
| C4 r1 / r2 / r3 | 10 / 10 / 10 | 879.192 / 880.035 / 880.801 | 7.131 / 7.257 / 7.432 | US$ 0,72 / 0,73 / 0,73 |
| C5 r1 / r2 / r3 | 13 / 12 / 14 | 1.161.607 / 1.064.516 / 1.278.613 | 5.688 / 5.920 / 10.084 | US$ 0,75 / 0,73 / 1,35 |

A C5 r3 foi interrompida pelo limite de uso e retomada mais de 3 horas depois. O cache expirou nesse intervalo e precisou ser escrito de novo (185 mil tokens de escrita, contra cerca de 84 mil nas outras). Por isso ela custou quase o dobro. Sem ela, a média da C5 seria US$ 0,74.

**Comparação com a Fase A:** o mesmo conjunto de cinco cenários rodou 10 vezes no harness determinístico, sem modelo. O custo de tokens foi zero, e cada execução levou de 2 a 29 s. Na Fase B, uma rodada dos cinco casos custa cerca de US$ 3,60 e leva de 1 a 2 minutos por caso.

## 5. Como foi calculado

**Fonte dos tokens:** o campo `usage` de cada resposta da API gravado pelo Claude Code nos registros da sessão (`~/.claude/projects/<projeto>/<sessão>.jsonl` e `<sessão>/subagents/agent-*.jsonl`). Cada resposta é contada uma vez: o script ignora linhas repetidas da mesma resposta (mesmo `message.id` e `requestId`). Os scripts estão no repositório:

```bash
P=~/.claude/projects/-opt-projetos-poc-agent-desktop-test-automation/<sessão>
python3 -I scripts/custos_usage.py "$P.jsonl" "$P/subagents" /tmp/usage.json
python3 -I scripts/custos_cost.py /tmp/usage.json
```

**Preços usados** (US$ por milhão de tokens; tabela do guia da API da Anthropic, versão de 06/10/2026):

| Modelo | Entrada | Saída | Leitura de cache | Escrita de cache 5 min | Escrita de cache 1 h |
|---|---:|---:|---:|---:|---:|
| `claude-opus-5-5` | 4,00 | 20,00 | 0,20 | 5,00 | 8,00 |
| `claude-sonnet-5-5` | 2,00 | 10,00 | 0,20 | 2,50 | 4,00 |
| `claude-fable-5-2` | 10,00 | 50,00 | 0,25 | 12,50 | 20,00 |

A escrita de cache custa 1,25 vez a entrada com validade de 5 minutos e 2 vezes com validade de 1 hora.

**Premissa a confirmar:** `claude-fable-5-2` não está na tabela de preços consultada. Usei o preço do Claude Fable 5.1, da mesma linha. Ele responde por US$ 12,68 do total. Se o preço for outro, só essa linha muda.

## 6. Leituras

1. **Quase todo o consumo é releitura de contexto.** 92% dos tokens são leitura de cache: a cada chamada de ferramenta, o modelo relê a conversa inteira. Só 0,8% dos tokens são de saída, mas eles respondem por cerca de 20% do custo. O cache de prompt é o que torna isso viável: sem ele, o custo seria 5 vezes maior.
2. **O custo de um caso cresce com o número de passos, não com a dificuldade.** C1 (só leitura, 5 requisições) custa US$ 0,52; C5 (três formulários, 12 a 14 requisições) custa US$ 0,94. Cada requisição relê de 80 a 100 mil tokens de contexto.
3. **O orquestrador é o maior gasto (61%).** A sessão principal acumulou o planejamento, a coordenação dos 26 subagentes e o papel de operador da Fase B. Ela passa de 30 milhões de tokens, porque o contexto dela é longo e relido a cada passo.
4. **Subagentes em `claude-sonnet-5-5` saíram baratos.** Os 11 subagentes de construção custaram US$ 6,89 no total. A mais cara, as sondagens P2–P8, custou US$ 1,25.
5. **Correção de um número registrado antes.** O `evidence/phase-b-ledger.tsv` e a primeira versão do `RESULTS.md` falavam em "cerca de 95 mil tokens por caso". Esse número é o tamanho do contexto final do subagente, não o consumo. O consumo real é de 400 mil a 1,2 milhão de tokens por repetição. O `RESULTS.md` foi corrigido para apontar para este documento.

## 7. Projeção

Estimativa para rodar a Fase B por API, nos mesmos termos (Claude Opus 5.5, um agente por caso):

| Uso | Custo estimado |
|---|---:|
| 1 caso simples, como C1 | cerca de US$ 0,50 |
| 1 caso com formulário, como C3 a C5 | US$ 0,65 a US$ 0,95 |
| Rodada completa dos 5 casos | cerca de US$ 3,60 |
| Regressão diária dos 5 casos, por 30 dias | cerca de US$ 107 |

A projeção não inclui o orquestrador, que nesta POC custou mais que a Fase B. Num uso real, o operador seria um script, sem modelo. Ela também não inclui retentativas: na POC, nenhuma das 15 repetições precisou ser refeita.

## 8. Não verificado

- Preço real do `claude-fable-5-2` (seção 5).
- Se os registros do Claude Code incluem as chamadas de compactação do contexto da sessão principal. Se não incluírem, o custo do orquestrador está subestimado.
- Desconto do plano de assinatura: o valor real pago não foi calculado.
- Conversão para reais: não foi feita, para não usar uma cotação sem fonte.
