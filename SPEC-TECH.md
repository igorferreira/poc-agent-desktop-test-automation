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

Conferido em 2026-11-12 contra a versão 1.2.0 (pacote global `package.json` = 1.2.0). Fontes e o que cada marca significa:

- **[G]** guia embutido no binário 1.2.0 (`skills get desktop`, `platform` e referências do Linux; lido direto do arquivo `bin/agent-desktop-linux-x64` do pacote, sem executar nada). Conta como verificado.
- **[F]** definição de flags no código-fonte do ramo `main` do repositório (`src/cli_args/*.rs`). Pode ser posterior à 1.2.0. **Não executei `--help`** (T-013 sem shell): conferir cada linha de comando com `agent-desktop <comando> --help` antes de usar, uma vez, na primeira sondagem.

O CHANGELOG da 1.2.0 não lista mudança de Linux, de `press`, `screenshot`, `wait` nem de terminal desde a 1.0.2. Mudanças que importam: envelope passou a 2.6 e refs de controles idênticos podem dar `AMBIGUOUS_TARGET` (1.1.0); `type --interval-ms` (1.1.0); `--stdin` em `type`, `set-value` e `clipboard-set` e o comando `mcp` (1.2.0).

### 6.1 Regras gerais

- [G] Cada comando imprime um envelope JSON com `ok` e `data`, ou `error` com `code`, `message`, `suggestion` e às vezes `details`, `recovery`, `disposition`. Código de saída: 0 sucesso, 1 erro estruturado, 2 erro de argumento. O campo `version` do envelope é a versão do esquema (2.6), não a da ferramenta. Ignorar chaves desconhecidas.
- [G] `disposition` tem `delivery` e `retry`. Ação bem-sucedida: `data.disposition` (`delivered_verified` ou `delivered_unverified`) e `data.steps` (cada mecanismo tentado, `semantic_api` ou `physical_synthetic`). Erro: `error.disposition`. **Só `not_delivered` é seguro repetir** (`retry: safe`). Qualquer outro valor: ler o estado antes de decidir. Comandos de observação não têm `disposition` no sucesso; seus erros e todo `INVALID_ARGS` trazem `not_delivered` e `safe`.
- [G] Refs são qualificadas (`@s8f3k2p9:e8`) e valem para o snapshot que as criou. Ref solta (`@e8`) dá `INVALID_ARGS`. `STALE_REF`: tirar novo snapshot. `AMBIGUOUS_TARGET`: controles idênticos, repetir não adianta.
- [G] Sem `--headed`, ações de ref são semânticas (AT-SPI), sem mover ponteiro nem trocar a janela ativa. `--headed` é flag global (`agent-desktop --headed type ...`) e libera entrada física: no X11 usa XTEST e fica `physical_synthetic`, `verified: false`.
- [G] `press` é sempre entrada física de teclado, com ou sem `--headed`.
- [G] No X11 não há dependência externa (`xdotool`, `xclip`, `wmctrl` não são usados). A ferramenta lê `WAYLAND_DISPLAY`, `DISPLAY` e `XDG_RUNTIME_DIR`.
- [G] Estado em `~/.agent-desktop` (ou `AGENT_DESKTOP_HOME`, caminho absoluto) precisa ser privado (`chmod 700`), senão `snapshot` falha com `INTERNAL`. O lock de entrada fica em `/tmp/agent-desktop-<uid>/` e serializa entrada por usuário (`TIMEOUT` com `lock_timeout`: outro agente está digitando).
- [G] `window-id` tem a forma `w-<id>`, é opaco e deixa de valer quando o processo do app reinicia: rodar `list-windows` de novo depois de reiniciar o terminal.
- [G] Barramento privado, sem tocar o da sessão: `XDG_RUNTIME_DIR=$(mktemp -d) dbus-run-session -- agent-desktop status`. O guia diz para nunca reiniciar o barramento de quem não é seu.

### 6.2 Comandos e flags

