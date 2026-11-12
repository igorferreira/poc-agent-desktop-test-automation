# ARCH — Arquitetura da POC

Versão 0.1 · 2026-11-11 · Modelo C4 em Mermaid. Detalhes de implementação em [SPEC-TECH.md](SPEC-TECH.md).

## Nível 1 — Contexto

```mermaid
C4Context
    title Nível 1 - Contexto
    Person(qa, "Engenheiro de QA", "Define cenários, dispara execuções e lê o relatório")
    System(poc, "POC Agent Desktop Test Automation", "Testa um app de tela verde usando o agent-desktop e mede o resultado")
    System(sut, "CADCLI", "App de tela verde em GnuCOBOL, substituto de um legado real")
    System_Ext(llm, "Provedor de LLM", "Qualquer modelo com chamada de ferramentas. Só na Fase B")
    System_Ext(os, "Sessão gráfica Linux", "X11 e barramento de acessibilidade AT-SPI")

    Rel(qa, poc, "Executa cenários e lê resultados")
    Rel(poc, sut, "Lê a tela e envia teclas", "agent-desktop")
    Rel(poc, llm, "Envia observações, recebe a próxima ação", "HTTPS")
    Rel(poc, os, "Consulta a árvore de acessibilidade", "AT-SPI")
    Rel(sut, os, "É desenhado em uma janela de terminal")
    UpdateLayoutConfig($c4ShapeInRow="3", $c4BoundaryInRow="1")
```

## Nível 2 — Contêineres

```mermaid
C4Container
    title Nível 2 - Contêineres
    Person(qa, "Engenheiro de QA", "Dispara execuções e lê o relatório")
    System_Ext(llm, "Provedor de LLM", "Só na Fase B")

    System_Boundary(host, "Host Ubuntu 26.04 - display X11 isolado ou sessão real") {
        Container(agent, "Agente de IA", "Claude Code, Codex, Gemini CLI ou outro", "Fase B: executa casos escritos em linguagem natural")
        Container(harness, "Harness", "Python 3.12, biblioteca padrão", "Fase A: sondagens, cenários, medição e relatório")
        Container(ad, "agent-desktop", "CLI em Rust, também servidor MCP", "Observa e opera janelas pela árvore de acessibilidade")
        Container(term, "Emulador de terminal", "mate-terminal, 80x24", "Janela com título CADCLI")
        Container(tmux, "tmux", "Sessão cadcli, socket próprio", "Hospeda o app e expõe a tela ao oráculo")
        Container(app, "CADCLI", "GnuCOBOL 3.2 e ncurses", "Menu, inclusão e consulta de clientes")
        ContainerDb(data, "clientes.dat", "Arquivo de texto, colunas fixas", "Registros de clientes")
        ContainerDb(evid, "evidence", "JSONL, TXT, PNG", "Envelopes, telas lidas, telas do oráculo")
    }

    System_Ext(atspi, "AT-SPI e X11", "Barramento de acessibilidade e servidor gráfico")

    Rel(qa, harness, "python3 -m harness")
    Rel(qa, agent, "Pede a execução de um caso")
    Rel(agent, llm, "Raciocínio", "HTTPS")
    Rel(agent, ad, "Comandos", "CLI ou MCP stdio")
    Rel(harness, ad, "Comandos, lê envelope JSON", "subprocess")
    Rel(ad, atspi, "snapshot, type, press, screenshot")
    Rel(atspi, term, "Expõe a árvore, entrega teclas")
    Rel(term, tmux, "pty")
    Rel(tmux, app, "pty")
    Rel(app, data, "Lê e grava")
    Rel(harness, tmux, "capture-pane", "oráculo")
    Rel(harness, data, "Confere registros", "oráculo")
    Rel(harness, evid, "Grava")
    Rel(agent, evid, "Grava agent-result.json")
    UpdateLayoutConfig($c4ShapeInRow="3", $c4BoundaryInRow="1")
```

Há dois caminhos até o app, e a separação é proposital:

- **Caminho sob teste:** agente ou harness → `agent-desktop` → AT-SPI/X11 → terminal → tmux → CADCLI.
- **Caminho do oráculo:** harness → tmux e arquivo de dados, sem passar pelo `agent-desktop`.

## Nível 3 — Componentes do harness

