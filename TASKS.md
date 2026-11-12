# TASKS — POC agent-desktop em tela verde

Atualizado em 2026-11-12. Fonte de requisitos: [PRD.md](PRD.md). Como fazer: [SPEC-TECH.md](SPEC-TECH.md). Visão geral: [ARCH.md](ARCH.md). Telas: [SCREENS.md](SCREENS.md). Cenários: [TEST-PLAN.md](TEST-PLAN.md). Ambiente: [SETUP.md](SETUP.md).

**Status:** `TODO` · `DOING` · `DONE` · `BLOCKED` (dizer o motivo) · `SKIP` (dizer o motivo).

**Regras para qualquer IA que pegue uma tarefa:**

1. Ler o [AGENTS.md](AGENTS.md) e os documentos que ele lista, em especial a seção 11 (segurança) do SPEC-TECH, antes de começar.
2. Só pegar tarefa cujas dependências estejam `DONE`.
3. Marcar `DOING` ao começar e `DONE` só quando o critério "Pronto quando" estiver cumprido e verificado. Atualizar este arquivo no mesmo trabalho.
4. Descobriu algo que contradiz a SPEC? Corrigir a SPEC e anotar aqui na seção "Achados".
5. A coluna "Agente" é o subagente do Claude Code indicado. Em outra IA, usar a coluna "Papel".

## F0 — Planejamento

| ID | Tarefa | Pronto quando | Agente | Papel | Depende | Status |
|---|---|---|---|---|---|---|
| T-001 | Escrever PRD.md | Arquivo no repositório | devsquad-po | Produto | — | DONE |
| T-002 | Escrever SPEC-TECH.md | Arquivo no repositório | devsquad-architect | Arquitetura | T-001 | DONE |
| T-003 | Escrever ARCH.md com C4 em Mermaid | Arquivo no repositório | devsquad-architect | Arquitetura | T-001 | DONE |
| T-004 | Escrever TASKS.md | Arquivo no repositório | devsquad-lead | Liderança técnica | T-001 | DONE |
| T-005 | Levantar o ambiente (SO, sessão, ferramentas, AT-SPI, `agent-desktop status`) | Fatos registrados no PRD §11 e SPEC §1 | linux-sys | Infra Linux | — | DONE |
| T-006 | Decidir D1–D6 do PRD §12 | Respostas registradas no PRD | Igor | Dono do produto | T-001 | DOING (D1–D3 e D5 decididas; D4 e D6 seguem o padrão: Claude Code na Fase B, limiares como propostos; falta Igor confirmar) |
| T-007 | Escrever os documentos complementares aprovados: SCREENS.md, TEST-PLAN.md, SETUP.md, AGENTS.md, CLAUDE.md | Arquivos no repositório | devsquad-lead | Liderança técnica | T-006 | DONE |
| T-008 | README.md e LICENSE (MIT) para o repositório público | Arquivos publicados no GitHub | devsquad-lead | Liderança técnica | T-010 | DONE |

## F1 — Ambiente

| ID | Tarefa | Pronto quando | Agente | Papel | Depende | Status |
|---|---|---|---|---|---|---|
| T-010 | `git init`, `.gitignore` (`evidence/`, `bin/`, `data/`) e repositório público no GitHub | Primeiro commit com os documentos, publicado | devsquad-devsecops | DevOps | T-006 | DONE |
| T-011 | Instalar `gnucobol3` (exige `sudo`) | `cobc --version` responde | Igor | Dono da máquina | T-006 | DONE |
| T-012 | Fixar a versão do `agent-desktop` | `agent-desktop version` mostra a versão decidida em D2; `status` continua saudável | ubuntu-mate-doc | DevOps | T-006 | DONE |
| T-013 | Ler os guias embutidos (`skills get desktop`, `platform` e referências Linux) e os `--help` dos comandos usados | SPEC §6 e §14 atualizadas com as flags reais | devsquad-architect | Arquitetura | T-012 | DONE |
| T-014 | Script do display isolado (Xephyr + D-Bus + AT-SPI + `marco` + terminal) | `agent-desktop status` e `list-apps` funcionam apontando para o display isolado, ou falha documentada | ubuntu-mate-doc | Infra Linux, desktop MATE | T-012 | DONE |

## F2 — Sondagem de viabilidade

Feita com tela falsa, antes do app COBOL. Cada sondagem grava os envelopes em `evidence/probes/`.