| Comando | Forma verificada | Fonte |
|---|---|---|
| `status` | `agent-desktop status`. Mostra plataforma, permissões, `supported_surfaces` (vazio = barramento AT-SPI não respondeu), `state_root` | G |
| `version` | `agent-desktop version` | G |
| `skills` | `skills`, `skills get <nome> [referência] [--full]`, `skills path`. Nomes: `desktop`, `platform`, `linux`, `ffi`, `jev`; referência como `references/capture-and-clipboard.md` ou só o nome base | G, F |
| `list-apps` | `list-apps [--app NOME] [--timeout-ms MS]`. Os nomes que imprime são os aceitos em `--app` | G, F |
| `list-windows` | `list-windows [--app NOME] [--timeout-ms MS]`. `--app` é igualdade exata sem diferenciar caixa. **Não há filtro por título**: filtrar o JSON. Linhas: `id`, `title`, `app_name`, `pid`, `bounds`, `is_focused`, `accessible` (e no Linux `visible`). A focada vem primeiro | G, F |
| `focus-window` | `focus-window [--window-id ID] [--app NOME] [--title TEXTO]` (título por trecho). Exige ao menos um. Só vale se `_NET_ACTIVE_WINDOW` nomeia a janela e o app a reporta ativa; senão `ACTION_FAILED` | G, F |
| `snapshot` | `snapshot [--app NOME] [--window-id ID] [-i] [--compact] [--skeleton] [--root REF] [--surface S] [--max-depth N] [--timeout-ms MS] [--include-bounds]`. Confira `data.complete`. Com `--app` sem `--window-id` e mais de uma janela: `AMBIGUOUS_TARGET` | G, F |
| `find` | `find [--app] [--window-id] [--role R] [--name N] [--value V] [--text T] [--exact] [--root REF] [--first\|--last\|--nth N\|--limit N\|--count] [--timeout-ms MS]`. `textarea`, `textbox` e `searchfield` viram `textfield`. Se o filtro de papel não casa, `data.roles_present` lista os papéis da árvore | G, F |
| `get` | `get REF [--property text\|value\|title\|bounds\|role\|states]`; padrão `text`. Valor ausente: `null` | G, F |
| `type` | `type REF TEXTO [--timeout-ms MS] [--interval-ms MS]` e `type REF --stdin` (até 10.000 bytes). **A ref é obrigatória**: não há `type` sem ref | G, F |
| `press` | `press COMBO [--app NOME] [--window-id ID] [--force]`. Sem `--app` nem `--window-id`, vai para a janela em foco | G, F |
| `wait` | `wait MS`; `wait --element REF --predicate exists\|enabled\|visible\|actionable\|value [--value V] [--action click\|type\|set-value\|clear]`; `wait --window TÍTULO [--app]`; `wait --text TEXTO [--app] [--count N]`; `wait --menu`; `wait --event window-opened\|window-closed\|app-launched\|app-terminated\|focus-changed\|surface-appeared\|surface-dismissed [--app] [--window-id]`; `--timeout MS` (padrão 30000) | G, F |
| `clipboard-get` | `clipboard-get [--format text\|auto\|image\|file-urls] [--out CAMINHO]`. Texto: `{"type":"text","text":...}`; vazio: `{"type":"text","found":false}` | G, F |
| `clipboard-set` | `clipboard-set TEXTO` ou `clipboard-set --stdin` (até 128 KiB) | G, F |
| `clipboard-clear` | `clipboard-clear`. No X11 encerra o processo auxiliar dono da seleção | G |
| `screenshot` | `screenshot [--app NOME] [--window-id ID] [--screen N] [CAMINHO]`. Com `CAMINHO` grava o PNG; sem ele devolve base64 em `data`. Não há flag de tempo limite | G, F |
| `session` | `session start [--name N] [--no-trace] [--screenshots]`, `session end [ID]`, `session list`, `session gc [--older-than S] [--ended]`. Ativar em outros comandos com `--session ID` ou `AGENT_DESKTOP_SESSION`. `--screenshots` grava PNG sem redação | G, F |
| `trace` | `trace show [--limit N] [--event PREFIXO]`, `trace export [--out ARQ.html] [--limit N]`. Flags globais `--trace CAMINHO` e `--trace-strict`. Campos sensíveis (`text`, `value`, `name`, `title`) saem como `{"redacted":true}` | G, F |
| `mcp` | `agent-desktop mcp` serve cada comando como ferramenta MCP por stdio (`desktop_snapshot`, `desktop_press`...). Flags globais dadas a `mcp` (`--session`, `--headed`, `--trace`) valem para toda chamada. Novo na 1.2.0 | G |

