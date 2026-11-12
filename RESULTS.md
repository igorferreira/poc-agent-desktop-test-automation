# RESULTS — POC agent-desktop em app de tela verde

> Gerado por `python3 -m harness report`. Os numeros vem de `evidence/` (fora do git); nao edite a mao.

## 1. Resumo e veredito proposto

Lendo a tela pela area de transferencia (L2) e enviando teclas com `--headed`, o agent-desktop completou C1-C5 em 50/50 repeticoes deterministicas e 15/15 casos conduzidos por IA, mas so no mate-terminal e em display isolado.

**Veredito PROPOSTO: GO COM RESSALVAS.** O veredito final e do Igor (T-072); este texto e so a proposta.

Regra (PRD secao 8):

- Fase A, L2, taxa por cenario >= 9/10: atende.
- Fidelidade L2, igualdade exata >= 95%: atende (100,0%).
- Fase B, >= 2/3 por caso: atende (15/15).
- Com os tres criterios atendidos, leitura por area de transferencia e entrada `--headed`, a regra do GO seria satisfeita.
- A clausula de ressalva "so em um emulador de terminal especifico" tambem se aplica: o xterm e invisivel ao agent-desktop e so o mate-terminal (VTE) foi medido. Por isso a proposta e GO com ressalvas, nao GO pleno.
- Se algum criterio acima nao for atendido, o veredito cai: NO-GO quando a Fase A ou a B falham.

## 2. Ambiente e versoes

| Item | Valor |
|---|---|
| Ferramenta | agent-desktop 1.2.0 |
| GnuCOBOL | 3.2.0 |
| Sistema | Ubuntu 26.04, X11, MATE |
| Display | Xephyr isolado `:2` |
| Terminal | mate-terminal |
| Entrada | I2 (`type --headed`, `press --window-id`) |
| Timeout por passo | 5,0 s |
| Execucoes Fase A | L2 `20261112-113612`, L3 `20261112-112535` (10 repeticoes por cenario) |
| Execucoes Fase B | `evidence/B-*` (Claude Code como subagente sem contexto) |

## 3. Matriz de viabilidade (sondagens P2-P7, G0)

| Estrategia | mate-terminal | xterm |
|---|---|---|
| L1 arvore de acessibilidade (`snapshot`, `get`, `find`) | Nao: o no `Terminal` tem `value` nulo | Nao: janela invisivel |
| L2 area de transferencia | **Funciona** (6/6 exatas na sondagem) | Nao se aplica |
| L3 `screenshot` + `tesseract` | Parcial: similaridade 0,86 a 0,95 na tela falsa, nunca exata | Nao testado |
| I1 `type` sem `--headed` | Nao: `POLICY_DENIED` | Nao se aplica |
| I2 `type --headed` / `press --window-id` com foco | **Funciona** (3/3 e 15/15) | Nao se aplica |
| `press` com janela sem foco | Nao entrega (`STALE_REF` ou `ACTION_FAILED`) | Nao se aplica |

Nao feito: mate-terminal sem tmux; qualquer medicao na sessao real. Detalhes em G0-VIABILIDADE.md.

## 4. Fase A (sem IA)

### L2 (area de transferencia) — `20261112-113612`

| Cenario | Sucesso | Duracao media (s) | Leituras | Exatas | Similaridade media |
|---|---|---|---|---|---|
| C1 | 10/10 | 1,9 | 10 | 10 | 1,00 |
| C2 | 10/10 | 13,7 | 40 | 40 | 1,00 |
| C3 | 10/10 | 15,7 | 20 | 20 | 1,00 |
| C4 | 10/10 | 10,1 | 20 | 20 | 1,00 |
| C5 | 10/10 | 28,6 | 30 | 30 | 1,00 |

Fidelidade global: 120 leituras, similaridade media 1,00, igualdade exata em 100,0%.
Contagem de `error_code`: nenhum.

### L3 (screenshot + OCR) — `20261112-112535`

| Cenario | Sucesso | Duracao media (s) | Leituras | Exatas | Similaridade media |
|---|---|---|---|---|---|
| C1 | 10/10 | 0,7 | 10 | 0 | 0,00 |
| C2 | 10/10 | 9,1 | 40 | 0 | 0,48 |
| C3 | 10/10 | 13,7 | 20 | 0 | 0,50 |
| C4 | 10/10 | 8,0 | 20 | 0 | 0,54 |
| C5 | 10/10 | 25,8 | 30 | 0 | 0,53 |

Fidelidade global: 120 leituras, similaridade media 0,46, igualdade exata em 0,0%.
Contagem de `error_code`: nenhum.