| ID | Tarefa | Pronto quando | Agente | Papel | Depende | Status |
|---|---|---|---|---|---|---|
| T-020 | Tela falsa 80x24 dentro do tmux, em janela com título `CADCLI` | Janela abre e o oráculo (`capture-pane`) devolve as 24 linhas | devsquad-backend | Desenvolvimento | T-012 | DONE |
| T-021 | P2: janela visível e `window-id` localizável pelo título | Resultado registrado | devsquad-qa | QA | T-020 | DONE |
| T-022 | P3: o que o `snapshot` mostra; leitura L1 | Resultado e trecho do envelope registrados | devsquad-qa | QA | T-021 | DONE |
| T-023 | P4: `type` sem `--headed` (I1) | Código de erro registrado | devsquad-qa | QA | T-021 | DONE |
| T-024 | P5: entrada com `--headed` (I2): texto, Enter, Tab, Backspace, F3, F12 | Cada tecla confirmada ou negada pelo oráculo | devsquad-qa | QA | T-021 | DONE |
| T-025 | P6: leitura L2 pela área de transferência | Similaridade com o oráculo registrada | devsquad-qa | QA | T-024 | DONE |
| T-026 | P7: leitura L3 por `screenshot` + `tesseract` | Similaridade com o oráculo registrada | devsquad-qa | QA | T-021 | DONE |
| T-027 | P8: controles — `xterm`, terminal sem tmux, display isolado contra sessão real | Matriz preenchida | devsquad-qa | QA | T-014, T-024 | DONE (xterm e sem tmux feitos; sessão real separada na T-029) |
| T-029 | P8 na sessão real (`DISPLAY=:0`): leitura L2 e entrada I2 com a guarda de foco | Resultado registrado no G0-VIABILIDADE.md e no RESULTS.md | devsquad-qa | QA | T-027 | BLOCKED (autorizada por Igor; espera ele fechar gerenciador de senhas e mensageiros e avisar "pronto") |
| T-028 | **Portão G0:** nota de viabilidade com a matriz estratégia × terminal × display | Igor decide seguir ou encerrar com NO-GO | devsquad-lead | Liderança técnica | T-022 a T-027 | DONE (Igor: seguir, 2026-11-12) |

## F3 — App CADCLI

| ID | Tarefa | Pronto quando | Agente | Papel | Depende | Status |
|---|---|---|---|---|---|---|
| T-030 | `app/cadcli.cbl`: telas T01–T03, validações, teclas F3 e F12 | Compila sem avisos | devsquad-backend | Desenvolvimento COBOL | T-011, T-028 | DONE |
| T-031 | `app/build.sh`, seed de dados e reset | Um comando compila; um comando restaura o estado inicial | devsquad-backend | Desenvolvimento | T-030 | DONE |
| T-032 | Teste de fumaça manual e telas de referência | As três telas e as cinco mensagens capturadas por `capture-pane` e guardadas em `tests/golden/` | devsquad-qa | QA | T-031 | DONE |

## F4 — Harness

| ID | Tarefa | Pronto quando | Agente | Papel | Depende | Status |
|---|---|---|---|---|---|---|
| T-040 | `ad.py`: executar o `agent-desktop`, interpretar envelope, gravar `steps.jsonl` | Testes unitários de envelope de sucesso e de erro passam | python-senior | Desenvolvimento Python | T-013 | DONE |
| T-041 | `launcher.py`: `env up` e `env down`, descoberta do `window-id` | Ambiente sobe e desce sem processos órfãos | python-senior | Desenvolvimento Python | T-040, T-014 | DONE |
| T-042 | `oracle.py`: tela pelo tmux e conferência de `clientes.dat` | Testes unitários com telas de referência passam | python-senior | Desenvolvimento Python | T-032 | DONE |
| T-043 | `screen.py`: estratégias de leitura viáveis segundo G0, normalização, fidelidade | Testes unitários de normalização e fidelidade passam | python-senior | Desenvolvimento Python | T-040, T-028 | DONE |
| T-044 | `keys.py`: envio de texto e teclas com guarda de foco | Envio abortado quando a janela ativa não é a CADCLI (teste) | python-senior | Desenvolvimento Python | T-040, T-028 | DONE |
| T-045 | `probes.py`: automatizar P2–P8 | `python3 -m harness probe` reproduz a matriz de G0 | python-senior | Desenvolvimento Python | T-043, T-044 | DONE |
| T-046 | `scripts/ad2.sh`: guarda que recusa rodar o agent-desktop fora do display isolado | Recusa com `DISPLAY` diferente de `:2` ou D-Bus da sessão real | devsquad-qa | QA | T-014 | DONE |

## F5 — Fase A (determinística)