Flags globais: `--headed`, `--session ID`, `--agent-id`, `--trace`, `--trace-strict`, `-w/--wait-for "papel:texto"`, `--wait-for-gone`, `--wait-timeout MS` (padrão 30000). `--wait-for` só vale em `snapshot`, `press` e ações de ref.

### 6.3 Teclas do `press`

[G] Nomes no Linux: `return` (Enter), `tab`, `delete` (**é Backspace**), `forwarddelete` (tecla Delete), `escape`, `space`, `home`, `pageup`, `f1` a `f24`, `up`, `down`, `left`, `right`. Caractere único é a própria tecla. Letra maiúscula sozinha vira `shift+minúscula`. Modificadores: `ctrl`, `alt`, `shift`, `meta`/`super`. Nome desconhecido: `INVALID_ARGS` com a lista aceita, nada enviado.

| Tecla do CADCLI | Argumento de `press` |
|---|---|
| Enter | `return` |
| Tab | `tab` |
| Backspace | `delete` |
| F3 | `f3` |
| F12 | `f12` |

Combinações bloqueadas com `POLICY_DENIED` (só passam com `--force`): `alt+f4`, `alt+tab`, `alt+f2`, `meta+l`, `meta+d`, `meta+tab`, `super` sozinha, `ctrl+alt+t`, `ctrl+alt+delete`, `ctrl+alt+backspace`, `ctrl+alt+l`, `ctrl+alt+f1` a `f12`. Nenhuma das teclas do CADCLI está na lista. `ctrl+shift+a` e `ctrl+shift+c` (L2) não estão na lista. Nunca usar `--force` na POC.

### 6.4 Terminal na árvore (continua sem texto)

[G] O nó do terminal é `textfield` de nome `Terminal`, com só a ação `RightClick`, e o `value` é `null`. O guia diz literalmente que a ref não lê a saída do terminal e manda verificar o efeito por arquivo ou outro app. `type` sem `--headed` nesse nó dá `POLICY_DENIED` (check `supported_action`); o nó só recebe teclas com `--headed`. Isso é igual ao que o guia 1.0.2 dizia: a 1.2.0 não mudou nada aqui. L1 segue em risco; só a sondagem P3 mostra se algum outro nó da árvore do mate-terminal expõe o texto.

### 6.5 Entrada: o que o guia garante

- [G] `type REF TEXTO` com `--headed` manda teclas físicas (XTEST no X11). Exige a janela `active` e o alvo (ou seu editor interno comprovado) com foco; sem foco: `ACTION_FAILED` com `check: target_focus` ou `window_active`, e `physical_delivery_started: false` quer dizer que nada foi enviado.
- [G] No X11, `type` físico **recusa caractere de controle, inclusive Tab e nova linha**, antes de enviar qualquer coisa. Enter e Tab sempre por `press return` e `press tab`.
- [G] `press` sem ref funciona direto na janela em foco. Escopado sem `--headed` (`--app` ou `--window-id`), só entrega se o alvo já tem o foco; com `--window-id` exige o foco exato daquela janela e, se não confirma, devolve `STALE_REF` com `check: exact_window_focus`, sem enviar tecla. Com `--headed` e `--app` ou `--window-id`, no X11, a ferramenta ativa a janela e envia.
- [G] `press` sempre reporta `delivered_unverified`: entrega não prova efeito. Verificar pelo oráculo.
- [G] Janela em outra área de trabalho: `focus-window` troca a área de trabalho do usuário. Na sessão real isso é efeito visível.

### 6.6 Linhas de comando por uso da POC

