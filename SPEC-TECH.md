# SPEC-TECH — POC agent-desktop em tela verde

Versão 0.1 · 2026-11-11 · Complementa [PRD.md](PRD.md) e [ARCH.md](ARCH.md). Telas em [SCREENS.md](SCREENS.md), cenários em [TEST-PLAN.md](TEST-PLAN.md), preparação da máquina em [SETUP.md](SETUP.md).

Convenção deste documento: **verificado** significa conferido nesta máquina ou na fonte oficial; **a validar** significa proposta que uma sondagem ou tarefa ainda precisa confirmar. Não trate "a validar" como fato.

## 1. Ambiente (verificado)

| Item | Valor |
|---|---|
| SO | Ubuntu 26.04.1 LTS, x86_64 |
| Sessão gráfica | X11, desktop MATE, gerenciador de janelas `marco`, `DISPLAY=:0` |
| Acessibilidade | `at-spi2-core` 2.60.4, barramento em execução, `toolkit-accessibility=true` |
| `sudo` | Pede senha. Instalações via `apt` são feitas pelo usuário |
| Diretório do projeto | `/opt/projetos/poc-agent-desktop-test-automation`. Repositório público: `github.com/igorferreira/poc-agent-desktop-test-automation` |

## 2. Stack

| Componente | Escolha | Versão | Estado | Motivo |
|---|---|---|---|---|
| Ferramenta sob avaliação | `agent-desktop` (npm, global) | Fixar 1.2.0 | Instalada 1.0.2 | Objeto da POC |
| App de tela verde | GnuCOBOL, `SCREEN SECTION` sobre ncurses | `gnucobol3` 3.2 | **Falta instalar** | COBOL de verdade. `gnucobol4` é snapshot de desenvolvimento: evitar |
| Emulador de terminal alvo | `mate-terminal` (VTE) | do sistema | Instalado | VTE implementa interfaces de acessibilidade; é o terminal nativo do desktop |
| Terminal de controle | `xterm` | do sistema | Instalado | Controle negativo: espera-se que não exponha nada |
| Hospedeiro do app e oráculo | `tmux` | do sistema | Instalado | `capture-pane` dá a tela exata, independente do `agent-desktop` |
| Harness | Python, só biblioteca padrão | 3.12.10 | Instalado | Sem dependências novas |
| Testes do harness | `pytest` | 8.3.5 | Instalado | |
| OCR (estratégia L3) | `tesseract` | do sistema | Instalado | Determinístico, sem LLM |
| Display isolado | `Xephyr` + `dbus-run-session` + `marco` | do sistema | Instalados | Não toma o teclado da sessão real |
| JSON em shell | `jq` | do sistema | Instalado | Inspeção manual de envelopes |
| Agente da Fase B | Qualquer IA com shell ou MCP | — | Claude Code disponível | Requisito RNF1 |

Instalações necessárias:

```bash
sudo apt install -y gnucobol3          # rodado pelo usuário
npm install -g agent-desktop@1.2.0     # decisão D2; não precisa de sudo (npm do nvm)
```

Passo a passo em [SETUP.md](SETUP.md).

Recuo se o GnuCOBOL não puder ser instalado: o mesmo app em Python `curses`, com telas idênticas.

## 3. Estrutura de diretórios

```
.
├── PRD.md  SPEC-TECH.md  ARCH.md  TASKS.md
├── SCREENS.md  TEST-PLAN.md  SETUP.md
├── AGENTS.md  CLAUDE.md    # instruções para agentes de IA
├── app/
│   ├── cadcli.cbl          # fonte do app
│   ├── build.sh            # cobc -> bin/cadcli
│   └── seed/clientes.dat   # estado inicial
├── harness/                # pacote Python (python3 -m harness)
│   ├── __main__.py         # linha de comando
│   ├── ad.py               # wrapper do agent-desktop
│   ├── launcher.py         # sobe e derruba o ambiente
│   ├── screen.py           # leitura: L1, L2, L3
│   ├── keys.py             # entrada: I1, I2, guarda de foco
│   ├── oracle.py           # tmux capture-pane e arquivo de dados
│   ├── probes.py           # sondagens P2-P8
│   ├── scenarios.py        # C1-C5
│   └── report.py           # RESULTS.md
├── tests/                  # pytest do harness
├── cases/                  # casos da Fase B em Markdown
├── evidence/               # fora do git
└── RESULTS.md
```