| ID | Tarefa | Pronto quando | Agente | Papel | Depende | Status |
|---|---|---|---|---|---|---|
| T-050 | `scenarios.py`: C1–C5 com julgamento pelo oráculo | Cada cenário passa ao menos uma vez | devsquad-qa | QA | T-041 a T-044 | DONE |
| T-051 | Rodar 10 repetições por cenário, por estratégia viável | `summary.json` com taxas de sucesso e fidelidade | devsquad-qa | QA | T-050 | DONE |
| T-052 | Analisar falhas e flakiness por `error.code` | Causas anotadas em "Achados" | devsquad-qa | QA | T-051 | DONE (nenhuma falha nem erro em 100 execuções) |

## F6 — Fase B (agente de IA)

| ID | Tarefa | Pronto quando | Agente | Papel | Depende | Status |
|---|---|---|---|---|---|---|
| T-060 | Instruções do agente e `cases/C1.md` a `C5.md` | Um agente sem contexto prévio entende o caso só com os arquivos | ai-solution-architect | Arquitetura de IA | T-051 | DONE (validação real na T-062) |
| T-061 | `harness verify` | Julga um caso pelo oráculo, sem depender do agente | python-senior | Desenvolvimento Python | T-042 | DONE |
| T-062 | Rodar os cinco casos com a IA escolhida em D4, 3 repetições, via CLI | Resultados e custo registrados | devsquad-qa | QA | T-060, T-061 | DONE |
| T-063 | Opcional: repetir via MCP ou com uma segunda IA | Resultados registrados | devsquad-qa | QA | T-062 | SKIP (opcional; não pedido) |
| T-064 | Revisar `cases/AGENT.md` e `cases/OPERADOR.md` com o que os agentes da T-062 relataram | Ambiguidades da T-062 resolvidas no texto | ai-solution-architect | Arquitetura de IA | T-062 | DONE (não revalidado com nova execução) |

## F7 — Fechamento

| ID | Tarefa | Pronto quando | Agente | Papel | Depende | Status |
|---|---|---|---|---|---|---|
| T-070 | `report.py` e `RESULTS.md` | Matriz de viabilidade, métricas das duas fases, limitações | python-senior | Desenvolvimento Python | T-052, T-062 | DONE |
| T-071 | Revisão de código do app e do harness | Sem achado bloqueante em aberto | devsquad-reviewer | Revisão | T-070 | DONE (aprovado; 2 bloqueantes corrigidos) |
| T-072 | Veredito GO, GO com ressalvas ou NO-GO, e proposta de fase 2 | Seção de veredito no `RESULTS.md`, aprovada por Igor | devsquad-strategy | Estratégia | T-070 | TODO |
| T-073 | Documentação de uso final (README; AGENTS.md com os comandos reais) | Outra pessoa reproduz a POC seguindo o README | devsquad-lead | Liderança técnica | T-071 | DOING |
| T-074 | `CUSTOS.md`: consumo de tokens e custo estimado de toda a POC, a partir dos registros da sessão | Tabelas por modelo, grupo, subagente e caso, com premissas e scripts para refazer | devsquad-lead | Liderança técnica | T-062 | DONE |
| T-075 | Revisão de texto do `RESULTS.md` (o gerador escreve sem acentos) | `harness/report.py` gera texto acentuado | python-senior | Desenvolvimento Python | T-070 | DONE |
| T-077 | Achados não bloqueantes da revisão T-071 (lista em "Achados", 2026-11-12) | Cada item corrigido ou aceito com justificativa | python-senior | Desenvolvimento Python | T-071 | TODO |
| T-076 | Atualizar `CUSTOS.md` com o consumo das tarefas de fechamento (T-071 a T-073) | Fotografia final do custo | devsquad-lead | Liderança técnica | T-073 | TODO |

## Achados

Registrar aqui, com data, o que a execução descobrir e que mude o plano.