`$W` = `window-id` da janela CADCLI, `$T` = ref do nó `Terminal` de um snapshot recente. Todas assumem `agent-desktop` 1.2.0; trocar por `npx -y agent-desktop@1.2.0` se a global não for 1.2.0.

```bash
# janela CADCLI (P2). Nunca list-windows sem --app: lista título de janelas de outros apps
W=$(agent-desktop list-windows --app mate-terminal \
  | jq -r '.data[] | select(.title == "CADCLI") | .id')   # verificado em P2: data é uma lista

# foco e guarda (G): confirmar que a ativa é a CADCLI antes de cada envio --headed
agent-desktop focus-window --window-id "$W"
agent-desktop list-windows --app mate-terminal | jq -e --arg w "$W" \
  '.data[] | select(.id == $w) | .is_focused'   # abortar se não for true

# L1: leitura por árvore (P3)
agent-desktop snapshot --window-id "$W" -i --compact
agent-desktop find --window-id "$W" --role textfield --name Terminal --first   # devolve a ref $T
agent-desktop get "$T" --property text      # esperado null (ver 6.4)
agent-desktop get "$T" --property value

# L2: selecionar tudo + copiar + ler (P6). Atalhos do mate-terminal a confirmar
agent-desktop --headed press ctrl+shift+a --window-id "$W"
agent-desktop --headed press ctrl+shift+c --window-id "$W"
agent-desktop clipboard-get --format text
agent-desktop clipboard-clear

# L3: captura da janela + OCR (P7)
agent-desktop screenshot --window-id "$W" evidence/<run_id>/screens/<passo>.png
tesseract evidence/<run_id>/screens/<passo>.png stdout --psm 6

# I1: sem --headed (P4). Esperado POLICY_DENIED, check supported_action
agent-desktop type "$T" "1"

# I2: com --headed (P5)
agent-desktop --headed type "$T" "000123"      # texto sem Tab nem nova linha
agent-desktop --headed press tab    --window-id "$W"
agent-desktop --headed press return --window-id "$W"
agent-desktop --headed press delete --window-id "$W"   # Backspace
agent-desktop --headed press f3     --window-id "$W"
agent-desktop --headed press f12    --window-id "$W"
# I2b, sem ref: um caractere por press (letra maiúscula sai como shift+letra, espaço é "space")
agent-desktop --headed press 1 --window-id "$W"

# espera (G): por texto só se L1 funcionar; senão sondar o oráculo
agent-desktop wait --text "CLIENTE INCLUIDO" --window-id "$W" --timeout 5000   # --window-id em wait --text: a confirmar; hoje documentado só com --app
agent-desktop wait --event window-opened --app mate-terminal --timeout 10000

# sessão e rastro
agent-desktop session start --name poc
agent-desktop --session "$SID" trace show --limit 50
```

Cada linha acima segue os guias [G] ou o fonte [F]; o encaixe `--headed press ... --window-id` e o formato exato do JSON de `list-windows` ainda não foram executados.

**Regra para quem implementa:** não inventar flags. Antes de usar um comando, rodar `agent-desktop <comando> --help` na versão fixada (as marcas [F] acima são o que mais precisa dessa conferência). Ler também:

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
| L2 | Selecionar tudo e copiar no terminal (itens do menu Editar via ref, ou `press ctrl+shift+a` e `ctrl+shift+c`), depois `clipboard-get` | A validar. Na sessão real sobrescreve a área de transferência do usuário. Nenhum comando novo da 1.2.0 faz isso por conta própria |
| L3 | `screenshot --window-id $W CAMINHO` + `tesseract` (Fase A) ou visão do LLM (Fase B) | A validar. Sai do espírito "sem screenshot" da ferramenta. Com gerenciador sem composição (o `marco` pode estar assim), janela coberta falha com `ACTION_FAILED` `reason: covered`: focar antes. Gerenciador com composição captura coberta e minimizada |

Fora do `agent-desktop`, só como oráculo e baseline: `tmux capture-pane -p`.

**Entrada**