## 4. App sob teste: CADCLI

Cadastro de clientes em tela 80x24, verde sobre preto.

**Telas**

| Tela | Conteúdo | Entrada |
|---|---|---|
| T01 Menu | Título, opções `1-INCLUIR`, `2-CONSULTAR`, `9-SAIR`, campo `OPCAO` | Dígito + Enter |
| T02 Inclusão | Campos `CODIGO` (6 dígitos), `NOME` (30), `CPF` (11 dígitos, fictício), `CIDADE` (20), `UF` (2) | Tab entre campos, Enter confirma |
| T03 Consulta | Campo `CODIGO`; exibe os dados do cliente | Enter consulta |

**Teclas:** Enter confirma, Tab avança campo, F3 volta ou sai, F12 cancela a edição. F1, F10 e F11 não são usadas porque emuladores e desktops costumam capturá-las.

**Linha 24:** mensagens. `CLIENTE INCLUIDO`, `CODIGO JA CADASTRADO`, `UF INVALIDA`, `CLIENTE NAO ENCONTRADO`, `OPCAO INVALIDA`.

**Layout:** posição exata de cada rótulo, campo e mensagem, comportamento de cada tecla e formato do registro estão no [SCREENS.md](SCREENS.md), que é a fonte de verdade. Em caso de divergência com esta seção, vale o SCREENS.md.

**Dados:** `data/clientes.dat`, `ORGANIZATION LINE SEQUENTIAL`, um cliente por linha em colunas fixas. O app carrega o arquivo em tabela na memória (até 100 registros) e acrescenta ao incluir. Arquivo de texto de propósito: o oráculo confere com uma leitura simples e o reset é copiar `app/seed/clientes.dat`.

**Build e execução (a validar):**

```bash
cobc -x -free -o bin/cadcli app/cadcli.cbl
COB_SCREEN_EXCEPTIONS=Y COB_SCREEN_ESC=Y ./bin/cadcli
```

`COB_SCREEN_EXCEPTIONS=Y` é o que faz o GnuCOBOL devolver teclas de função ao programa via `CRT STATUS` (F3 = 1003, F12 = 1012). Cores: `FOREGROUND-COLOR 2`, `BACKGROUND-COLOR 0`.

## 5. Ambiente de execução

**Cadeia:** emulador de terminal → tmux → CADCLI.

```bash
# a validar
tmux -L cadcli -f /dev/null new-session -d -s cadcli -x 80 -y 24 \
  'COB_SCREEN_EXCEPTIONS=Y COB_SCREEN_ESC=Y ./bin/cadcli'
tmux -L cadcli set -g status off          # tela com 24 linhas exatas
mate-terminal --title=CADCLI --geometry=80x24 -e 'tmux -L cadcli attach -t cadcli'
```

O servidor tmux usa socket próprio (`-L cadcli`) e não lê a configuração do usuário (`-f /dev/null`), para não herdar atalhos nem barra de status.

**Dois modos de display:**

| Modo | Como | Vantagem | Risco |
|---|---|---|---|
| Isolado (padrão) | `Xephyr :2` + `dbus-run-session` + barramento AT-SPI próprio + `marco` + terminal | Não toma o teclado; área de transferência separada; sem atalhos globais | **A validar:** o `agent-desktop` exige sessão gráfica com barramento AT-SPI; pode não aceitar display aninhado |
| Sessão real | `DISPLAY=:0` | Funciona hoje (verificado para `status` e `list-apps`) | Entrada `--headed` toma o teclado; ver seção 11 |

**Identificação da janela:** o usuário tem outros terminais abertos. Nunca usar só `--app mate-terminal`. Obter o `window-id` em `list-windows` filtrando pelo título `CADCLI` e passar `--window-id` em todo comando.

## 6. Contrato com o agent-desktop

Verificado no README e no `--help` da versão 1.0.2:

- Cada comando imprime um envelope JSON: `{"version", "ok", "command", "data"}` ou `error` com `code` e `disposition`.
- Refs pertencem ao snapshot que as criou (`@s8f3k2p9:e8`). Ref solta (`@e8`) dá `INVALID_ARGS`. Se a interface mudou, a ação devolve `STALE_REF` ou `AMBIGUOUS_TARGET`: tirar novo snapshot.
- Repetir um comando só quando `error.disposition.retry` for `safe`.
- Sem `--headed`, ações de ref usam a API de acessibilidade, sem mover ponteiro nem tomar foco. `--headed` libera entrada física.
- `type`, `set-value` e `clipboard-set` aceitam `--stdin`.
- O diretório de estado (`~/.agent-desktop`) precisa ser privado (`chmod 700`), senão `snapshot` falha com `INTERNAL`.
- No Linux, `press` e teclas de texto funcionam em X11; `focus-window` exige X11.

Comandos que a POC usa: `status`, `version`, `list-apps`, `list-windows`, `focus-window`, `snapshot`, `find`, `get`, `type`, `press`, `wait`, `clipboard-get`, `clipboard-clear`, `screenshot`, `session`, `trace`, `skills`.

**Regra para quem implementa:** não inventar flags. Antes de usar um comando, rodar `agent-desktop <comando> --help` na versão fixada. Ler também:

```bash
agent-desktop skills get desktop
agent-desktop skills get platform
agent-desktop skills get agent-desktop-linux references/display-servers-and-input.md
agent-desktop skills get agent-desktop-linux references/capture-and-clipboard.md
agent-desktop skills get agent-desktop-linux references/troubleshooting.md
```

## 7. Estratégias de leitura e de entrada

**Leitura da tela**, em ordem de preferência:

| ID | Estratégia | Estado |
|---|---|---|
| L1 | `snapshot` da janela e `get` de texto ou valor no nó do terminal | **Em risco:** o guia Linux diz que o `value` do nó `Terminal` é nulo. Sondagem P3 decide |
| L2 | Selecionar tudo e copiar no terminal (itens do menu Editar via ref, ou atalho), depois `clipboard-get` | A validar. Na sessão real sobrescreve a área de transferência do usuário |
| L3 | `screenshot` da janela + `tesseract` (Fase A) ou visão do LLM (Fase B) | A validar. Sai do espírito "sem screenshot" da ferramenta |

Fora do `agent-desktop`, só como oráculo e baseline: `tmux capture-pane -p`.

**Entrada**

| ID | Estratégia | Estado |
|---|---|---|
| I1 | `type` em ref, sem `--headed` | Espera-se `POLICY_DENIED` (guia Linux). Registrar o código obtido |
| I2 | `--headed` com `type` para texto e `press` para Enter, Tab, Backspace, F3, F12 | Caminho esperado. Exige foco na janela |

**Normalização para comparar telas:** 24 linhas, remover espaços à direita de cada linha, manter linhas vazias. Fidelidade = igualdade exata; registrar também a razão de similaridade (`difflib.SequenceMatcher`).

**Espera:** depois de cada envio, esperar por condição (`wait` do `agent-desktop` quando L1 funcionar; senão, sondar o oráculo até a tela mudar), com timeout. Nunca `sleep` fixo como sincronização.

## 8. Oráculo

Independente do `agent-desktop` e do agente:

- Tela: `tmux -L cadcli capture-pane -p -t cadcli`.
- Persistência: conteúdo de `data/clientes.dat`.

Cada cenário declara o estado esperado (trecho de tela e, quando couber, linha no arquivo). O oráculo decide aprovado ou reprovado. O que o agente afirma sobre o próprio sucesso é registrado, mas não conta.

## 9. Harness

```bash
python3 -m harness env up [--display isolated|real] [--terminal mate-terminal|xterm]
python3 -m harness env down
python3 -m harness probe [P2 ... P8]
python3 -m harness run [--scenario C3] [--reps 10] [--read L1|L2|L3]
python3 -m harness verify C3        # oráculo para a Fase B
python3 -m harness report           # gera RESULTS.md
```

**Evidência**, em `evidence/<run_id>/`:

- `meta.json`: versão do `agent-desktop`, terminal, display, estratégias, data.
- `steps.jsonl`: uma linha por comando: `ts`, `scenario`, `rep`, `step`, `argv`, `ok`, `error_code`, `duration_ms`.
- `screens/<passo>.read.txt` e `screens/<passo>.oracle.txt`.
- `summary.json`: aprovação por cenário e repetição, fidelidade, contagem de erros.

Antes de cada repetição: restaurar `data/clientes.dat` a partir do seed e reiniciar o app.

## 10. Sondagens (fase F2)

Feitas com uma tela falsa (script que imprime 24 linhas e ecoa teclas, dentro do tmux), antes de escrever o app COBOL.

| ID | Pergunta | Estado |
|---|---|---|
| P1 | `agent-desktop status` saudável? | **Feito:** `accessibility: granted` |
| P2 | A janela do terminal aparece em `list-apps` e `list-windows`, com `window-id` localizável pelo título? | Pendente |
| P3 | O `snapshot` mostra o quê? Algum nó expõe o texto da tela (L1)? | Pendente |
| P4 | `type` sem `--headed` devolve qual erro (I1)? | Pendente |
| P5 | Com `--headed`: texto, Enter, Tab, Backspace, F3 e F12 chegam ao app (I2)? | Pendente |
| P6 | L2 devolve a tela completa pela área de transferência? | Pendente |
| P7 | L3: `screenshot` + `tesseract` atinge que similaridade com o oráculo? | Pendente |
| P8 | Controles: `xterm`; terminal sem tmux; display isolado contra sessão real | Pendente |

Saída: matriz estratégia × terminal × display, e o portão G0 do PRD.

## 11. Segurança e privacidade

Há apps sensíveis abertos na sessão real (gerenciador de senhas, mensageiros, navegador). Regras obrigatórias:

1. Todo comando do `agent-desktop` leva `--window-id` da janela CADCLI. Proibido `snapshot`, `screenshot` ou `find` em outros apps.
2. Antes de cada envio com `--headed`: `focus-window`, confirmar que a janela ativa é a CADCLI e só então enviar. Se a confirmação falhar, abortar a repetição. Uma tecla física vai para a janela que tiver o foco, seja qual for.
3. Na sessão real, a estratégia L2 só roda com autorização explícita, porque sobrescreve a área de transferência.
4. `evidence/` fica fora do git. Envelopes, screenshots e traces podem conter conteúdo do desktop.
5. Só dados sintéticos. Nenhum CPF real.
6. Ninguém reinicia o barramento AT-SPI da sessão do usuário.

## 12. Fase B: agente de IA

- Requisito mínimo do agente: executar comandos de shell, ou conectar a um servidor MCP stdio (`agent-desktop mcp`, uma ferramenta por comando: `desktop_snapshot`, `desktop_press` etc.).
- Entrada do agente: um arquivo `cases/C<n>.md` com objetivo, pré-condição, o que fazer e o que declarar (formato no [TEST-PLAN.md](TEST-PLAN.md), seção 6), mais as regras da seção 11.
- O agente usa a estratégia de leitura e de entrada que a Fase A apontou como viável.
- Saída do agente: `evidence/<run_id>/agent-result.json` com o que fez e o que afirma.
- Julgamento: `python3 -m harness verify C<n>`.
- Registrar: IA e modelo usados, número de chamadas, tempo, tokens quando o agente informar.

## 13. Testes do próprio harness

`pytest` cobre o que não depende de display: leitura do envelope (sucesso e erro), normalização de tela, cálculo de fidelidade, julgamento do oráculo a partir de telas gravadas. As sondagens e os cenários são, eles mesmos, os testes de integração.

## 14. Não verificado

- Flags exatas de cada comando na versão 1.2.0.
- Funcionamento do `agent-desktop` em display Xephyr.
- Nome e atalho dos itens "Selecionar tudo" e "Copiar" no `mate-terminal`.
- Passagem de F3 e F12 pela cadeia terminal → tmux → GnuCOBOL.
- Códigos de `CRT STATUS` no build do GnuCOBOL do Ubuntu.