- 2026-11-11 — `agent-desktop` já estava instalado na versão 1.0.2; o npm publica 1.2.0.
- 2026-11-11 — `status` saudável e `list-apps` funcional no MATE, que não é o desktop medido pela ferramenta (GNOME).
- 2026-11-11 — O guia Linux embutido (1.0.2) afirma: nó de terminal é `textfield` `Terminal`, `value` nulo, `type` sem `--headed` recusado com `POLICY_DENIED`. Isso torna T-022 e T-024 as tarefas que decidem a POC.
- 2026-11-11 — `sudo` pede senha: T-011 fica com Igor.
- 2026-11-11 — `npm view agent-desktop time`: pacote no npm desde 23/02/2026; 1.0.0 em 28/10; 1.2.0 em 05/11. Cinco versões em oito dias reforçam a fixação de versão (T-012).
- 2026-11-11 — O npm global fica no nvm do usuário: T-012 não precisa de `sudo`. `~/.agent-desktop` ainda não existe; aplicar `chmod 700` quando for criado.
- 2026-11-11 — `mate-terminal` reaproveita o processo já aberto. No display isolado é preciso `--disable-factory` (T-014).
- 2026-11-11 — `at-spi-bus-launcher` aceita `--launch-immediately` e `--a11y=0|1`: base da receita do display isolado no SETUP.md, ainda não testada.
- 2026-11-12 — T-012: `npm install -g agent-desktop@1.2.0` não rodou o `postinstall`; a CLI funciona pelo launcher Node, com cerca de 125 ms a mais por chamada. Linkar o binário nativo exige `--allow-scripts=agent-desktop` (não feito).
- 2026-11-12 — T-014: display isolado funciona com `mate-terminal`: `list-apps` mostra só `mate-terminal` e `marco` do `:2`. O `window-id` muda a cada subida; ler sempre de `list-windows`.
- 2026-11-12 — T-014: `xterm` não expõe AT-SPI. A janela existe no X, mas `list-windows` devolve `[]`. Serve só como controle negativo e para o oráculo.
- 2026-11-12 — T-014: se a sessão D-Bus isolada cai, `list-apps` falha com `PLATFORM_NOT_SUPPORTED`. Por isso o tmux é iniciado com `setsid`.
- 2026-11-12 — T-020: F3 e F12 chegam pelo tmux 3.6 e o `curses` com `keypad` decodifica sem tratamento manual. Backspace chega como 127, 8 ou `KEY_BACKSPACE`, conforme o terminal.
- 2026-11-12 — T-013: o agente leu os guias de dentro do binário 1.2.0 e as flags do fonte no GitHub (marcas [G] e [F] no SPEC §6). O `--help` da 1.2.0 confirmou as flags de `press`, `type`, `focus-window`, `list-windows`, `screenshot`, `snapshot`, `get`, `wait` e `clipboard-get`. `list-windows` não filtra por título: filtrar o JSON por `CADCLI` com `--app mate-terminal`. Teclas do `press`: `return`, `tab`, `delete` (Backspace), `f3`, `f12`.
- 2026-11-12 — T-013: `press --app` manda teclas ao processo sem focar a janela (`--headed` foca antes). `type` exige ref; o nó `Terminal` segue com `value` nulo segundo o guia 1.2.0.
- 2026-11-12 — T-040: `retry_safe` só aceita repetir com `disposition.retry == "safe"` e `delivery == "not_delivered"` (guia `skills get desktop`, seção "Delivery and retry").
- 2026-11-12 — `tests/test_fake_screen.py` sobe e derruba a mesma sessão `tmux -L cadcli` usada pelas sondagens. Não rodar esse teste durante uma sondagem ou execução de cenário.
- 2026-11-12 — F2: L1 inviável (nó `Terminal` sem texto); L2 pela área de transferência 6/6 exata; L3 até 0,95 de similaridade, nunca exata; I1 `POLICY_DENIED`; I2 15/15 por tecla. Detalhes em [G0-VIABILIDADE.md](G0-VIABILIDADE.md).
- 2026-11-12 — F2: `press --app` sem foco não entrega (`ACTION_FAILED`, `window_active`). Corrige o achado de T-013.
- 2026-11-12 — F2: `list-windows` devolve `data` como lista. A sessão D-Bus isolada caiu sozinha uma vez; causa não determinada.
- 2026-11-12 — F3: CADCLI compila sem aviso de código. O `cobc` da distro gera `_FORTIFY_SOURCE redefined`, silenciado em `app/build.sh`. `CRT STATUS`: Enter 0000, F3 1003, F12 1012. C1–C5 passaram à mão via `tmux send-keys`.
- 2026-11-12 — F3: campo numérico vazio mostra zeros (`000000`), não `_`. Ao repintar depois de um erro, espaço dentro de campo preenchido aparece como `_` (`UF_ERRADA`): o oráculo não deve comparar NOME literal em tela de erro. Mensagem extra `CADASTRO CHEIO` (100 registros), não testada.
- 2026-11-12 — F4: causa da "queda sozinha" da sessão isolada: a tela falsa morria com `curses.error` quando o terminal anexava e o pane ficava menor que 24 linhas. O launcher agora fixa `window-size manual` e `resize-window -x 80 -y 24`. Com `status` do tmux ligado, a leitura L2 perde a primeira linha.
- 2026-11-12 — F4: leitura L2 completa (menus e `clipboard-get`) leva cerca de 1,8 s; os 45 ms do G0 eram só o `clipboard-get`. Integração com a tela falsa: L2 exata (24/24). L3: similaridade 0,86, 0 linhas iguais, porque o `tesseract` descarta linhas vazias e espaços duplos.
- 2026-11-12 — T-060: o agente da Fase B não deve dar `source` no env do display: `scripts/ad2.sh` compara o D-Bus herdado com o do display e recusaria. As respostas dos `claims` estão em SCREENS.md, TEST-PLAN.md e `harness/`; `cases/AGENT.md` proíbe ler esses arquivos, mas só a disciplina do agente garante isso. O estado final no oráculo continua sendo a prova das ações.
- 2026-11-12 — T-060: se a leitura L2 falhar no meio, o menu Editar pode ficar aberto e capturar a próxima tecla. `cases/AGENT.md` proíbe enviar tecla antes de uma leitura completa.
- 2026-11-12 — Fase A, L2 (`evidence/20261112-113612`): C1–C5 10/10 cada; 120 leituras, 100% exatas; nenhum `error_code`. Duração média: C1 1,9 s, C2 13,7 s, C3 15,7 s, C4 10,1 s, C5 28,6 s.
- 2026-11-12 — Fase A, L3 (`evidence/20261112-112535`): C1–C5 10/10 cada (o julgamento é pelo oráculo); 120 leituras, similaridade média 0,46, 0% exatas. No app COBOL o OCR é muito pior que na tela falsa (0,86): L3 não serve como leitura.
- 2026-11-12 — Fase B (T-062), Claude Code como subagente sem contexto, 3 repetições por caso: 15/15 passaram no `verify` (estado do oráculo e `claims`). Custo por repetição: 90–99 mil tokens do subagente, 5–14 chamadas de ferramenta, 40–139 s. Registro em `evidence/phase-b-ledger.tsv`. A C5 r3 foi interrompida por limite de uso da API e retomada; tempo e tokens dela não contam.
- 2026-11-12 — Fase B: os subagentes rodaram comandos sem aprovação manual do operador (o `OPERADOR.md` previa aprovar cada um). Nenhum relatou leitura fora do permitido; o oráculo confirma o estado, mas não prova que o agente não leu arquivos proibidos.
- 2026-11-12 — T-074: o número "tokens do subagente" que o Claude Code mostra ao fim de cada subagente (cerca de 95 mil na Fase B) é o tamanho do contexto final, não o consumo. O consumo real, somado pelos registros da sessão, foi de 400 mil a 1,3 milhão de tokens por repetição da Fase B. `RESULTS.md` corrigido. Total da POC até 19:07 UTC: 54,9 milhões de tokens, cerca de US$ 44,80 em preço de API (detalhes em CUSTOS.md).
- 2026-11-12 — T-074: os subagentes `devsquad-*`, `python-senior` e `ubuntu-mate-doc` rodaram em `claude-sonnet-5-5`, pela definição de cada agente; os `general-purpose` e `ai-solution-architect`, em `claude-opus-5-5`.
- 2026-11-12 — T-045: `python3 -m harness probe` reproduziu a matriz do G0 sem divergência (P2–P8a). P8b, mate-terminal sem tmux: L2 exata (24/24) contra a saída esperada da tela falsa. P7 desta vez: 0,912. Uma execução só, sem medida de flakiness. Suíte completa: 27 testes passam, mais o de integração com display.
- 2026-11-12 — T-071, corrigidos: (1) `harness/ad.py` `build_env` só conferia `DISPLAY`; um arquivo de ambiente sem D-Bus herdaria o barramento da sessão real. Agora exige D-Bus próprio e remove `AT_SPI_BUS_ADDRESS`. (2) `scripts/display-down.sh` matava PIDs do arquivo sem validar; agora confere o nome do processo. Conferido com `env up`/`env down` e o teste de integração: sem processo órfão. (3) `.claude/` no `.gitignore`. (4) `report.py`: fidelidade abaixo do limiar agora dá NO-GO, como no PRD §8 (antes dava "GO com ressalvas").
- 2026-11-12 — T-071, não corrigidos (T-077): frases fixas do `report.py` que não acompanham os dados; execuções padrão fixas no `report.py`; no C2, app que cai também passa como "saiu"; `check_claims` tolerante demais em C1; `convert` e `tesseract` sem timeout; `sleep 0.5` no `display-up.sh`; no COBOL, tecla fora de F3/F12 (ex.: ESC) tenta gravar.