O sucesso de cada cenario e julgado pelo oraculo (tmux e arquivo de dados), nao pela leitura; por isso L3 passa nos cenarios mesmo sem servir como leitura.

Comparacao com os limiares:

| Metrica | Limiar | L2 | L3 |
|---|---|---|---|
| Cenarios com sucesso >= 9/10 | todos | 5/5 | 5/5 |
| Leituras exatas | >= 95% | 100,0% | 0,0% |

L3 falha o limiar de fidelidade; L2 o atende.

## 5. Fase B (agente de IA)

| Caso | Passou | Contexto final medio (tokens) | Chamadas medias | Duracao media (s) |
|---|---|---|---|---|
| C1 | 3/3 | 90.489 | 6,0 | 43 |
| C2 | 3/3 | 97.577 | 11,0 | 112 |
| C3 | 3/3 | 95.117 | 9,3 | 92 |
| C4 | 3/3 | 97.280 | 11,0 | 107 |
| C5 | 3/3 | 96.941 | 13,7 | 136 |

Medias de custo excluem linhas com NA (interrompidas por limite de uso): 1 repeticao(oes) fora do calculo de tokens e duracao. Limiar: >= 2/3 por caso (atende). Contexto final medio por caso: 95.481 tokens. Isso e o tamanho do contexto do subagente, nao o consumo: o consumo real e o custo estao em CUSTOS.md.

## 6. Hipoteses

| ID | Estado | Evidencia |
|---|---|---|
| H1 leitura do texto | **Parcial** | L1 refutada (no `Terminal` sem texto). L2 confirmada: 100,0% exatas em 120 leituras. L3 inviavel: similaridade 0,46, 0,0% exatas |
| H2 envio de texto e teclas | **Confirmada, com ressalva** | `type`/`press` sem `--headed` ou sem foco nao entregam; com `--headed` e foco, chegam (P5 e Fase A). Entrada fisica |
| H3 agente completa os cenarios | **Confirmada** | 15/15 casos pelo oraculo, em linguagem natural |
| H4 repetibilidade | **Confirmada** | Fase A: 50/50 (L2) e 50/50 (L3), sem `error_code`. Fase B so tem 3 repeticoes por caso |

## 7. Limitacoes e ressalvas

- Leitura so pela area de transferencia (menu Editar do terminal), nao pela arvore de acessibilidade.
- Entrada fisica (`--headed`) depende de foco; sem foco o agent-desktop recusa o envio.
- So display isolado (Xephyr). A sessao real nao foi medida; a sondagem P8 e parcial. Na sessao real a leitura sobrescreve a area de transferencia do usuario.
- So mate-terminal (VTE). O xterm e invisivel ao agent-desktop; outros terminais nao foram testados.
- OCR inviavel no app real: similaridade media 0,46 (0% exatas).
- App de brinquedo em ncurses, nao 3270/5250; nao representa modo bloco nem emulador proprietario.
- Fase B: os subagentes rodaram sem aprovacao manual de comandos e tinham acesso a arquivos com as respostas. Foi proibido por instrucao, sem prova tecnica de que nao leram; o oraculo confirma as acoes, nao a origem dos `claims`.
- Custo da Fase B: contexto final de cerca de 95.000 tokens por caso; o consumo real (centenas de milhares de tokens por repeticao, quase todo leitura de cache) e o custo estimado estao em CUSTOS.md. So 3 repeticoes por caso e um unico agente (D4).
- Ferramenta jovem (1.2.0 fixada); resultados valem para essa versao.

## 8. Onde o resultado se aplica e fase 2

PRD secao 4, tres casos em que o agent-desktop poderia agregar:

- **Emulador sem API de script:** aplica-se, se o emulador expuser acessibilidade (VTE expoe; xterm nao) e tiver menu de copiar. Nao testado com emuladores proprietarios.
- **Fluxo misto com apps graficos:** plausivel (a ferramenta e feita para isso), mas nao medido nesta POC.
- **Ferramenta unica para o desktop:** aplica-se com a ressalva de que o app de terminal e lido por area de transferencia, e a entrada exige foco.
- Para terminal puro sem esses requisitos, tmux/expect continua mais simples, rapido e barato: a Fase A leva segundos por cenario e a Fase B centenas de milhares de tokens por caso (ver CUSTOS.md).

**Fase 2 (recomendacao curta):** repetir com um emulador 3270/5250 real ou proprietario, medir a sessao real com autorizacao, testar um segundo terminal acessivel e um fluxo misto (app grafico + tela verde), e repetir a Fase B com mais repeticoes e outro agente.
