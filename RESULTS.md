# RESULTS — POC agent-desktop em app de tela verde

> Gerado por `python3 -m harness report`. Os números vêm de `evidence/` (fora do git); não edite a mão.

## 1. Resumo e veredito proposto

Lendo a tela pela área de transferência (L2) e enviando teclas com `--headed`, o agent-desktop completou C1-C5 em 50/50 repetições determinísticas e 15/15 casos conduzidos por IA, mas só no mate-terminal e em display isolado.

**Veredito PROPOSTO: GO COM RESSALVAS.** O veredito final é do Igor (T-072); este texto é só a proposta.

Regra (PRD seção 8):

- Fase A, L2, taxa por cenário >= 9/10: atende.
- Fidelidade L2, igualdade exata >= 95%: atende (100,0%).
- Fase B, >= 2/3 por caso: atende (15/15).
- Com os três critérios atendidos, leitura por área de transferência e entrada `--headed`, a regra do GO seria satisfeita.
- A cláusula de ressalva "só em um emulador de terminal específico" também se aplica: o xterm é invisível ao agent-desktop e só o mate-terminal (VTE) foi medido. Por isso a proposta é GO com ressalvas, não GO pleno.
- Se algum critério acima não for atendido, o veredito cai: NO-GO quando a Fase A ou a B falham.

## 2. Ambiente e versões

| Item | Valor |
|---|---|
| Ferramenta | agent-desktop 1.2.0 |
| GnuCOBOL | 3.2.0 |
| Sistema | Ubuntu 26.04, X11, MATE |
| Display | Xephyr isolado `:2` |
| Terminal | mate-terminal |
| Entrada | I2 (`type --headed`, `press --window-id`) |
| Timeout por passo | 5,0 s |
| Execuções Fase A | L2 `20261112-162519`, L3 `20261112-163758` (10 repetições por cenário) |
| Execuções Fase B | `evidence/B-*` (Claude Code como subagente sem contexto) |

## 3. Matriz de viabilidade (sondagens P2-P7, G0)

| Estratégia | mate-terminal | xterm |
|---|---|---|
| L1 árvore de acessibilidade (`snapshot`, `get`, `find`) | Não: o nó `Terminal` tem `value` nulo | Não: janela invisível |
| L2 área de transferência | **Funciona** (6/6 exatas na sondagem) | Não se aplica |
| L3 `screenshot` + `tesseract` | Parcial: similaridade 0,86 a 0,95 na tela falsa, nunca exata | Não testado |
| I1 `type` sem `--headed` | Não: `POLICY_DENIED` | Não se aplica |
| I2 `type --headed` / `press --window-id` com foco | **Funciona** (3/3 e 15/15) | Não se aplica |
| `press` com janela sem foco | Não entrega (`STALE_REF` ou `ACTION_FAILED`) | Não se aplica |

Mate-terminal sem tmux: L2 exata contra a tela falsa (P8b). Não feito: qualquer medição na sessão real. Detalhes em G0-VIABILIDADE.md.

## 4. Fase A (sem IA)

### L2 (área de transferência) — `20261112-162519`

| Cenário | Sucesso | Duração média (s) | Leituras | Exatas | Similaridade média |
|---|---|---|---|---|---|
| C1 | 10/10 | 2,0 | 10 | 10 | 1,00 |
| C2 | 10/10 | 14,6 | 40 | 40 | 1,00 |
| C3 | 10/10 | 15,7 | 20 | 20 | 1,00 |
| C4 | 10/10 | 10,0 | 20 | 20 | 1,00 |
| C5 | 10/10 | 28,4 | 30 | 30 | 1,00 |

Fidelidade global: 120 leituras, similaridade média 1,00, igualdade exata em 100,0%.
Contagem de `error_code`: nenhum.

### L3 (screenshot + OCR) — `20261112-163758`

| Cenário | Sucesso | Duração média (s) | Leituras | Exatas | Similaridade média |
|---|---|---|---|---|---|
| C1 | 10/10 | 0,6 | 10 | 0 | 0,16 |
| C2 | 10/10 | 9,6 | 40 | 0 | 0,48 |
| C3 | 10/10 | 13,9 | 20 | 0 | 0,50 |
| C4 | 10/10 | 8,0 | 20 | 0 | 0,54 |
| C5 | 10/10 | 26,1 | 30 | 0 | 0,53 |

Fidelidade global: 120 leituras, similaridade média 0,48, igualdade exata em 0,0%.
Contagem de `error_code`: nenhum.

