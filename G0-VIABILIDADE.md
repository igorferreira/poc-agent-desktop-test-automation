# G0 — Nota de viabilidade

Data: 2026-11-12 · Tarefa T-028 · Base: sondagens P2–P7 (T-021 a T-026) e P8 parcial (T-027), com a tela falsa (`scripts/fake_screen.py`) no display isolado Xephyr `:2`, agent-desktop 1.2.0. Evidência em `evidence/probes/` (fora do git).

**A decisão de seguir ou encerrar é do Igor.**

## Matriz

| Estratégia | mate-terminal | xterm |
|---|---|---|
| L1 — `snapshot`, `get`, `find --text` | Não. Nenhum nó expõe o texto. O nó `Terminal` tem `value` nulo e `get --property text` devolve só o nome "Terminal" | Não. A janela é invisível ao agent-desktop |
| L2 — área de transferência | **Funciona.** `click` semântico em Editar, depois Selecionar tudo e Copiar, depois `clipboard-get`. 6 de 6 leituras exatas (24/24 linhas, similaridade 1,0), cerca de 45 ms, sem `--headed` | Não se aplica |
| L3 — `screenshot` + `tesseract` | Parcial. Similaridade de 0,86 sem tratamento a 0,95 com recorte, ampliação 2x e negativo. Nunca exato: confunde 0/O, 1/I e J/3 | Não testado: sem `window-id`, não há screenshot por janela |
| I1 — `type` sem `--headed` | Não. `POLICY_DENIED` (`supported_action`), `not_delivered`; nada chegou | Não se aplica |
| I2 — `type --headed` no nó `Terminal` | **Funciona.** 3 de 3 | Não se aplica |
| I2 — `press --window-id`, janela focada | **Funciona.** 15 de 15, com e sem `--headed` (`return`, `tab`, `delete`, `f3`, `f12`) | Não se aplica |
| `press`, janela sem foco | Não entrega: `STALE_REF` (`exact_window_focus`) ou `ACTION_FAILED` (`window_active`). Nada é enviado | Não se aplica |
| L2 — mate-terminal **sem tmux** (tela falsa direto no terminal; T-027/T-045, `evidence/probes-20261112-161334/P8b.json`) | **Funciona.** Leitura igual à saída esperada da tela falsa (24/24 linhas, similaridade 1,0). Sem oráculo tmux: a comparação é com a tela determinística da `fake_screen.py` | Não se aplica |

Não feito: qualquer medição na sessão real (exige autorização do Igor).

## Leitura do resultado

- Existe uma estratégia de leitura (L2) e uma de entrada (I2) viáveis. Pelo critério do PRD (§13), **G0 está cumprido**.
- A leitura viável não é pela árvore de acessibilidade do texto, e sim pelos menus do terminal mais a área de transferência. Na sessão real isso sobrescreve a área de transferência do usuário, por isso exige autorização (SPEC §11 regra 3). No display isolado não há esse problema.
- A entrada é física (`delivered_unverified`) e depende do foco. O próprio agent-desktop recusa enviar `press` para janela sem foco, o que reforça a guarda de foco.
- O xterm é inútil para o agent-desktop: o resultado vale para terminais com acessibilidade (VTE).
- Tudo foi medido com a tela falsa. O app COBOL real ainda não foi medido.

## Recomendação

Seguir para F3–F5 com **L2 como leitura principal**, **L3 como apoio** e **I2** como entrada (`type --headed` para texto, `press --window-id` para teclas), sempre no display isolado. Segundo o critério de veredito do PRD §8, este caminho, se passar nos cenários, leva a "GO". Leitura só pela área de transferência é uma ressalva a registrar no relatório.

## Achados que mudam documentos

1. `list-windows` devolve `data` como lista, não `data.windows[]`.
2. `press --app` sem foco não entrega (`ACTION_FAILED`). O achado anterior de T-013 não se confirmou.
3. O `click` semântico abre o menu Editar do mate-terminal sem `--headed`; os itens só ficam clicáveis depois do menu aberto.
4. A sessão D-Bus isolada caiu sozinha uma vez, causa não determinada. Subir o tmux com `setsid` e conferir a sessão antes de cada repetição.
5. `tmux set` logo depois de `new-session` pode falhar; esperar a sessão existir antes de configurá-la.

## Decisão

2026-11-12 — Igor: **seguir**. Igor também autorizou a sondagem de controle P8 na sessão real, com os apps sensíveis fechados e sem uso de teclado e mouse durante a execução.

2026-11-13 — Tentativa da sondagem na sessão real (T-029): bloqueada antes de qualquer envio. O barramento AT-SPI da sessão real recusa conexões (`accessibility: denied`). Reiniciá-lo é decisão do Igor.
