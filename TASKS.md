# TASKS — POC agent-desktop em tela verde

Atualizado em 2026-11-11. Fonte de requisitos: [PRD.md](PRD.md). Como fazer: [SPEC-TECH.md](SPEC-TECH.md). Visão geral: [ARCH.md](ARCH.md). Telas: [SCREENS.md](SCREENS.md). Cenários: [TEST-PLAN.md](TEST-PLAN.md). Ambiente: [SETUP.md](SETUP.md).

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
| T-006 | Decidir D1–D6 do PRD §12 | Respostas registradas no PRD | Igor | Dono do produto | T-001 | DOING (D1–D3 e D5 decididas; D4 e D6 pendentes, vale o padrão) |
| T-007 | Escrever os documentos complementares aprovados: SCREENS.md, TEST-PLAN.md, SETUP.md, AGENTS.md, CLAUDE.md | Arquivos no repositório | devsquad-lead | Liderança técnica | T-006 | DONE |

## F1 — Ambiente

| ID | Tarefa | Pronto quando | Agente | Papel | Depende | Status |
|---|---|---|---|---|---|---|
| T-010 | `git init`, `.gitignore` (`evidence/`, `bin/`, `data/`) e repositório público no GitHub | Primeiro commit com os documentos, publicado | devsquad-devsecops | DevOps | T-006 | DONE |
| T-011 | Instalar `gnucobol3` (exige `sudo`) | `cobc --version` responde | Igor | Dono da máquina | T-006 | TODO |
| T-012 | Fixar a versão do `agent-desktop` | `agent-desktop version` mostra a versão decidida em D2; `status` continua saudável | ubuntu-mate-doc | DevOps | T-006 | DONE |
| T-013 | Ler os guias embutidos (`skills get desktop`, `platform` e referências Linux) e os `--help` dos comandos usados | SPEC §6 e §14 atualizadas com as flags reais | devsquad-architect | Arquitetura | T-012 | DONE |
| T-014 | Script do display isolado (Xephyr + D-Bus + AT-SPI + `marco` + terminal) | `agent-desktop status` e `list-apps` funcionam apontando para o display isolado, ou falha documentada | ubuntu-mate-doc | Infra Linux, desktop MATE | T-012 | DONE |

## F2 — Sondagem de viabilidade

Feita com tela falsa, antes do app COBOL. Cada sondagem grava os envelopes em `evidence/probes/`.

| ID | Tarefa | Pronto quando | Agente | Papel | Depende | Status |
|---|---|---|---|---|---|---|
| T-020 | Tela falsa 80x24 dentro do tmux, em janela com título `CADCLI` | Janela abre e o oráculo (`capture-pane`) devolve as 24 linhas | devsquad-backend | Desenvolvimento | T-012 | DONE |
| T-021 | P2: janela visível e `window-id` localizável pelo título | Resultado registrado | devsquad-qa | QA | T-020 | BLOCKED (sondagem interrompida no limite de uso; retomar) |
| T-022 | P3: o que o `snapshot` mostra; leitura L1 | Resultado e trecho do envelope registrados | devsquad-qa | QA | T-021 | BLOCKED (sondagem interrompida no limite de uso; retomar) |
| T-023 | P4: `type` sem `--headed` (I1) | Código de erro registrado | devsquad-qa | QA | T-021 | BLOCKED (sondagem interrompida no limite de uso; retomar) |
| T-024 | P5: entrada com `--headed` (I2): texto, Enter, Tab, Backspace, F3, F12 | Cada tecla confirmada ou negada pelo oráculo | devsquad-qa | QA | T-021 | BLOCKED (sondagem interrompida no limite de uso; retomar) |
| T-025 | P6: leitura L2 pela área de transferência | Similaridade com o oráculo registrada | devsquad-qa | QA | T-024 | BLOCKED (sondagem interrompida no limite de uso; retomar) |
| T-026 | P7: leitura L3 por `screenshot` + `tesseract` | Similaridade com o oráculo registrada | devsquad-qa | QA | T-021 | BLOCKED (sondagem interrompida no limite de uso; retomar) |
| T-027 | P8: controles — `xterm`, terminal sem tmux, display isolado contra sessão real | Matriz preenchida | devsquad-qa | QA | T-014, T-024 | BLOCKED (sondagem interrompida no limite de uso; retomar) |
| T-028 | **Portão G0:** nota de viabilidade com a matriz estratégia × terminal × display | Igor decide seguir ou encerrar com NO-GO | devsquad-lead | Liderança técnica | T-022 a T-027 | TODO |

## F3 — App CADCLI