O sucesso de cada cenário é julgado pelo oráculo (tmux e arquivo de dados), não pela leitura; por isso L3 passa nos cenários mesmo sem servir como leitura.

Comparação com os limiares:

| Métrica | Limiar | L2 | L3 |
|---|---|---|---|
| Cenários com sucesso >= 9/10 | todos | 5/5 | 5/5 |
| Leituras exatas | >= 95% | 100,0% | 0,0% |

L3 falha o limiar de fidelidade; L2 o atende.

## 5. Fase B (agente de IA)

| Caso | Passou | Contexto final médio (tokens) | Chamadas médias | Duração média (s) |
|---|---|---|---|---|
| C1 | 3/3 | 90.489 | 6,0 | 43 |
| C2 | 3/3 | 97.577 | 11,0 | 112 |
| C3 | 3/3 | 95.117 | 9,3 | 92 |
| C4 | 3/3 | 97.280 | 11,0 | 107 |
| C5 | 3/3 | 96.941 | 13,7 | 136 |

Médias de custo excluem linhas com NA (interrompidas por limite de uso): 1 repetição(ões) fora do cálculo de tokens e duração. Limiar: >= 2/3 por caso (atende). Contexto final médio por caso: 95.481 tokens. Isso é o tamanho do contexto do subagente, não o consumo: o consumo real e o custo estão em CUSTOS.md.

## 6. Hipóteses

| ID | Estado | Evidência |
|---|---|---|
| H1 leitura do texto | **Parcial** | L1 refutada (nó `Terminal` sem texto). L2 confirmada: 100,0% exatas em 120 leituras. L3 inviável: similaridade 0,48, 0,0% exatas |
| H2 envio de texto e teclas | **Confirmada, com ressalva** | `type`/`press` sem `--headed` ou sem foco não entregam; com `--headed` e foco, chegam (P5 e Fase A). Entrada física |
| H3 agente completa os cenários | **Confirmada** | 15/15 casos pelo oráculo, em linguagem natural |
| H4 repetibilidade | **Confirmada** | Fase A: 50/50 (L2) e 50/50 (L3), sem `error_code`. Fase B só tem 3 repetições por caso |

## 7. Limitações e ressalvas

- Leitura só pela área de transferência (menu Editar do terminal), não pela árvore de acessibilidade.
- Entrada física (`--headed`) depende de foco; sem foco o agent-desktop recusa o envio.
- Só display isolado (Xephyr). A sessão real não foi medida; a sondagem P8 é parcial. Na sessão real a leitura sobrescreve a área de transferência do usuário.
- Só mate-terminal (VTE). O xterm é invisível ao agent-desktop; outros terminais não foram testados.
- OCR inviável no app real: similaridade média 0,48 (0% exatas).
- App de brinquedo em ncurses, não 3270/5250; não representa modo bloco nem emulador proprietário.
- Fase B: os subagentes rodaram sem aprovação manual de comandos e tinham acesso a arquivos com as respostas. Foi proibido por instrução, sem prova técnica de que não leram; o oráculo confirma as ações, não a origem dos `claims`.
- Custo da Fase B: contexto final de cerca de 95.000 tokens por caso; o consumo real (centenas de milhares de tokens por repetição, quase todo leitura de cache) e o custo estimado estão em CUSTOS.md. Só 3 repetições por caso e um único agente (D4).
- A Fase B foi medida antes da T-077, que mudou o app (só Enter valida ou grava) e o julgamento do C2 (exige código de saída 0). A Fase A foi refeita depois da T-077; a Fase B não foi.
- Ferramenta jovem (1.2.0 fixada); resultados valem para essa versão.

## 8. Onde o resultado se aplica e fase 2

PRD seção 4, três casos em que o agent-desktop poderia agregar:

- **Emulador sem API de script:** aplica-se, se o emulador expuser acessibilidade (VTE expõe; xterm não) e tiver menu de copiar. Não testado com emuladores proprietários.
- **Fluxo misto com apps gráficos:** plausível (a ferramenta é feita para isso), mas não medido nesta POC.
- **Ferramenta única para o desktop:** aplica-se com a ressalva de que o app de terminal é lido por área de transferência, e a entrada exige foco.
- Para terminal puro sem esses requisitos, tmux/expect continua mais simples, rápido e barato: a Fase A leva segundos por cenário e a Fase B centenas de milhares de tokens por caso (ver CUSTOS.md).

**Fase 2 (recomendação curta):** repetir com um emulador 3270/5250 real ou proprietário, medir a sessão real com autorização, testar um segundo terminal acessível e um fluxo misto (app gráfico + tela verde), e repetir a Fase B com mais repetições e outro agente.