| ID | Estratégia | Estado |
|---|---|---|
| I1 | `type` em ref, sem `--headed` | Espera-se `POLICY_DENIED` (guia Linux). Registrar o código obtido |
| I2 | `--headed type REF` para texto e `press` (`return`, `tab`, `delete`, `f3`, `f12`) para o resto | Caminho esperado. Exige foco na janela. `type` exige ref do nó `Terminal` e recusa Tab e nova linha no X11 (seção 6.5) |
| I2b | `--headed press <caractere> --window-id $W`, um caractere por chamada, sem ref | Recuo se `type` em ref falhar por foco. Mais lento (um processo por tecla; `batch` agrupa). Ajuste da 1.2.0: `press` escopado por `--window-id` só entrega se aquela janela tem o foco exato, o que serve de guarda extra para a regra 2 da seção 11 |

**Normalização para comparar telas:** 24 linhas, remover espaços à direita de cada linha, manter linhas vazias. Fidelidade = igualdade exata; registrar também a razão de similaridade (`difflib.SequenceMatcher`).

**Espera:** depois de cada envio, esperar por condição (`wait` do `agent-desktop` quando L1 funcionar; senão, sondar o oráculo até a tela mudar), com timeout. Nunca `sleep` fixo como sincronização.

## 8. Oráculo

Independente do `agent-desktop` e do agente:

- Tela: `tmux -L cadcli capture-pane -p -t cadcli`.
- Persistência: conteúdo de `data/clientes.dat`.

Cada cenário declara o estado esperado (trecho de tela e, quando couber, linha no arquivo). O oráculo decide aprovado ou reprovado. O que o agente afirma sobre o próprio sucesso é registrado, mas não conta.

## 9. Harness

```bash
python3 -m harness env up [--display isolated] [--terminal mate-terminal|xterm]   # exige bin/cadcli (app/build.sh)
python3 -m harness env down
python3 -m harness run [--scenario C3] [--reps 1] [--read l2|l3] [--timeout 5]    # sem --scenario: C1-C5
python3 -m harness verify C3 --result evidence/<run_id>/agent-result.json         # sai 0 se passou, 1 se não
python3 -m harness report [--phase-a-l2 DIR] [--phase-a-l3 DIR]   # gera RESULTS.md a partir de evidence/
```

`--display real` é recusado. `run` usa o ambiente já no ar; cada passo espera por condição no oráculo (timeout padrão 5 s, registrado em `meta.json`). Nos passos [L] a leitura (L2 padrão) só alimenta a fidelidade. `verify` julga o estado final (oráculo) e compara `claims` com o TEST-PLAN §6 (texto em maiúsculas; C1 `opcoes` por trecho; C2 `telas` ignora repetições consecutivas, esperado T01, T02, T01). `probe` (sondagens) ainda não está no CLI.

**Evidência**, em `evidence/<run_id>/`:

- `meta.json`: versão do `agent-desktop`, terminal, display, estratégias, data.
- `steps.jsonl`: uma linha por comando: `ts`, `scenario`, `rep`, `step`, `argv`, `ok`, `error_code`, `duration_ms`.
- `screens/<cenario>-<rep>-<passo>.read.txt` e `.oracle.txt` (só nos passos [L]; `.oracle.txt` também no passo que estourou o timeout).
- `summary.json`: aprovação por cenário e repetição, fidelidade, contagem de erros.

Antes de cada repetição: `app/reset.sh` e reiniciar o app (`respawn-pane`). Se a sessão tmux morreu (C2 encerra o app), o harness refaz tmux, display e janela (o `window-id` muda).

## 10. Sondagens (fase F2)

Feitas com uma tela falsa (script que imprime 24 linhas e ecoa teclas, dentro do tmux), antes de escrever o app COBOL.