| ID | Tarefa | Pronto quando | Agente | Papel | Depende | Status |
|---|---|---|---|---|---|---|
| T-030 | `app/cadcli.cbl`: telas T01–T03, validações, teclas F3 e F12 | Compila sem avisos | devsquad-backend | Desenvolvimento COBOL | T-011, T-028 | TODO |
| T-031 | `app/build.sh`, seed de dados e reset | Um comando compila; um comando restaura o estado inicial | devsquad-backend | Desenvolvimento | T-030 | TODO |
| T-032 | Teste de fumaça manual e telas de referência | As três telas e as cinco mensagens capturadas por `capture-pane` e guardadas em `tests/golden/` | devsquad-qa | QA | T-031 | TODO |

## F4 — Harness

| ID | Tarefa | Pronto quando | Agente | Papel | Depende | Status |
|---|---|---|---|---|---|---|
| T-040 | `ad.py`: executar o `agent-desktop`, interpretar envelope, gravar `steps.jsonl` | Testes unitários de envelope de sucesso e de erro passam | python-senior | Desenvolvimento Python | T-013 | DONE |
| T-041 | `launcher.py`: `env up` e `env down`, descoberta do `window-id` | Ambiente sobe e desce sem processos órfãos | python-senior | Desenvolvimento Python | T-040, T-014 | TODO |
| T-042 | `oracle.py`: tela pelo tmux e conferência de `clientes.dat` | Testes unitários com telas de referência passam | python-senior | Desenvolvimento Python | T-032 | TODO |
| T-043 | `screen.py`: estratégias de leitura viáveis segundo G0, normalização, fidelidade | Testes unitários de normalização e fidelidade passam | python-senior | Desenvolvimento Python | T-040, T-028 | TODO |
| T-044 | `keys.py`: envio de texto e teclas com guarda de foco | Envio abortado quando a janela ativa não é a CADCLI (teste) | python-senior | Desenvolvimento Python | T-040, T-028 | TODO |
| T-045 | `probes.py`: automatizar P2–P8 | `python3 -m harness probe` reproduz a matriz de G0 | python-senior | Desenvolvimento Python | T-043, T-044 | TODO |

## F5 — Fase A (determinística)

| ID | Tarefa | Pronto quando | Agente | Papel | Depende | Status |
|---|---|---|---|---|---|---|
| T-050 | `scenarios.py`: C1–C5 com julgamento pelo oráculo | Cada cenário passa ao menos uma vez | devsquad-qa | QA | T-041 a T-044 | TODO |
| T-051 | Rodar 10 repetições por cenário, por estratégia viável | `summary.json` com taxas de sucesso e fidelidade | devsquad-qa | QA | T-050 | TODO |
| T-052 | Analisar falhas e flakiness por `error.code` | Causas anotadas em "Achados" | devsquad-qa | QA | T-051 | TODO |

## F6 — Fase B (agente de IA)

| ID | Tarefa | Pronto quando | Agente | Papel | Depende | Status |
|---|---|---|---|---|---|---|
| T-060 | Instruções do agente e `cases/C1.md` a `C5.md` | Um agente sem contexto prévio entende o caso só com os arquivos | ai-solution-architect | Arquitetura de IA | T-051 | TODO |
| T-061 | `harness verify` | Julga um caso pelo oráculo, sem depender do agente | python-senior | Desenvolvimento Python | T-042 | TODO |
| T-062 | Rodar os cinco casos com a IA escolhida em D4, 3 repetições, via CLI | Resultados e custo registrados | devsquad-qa | QA | T-060, T-061 | TODO |
| T-063 | Opcional: repetir via MCP ou com uma segunda IA | Resultados registrados | devsquad-qa | QA | T-062 | TODO |

## F7 — Fechamento

| ID | Tarefa | Pronto quando | Agente | Papel | Depende | Status |
|---|---|---|---|---|---|---|
| T-070 | `report.py` e `RESULTS.md` | Matriz de viabilidade, métricas das duas fases, limitações | python-senior | Desenvolvimento Python | T-052, T-062 | TODO |
| T-071 | Revisão de código do app e do harness | Sem achado bloqueante em aberto | devsquad-reviewer | Revisão | T-070 | TODO |
| T-072 | Veredito GO, GO com ressalvas ou NO-GO, e proposta de fase 2 | Seção de veredito no `RESULTS.md`, aprovada por Igor | devsquad-strategy | Estratégia | T-070 | TODO |
| T-073 | Documentação de uso final (README; AGENTS.md com os comandos reais) | Outra pessoa reproduz a POC seguindo o README | devsquad-lead | Liderança técnica | T-071 | TODO |

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