```mermaid
C4Component
    title Nível 3 - Componentes do harness
    Container_Ext(ad, "agent-desktop", "CLI")
    Container_Ext(tmux, "tmux", "Sessão cadcli")
    ContainerDb_Ext(data, "clientes.dat", "Arquivo de dados")
    ContainerDb_Ext(evid, "evidence", "Arquivos de evidência")

    Container_Boundary(h, "Harness") {
        Component(cli, "__main__", "argparse", "Comandos env, probe, run, verify, report")
        Component(launcher, "launcher", "Python", "Sobe e derruba display, tmux e terminal. Descobre o window-id")
        Component(adw, "ad", "subprocess", "Executa o agent-desktop, interpreta o envelope, registra cada passo")
        Component(screen, "screen", "Python", "Leitura da tela: L1 acessibilidade, L2 área de transferência, L3 screenshot e OCR")
        Component(keys, "keys", "Python", "Envio de texto e teclas com guarda de foco")
        Component(oracle, "oracle", "Python", "Tela real via capture-pane e conferência do arquivo de dados")
        Component(probes, "probes", "Python", "Sondagens P2 a P8")
        Component(scen, "scenarios", "Python", "Cenários C1 a C5")
        Component(report, "report", "Python", "Métricas e RESULTS.md")
    }

    Rel(cli, launcher, "env up, env down")
    Rel(cli, probes, "probe")
    Rel(cli, scen, "run")
    Rel(cli, oracle, "verify")
    Rel(cli, report, "report")
    Rel(probes, screen, "Usa")
    Rel(probes, keys, "Usa")
    Rel(scen, screen, "Usa")
    Rel(scen, keys, "Usa")
    Rel(scen, oracle, "Julga cada passo")
    Rel(screen, adw, "snapshot, get, clipboard-get, screenshot")
    Rel(keys, adw, "focus-window, type, press")
    Rel(launcher, adw, "list-windows")
    Rel(adw, ad, "Processo filho")
    Rel(adw, evid, "steps.jsonl")
    Rel(oracle, tmux, "capture-pane")
    Rel(oracle, data, "Lê")
    Rel(report, evid, "Lê")
    UpdateLayoutConfig($c4ShapeInRow="3", $c4BoundaryInRow="1")
```

## Fluxo de um passo de teste

```mermaid
sequenceDiagram
    autonumber
    participant D as Agente ou harness
    participant AD as agent-desktop
    participant T as Terminal
    participant A as CADCLI via tmux
    participant O as Oráculo

    D->>AD: focus-window --window-id W
    AD-->>D: envelope ok
    D->>AD: confirma janela ativa
    alt janela ativa não é CADCLI
        D->>D: aborta a repetição
    else janela ativa é CADCLI
        D->>AD: --headed type ou press
        AD->>T: tecla física via X11
        T->>A: bytes no pty
        A-->>T: redesenha a tela
        D->>AD: lê a tela por L1, L2 ou L3
        AD-->>D: texto lido
        D->>O: capture-pane e arquivo de dados
        O-->>D: tela real e registros
        D->>D: compara, grava evidência, julga pelo oráculo
    end
```

## Escolha das estratégias

```mermaid
flowchart TD
    S["Sondagens na tela falsa"] --> L1{"L1: acessibilidade expõe o texto?"}
    L1 -- sim --> RL1["Leitura por L1"]
    L1 -- não --> L2{"L2: área de transferência devolve a tela?"}
    L2 -- sim --> RL2["Leitura por L2"]
    L2 -- não --> L3{"L3: screenshot + OCR atinge o limiar?"}
    L3 -- sim --> RL3["Leitura por L3"]
    L3 -- não --> NG["NO-GO: sem leitura confiável"]

    RL1 --> I{"Entrada: I2 com --headed entrega as teclas?"}
    RL2 --> I
    RL3 --> I
    I -- não --> NG2["NO-GO: sem entrada confiável"]
    I -- sim --> G0["G0 aprovado: construir CADCLI e seguir"]

    G0 --> V{"Leitura usada"}
    V -- "L1 ou L2" --> GO["Candidato a GO"]
    V -- "L3" --> GOR["Candidato a GO com ressalvas"]
```

## Implantação

```mermaid
flowchart LR
    subgraph real["Sessão real do usuário, DISPLAY=:0"]
        U["Apps do usuário"]
        RUN["Agente ou harness + agent-desktop"]
    end
    subgraph iso["Display isolado, Xephyr :2"]
        BUS["dbus-run-session + AT-SPI próprio"]
        WM["marco"]
        TERM["mate-terminal CADCLI"]
    end
    subgraph srv["Servidor tmux, socket cadcli"]
        APP["CADCLI"]
        DAT[("clientes.dat")]
    end
    RUN -- "DISPLAY=:2 e barramento do display isolado" --> BUS
    BUS --- TERM
    WM --- TERM
    TERM -- attach --> APP
    APP --- DAT
    RUN -. "capture-pane (oráculo)" .-> APP
```

O display isolado é o padrão proposto e ainda precisa ser validado (sondagem P8). Se o `agent-desktop` não funcionar nele, tudo roda na sessão real e a guarda de foco passa a ser a única proteção.

## Decisões de arquitetura

| # | Decisão | Motivo | Alternativa descartada |
|---|---|---|---|
| A1 | Sondar com tela falsa antes de escrever o app | A pergunta central pode ter resposta negativa em uma hora de trabalho | Construir tudo e descobrir no fim |
| A2 | Oráculo fora do caminho sob teste (tmux + arquivo) | O agente não pode julgar o próprio sucesso; mede fidelidade de leitura com precisão | Confiar no que o `agent-desktop` leu |
| A3 | Duas fases: determinística, depois com IA | Separa falha da ferramenta de falha do modelo | Só rodar com IA |
| A4 | Display isolado como padrão | Entrada física não toma o teclado nem atinge outros apps | Rodar direto na sessão real |
| A5 | Harness em Python, só biblioteca padrão | Já instalado, sem dependências | Bash + jq (frágil para medir); framework de testes externo |
| A6 | Dados em arquivo de texto de colunas fixas | Oráculo e reset triviais | Arquivo indexado (depende do build do GnuCOBOL) |
| A7 | Casos da Fase B em Markdown, agente fala CLI ou MCP | Qualquer IA executa | Prender a POC a um SDK de agente |