| ID | Pergunta | Estado |
|---|---|---|
| P1 | `agent-desktop status` saudável? | **Feito:** `accessibility: granted` |
| P2 | A janela do terminal aparece em `list-apps` e `list-windows`, com `window-id` localizável pelo título? | **Feito (2026-11-12):** sim. `list-windows --app mate-terminal` devolve `data` como **array** (não `data.windows`); filtrar `.data[]|select(.title=="CADCLI")`. `focus-window --window-id` funciona com e sem `--headed` (`is_focused: true`). O id muda a cada subida |
| P3 | O `snapshot` mostra o quê? Algum nó expõe o texto da tela (L1)? | **Feito:** L1 NÃO funciona. Árvore (80 refs) só tem menus, aba, `Terminal` (textfield) e scrollbar. `get --property text` no `Terminal` devolve o nome `"Terminal"`; `value` é `null`. `find --text` e `wait --text` não acham o texto da tela |
| P4 | `type` sem `--headed` devolve qual erro (I1)? | **Feito:** `POLICY_DENIED`, check `supported_action`, `not_delivered`/`safe`. Nada chegou ao oráculo |
| P5 | Com `--headed`: texto, Enter, Tab, Backspace, F3 e F12 chegam ao app (I2)? | **Feito:** sim. `--headed type` 3/3; `press` escopado por `--window-id` (com e sem `--headed`, janela focada) 15/15; `press --app` focado 15/15; `--headed press --app` 15/15. Janela NÃO focada, sem `--headed`: `press --window-id` dá `STALE_REF` (`exact_window_focus`) e `press --app` dá `ACTION_FAILED` (`window_active`), 0/15 enviadas, nada entregue. `disposition` sempre `delivered_unverified` |
| P6 | L2 devolve a tela completa pela área de transferência? | **Feito:** sim, 6/6 com igualdade exata e razão 1.0 (menu Editar > Selecionar tudo > Copiar por `click` semântico, sem `--headed`; e `--headed press ctrl+shift+a`/`ctrl+shift+c`). `clipboard-get` em ~45 ms. Menu precisa abrir antes (`click` em `Editar`), senão item `offscreen` |
| P7 | L3: `screenshot` + `tesseract` atinge que similaridade com o oráculo? | **Feito:** PNG 836x588. OCR `--psm 6`: bruto 0.859, recorte 0.902, recorte+2x+negativo+cinza 0.953 (14/23 linhas iguais). Nunca exato (confunde 0/O, 1/I, 3 em lugar de J etc.) |
| P8 | Controles: `xterm`; terminal sem tmux; display isolado contra sessão real | **Parcial:** `xterm` invisível (`list-windows` `[]`, `list-apps` só `marco`). Mate-terminal sem tmux: não feito. Sessão real: pendente de autorização do Igor |

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

- Saída real de `--help` na 1.2.0: as flags da seção 6 vêm dos guias embutidos [G] e do fonte do `main` [F]; rodar `--help` de cada comando uma vez e corrigir a seção 6 se divergir (em especial `focus-window --title`, `wait --text` com `--window-id`, `screenshot --window-id`).
- Verificado em P2: app `mate-terminal`, JSON em `data[]`. Não verificado: título mudar depois de aberto.
- Se `focus-window` funciona sem `--headed` (um trecho do guia mostra `--headed focus-window`, outro não). P2/P5.
- Se o nó `Terminal` do `mate-terminal` está `focused` e `active` a ponto de `--headed type REF` passar na checagem de foco; senão cai em I2b. P5.
- Verificado em P3: nenhum nó expõe o texto da tela.
- Funcionamento do `agent-desktop` em display Xephyr (o guia confirma barramento privado com `dbus-run-session`, mas não Xephyr; `focus-window` precisa de EWMH, que o `marco` deveria dar).
- Nome e atalho dos itens "Selecionar tudo" e "Copiar" no `mate-terminal` (`ctrl+shift+a` e `ctrl+shift+c` são o palpite) e se o `clipboard-get` lê a seleção que o VTE serve. P6.
- Se o `marco` compõe janelas (define se `screenshot` de janela coberta funciona). P7.
- Passagem de F3 e F12 pela cadeia terminal → tmux → GnuCOBOL.
- Códigos de `CRT STATUS` no build do GnuCOBOL do Ubuntu.
