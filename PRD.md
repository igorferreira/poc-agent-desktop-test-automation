# PRD — POC: agent-desktop em aplicação de tela verde

| | |
|---|---|
| Versão | 0.1 (rascunho para aprovação) |
| Data | 2026-11-11 |
| Dono | Igor Ferreira |
| Documentos irmãos | [SPEC-TECH.md](SPEC-TECH.md), [ARCH.md](ARCH.md), [SCREENS.md](SCREENS.md), [TEST-PLAN.md](TEST-PLAN.md), [SETUP.md](SETUP.md), [TASKS.md](TASKS.md), [AGENTS.md](AGENTS.md) |

## 1. Resumo

Queremos saber se o `agent-desktop` (Vercel Labs) serve para automatizar testes de uma aplicação antiga de tela verde, estilo COBOL. A POC constrói um app de tela verde pequeno, tenta lê-lo e operá-lo com o `agent-desktop`, mede o resultado e termina com um veredito: dá, dá com ressalvas, ou não dá.

## 2. Contexto

O `agent-desktop` é uma CLI em Rust (Apache-2.0; no npm desde 23/02/2026, versão 1.0.0 em 28/10/2026) que dá "computer use" a agentes de IA sem screenshots. Ela lê a árvore de acessibilidade do sistema operacional (AT-SPI no Linux, UI Automation no Windows, AX no macOS), devolve JSON com uma referência (`ref`) por elemento, e o agente age sobre essas referências. A ferramenta não tem modelo embutido: o laço observar-agir fica no agente que a chama. Ela também funciona como servidor MCP (`agent-desktop mcp`).

Uma tela verde é o pior caso para essa abordagem. O app não tem botões nem campos como elementos: é uma grade de 80x24 caracteres desenhada dentro de um emulador de terminal. A árvore de acessibilidade enxerga o emulador, não o app.

## 3. Pergunta central e hipóteses

**Pergunta:** um agente de IA consegue executar um caso de teste de ponta a ponta em um app de tela verde usando só o `agent-desktop`, com resultado confiável e repetível?

| ID | Hipótese | Estado antes da POC |
|---|---|---|
| H1 | O `agent-desktop` consegue ler o texto da tela do terminal | **Em risco.** O guia Linux embutido na ferramenta diz que o nó de texto de um terminal é um `textfield` chamado `Terminal` com `value` nulo |
| H2 | O `agent-desktop` consegue enviar texto e teclas (Enter, Tab, F3, F12) ao app | **Parcial.** O mesmo guia diz que `type` sem `--headed` é recusado (`POLICY_DENIED`) e que o terminal só recebe teclas com `--headed`, isto é, entrada física |
| H3 | Com H1 e H2 resolvidas, um agente de IA completa os cenários a partir de casos em linguagem natural | Desconhecido |
| H4 | O resultado é repetível (sem flakiness relevante) | Desconhecido |

## 4. Baseline e posicionamento

Para um app de terminal puro, automação no nível do protocolo (tmux, `expect`/`pexpect`, `s3270` para 3270) costuma ser mais simples e mais robusta do que automação no nível da interface gráfica. A POC não ignora isso: o tmux entra como oráculo e como referência de comparação.

O `agent-desktop` só agrega valor nesse cenário se cobrir casos que o protocolo não cobre:

- A tela verde vive dentro de um emulador proprietário sem API de script.
- O fluxo de teste mistura tela verde com apps gráficos (planilha, navegador, cliente de e-mail).
- A equipe quer uma única ferramenta de agente para todo o desktop.

O relatório final deve dizer em quais desses casos o resultado da POC se aplica.

## 5. Escopo

**Dentro:**

- App de tela verde de exemplo (CADCLI: menu, inclusão e consulta de clientes) em GnuCOBOL.
- Execução em Linux (Ubuntu 26.04, X11, MATE), na máquina atual.
- Sondagens (probes) de viabilidade antes de construir qualquer coisa maior.
- Fase A: cenários determinísticos, sem LLM, para medir a ferramenta isoladamente.
- Fase B: os mesmos cenários conduzidos por um agente de IA a partir de casos em linguagem natural.
- Relatório com métricas, evidências e veredito.

**Fora:**

- Mainframe real, 3270/5250, emuladores proprietários (candidatos à fase 2).
- Windows e macOS.
- Geração automática de casos de teste pela IA.
- Integração com CI.
- Qualquer dado real. Só dados sintéticos.

## 6. Cenários de teste

| ID | Cenário | O que prova |
|---|---|---|
| C1 | Ler a tela do menu principal e identificar título e opções | H1 |
| C2 | Navegar: menu → inclusão → F12 limpa a digitação → F3 volta ao menu → 9 sai | H2 (dígitos, Enter, teclas de função) |
| C3 | Incluir um cliente (5 campos, Tab entre eles) e ver a mensagem de sucesso | H1 + H2 em formulário |
| C4 | Consultar um cliente existente e um inexistente, e conferir os dados e a mensagem exibidos | Leitura de dados dinâmicos |
| C5 | Caminho de erro: incluir código duplicado e UF inválida, ler a mensagem na linha 24 | Leitura de mensagens de validação |

O sucesso de cada cenário é decidido por um oráculo independente (tela capturada pelo tmux e conteúdo do arquivo de dados), nunca pelo próprio agente. O passo a passo de cada cenário está no [TEST-PLAN.md](TEST-PLAN.md).

## 7. Requisitos

**Funcionais**

- RF1. Subir e derrubar o ambiente de teste (janela do terminal com o app) por comando único.
- RF2. Ler a tela por pelo menos uma estratégia baseada no `agent-desktop` e registrar qual funcionou.
- RF3. Enviar texto, Enter, Tab, Backspace, F3 e F12 ao app.
- RF4. Executar C1–C5 de forma determinística (Fase A), com N repetições.
- RF5. Executar C1–C5 por um agente de IA (Fase B) a partir de casos em Markdown.
- RF6. Guardar evidência de cada passo: comando, envelope JSON, tela lida, tela do oráculo, duração.
- RF7. Gerar relatório com métricas e veredito.

**Não funcionais**

- RNF1. Agnóstico de IA: qualquer agente que rode comandos de shell ou fale MCP deve conseguir executar a Fase B só com os documentos do repositório.
- RNF2. Reprodutível: versões fixadas e estado inicial do app restaurado antes de cada repetição.
- RNF3. Seguro para o desktop do usuário: nenhum comando lê ou digita fora da janela do app de teste.
- RNF4. Mínimo de dependências novas. Usar o que já está instalado sempre que possível.

## 8. Métricas e critério de sucesso

Limiares propostos, ajustáveis:

| Métrica | Como medir | Limiar |
|---|---|---|
| Taxa de sucesso por cenário, Fase A | 10 repetições, julgadas pelo oráculo | ≥ 9/10 em cada cenário |
| Fidelidade de leitura | Tela lida comparada à do tmux, 24 linhas | Igualdade exata em ≥ 95% das leituras |
| Taxa de sucesso por cenário, Fase B | 3 repetições por caso, julgadas pelo oráculo | ≥ 2/3 em cada caso |
| Custo da Fase B | Chamadas de ferramenta, tempo de relógio, tokens quando disponível | Só registrar |
| Erros | Contagem por `error.code` do envelope | Só registrar |

**Veredito**

- **GO:** C1–C5 passam nas duas fases lendo a tela por acessibilidade ou área de transferência, com entrada via `--headed`.
- **GO com ressalvas:** funciona, mas só com screenshot + OCR ou visão; ou só tomando o teclado da sessão real; ou só em um emulador de terminal específico.
- **NO-GO:** a entrada de teclas não é confiável, ou nenhuma estratégia de leitura atinge o limiar. O relatório recomenda a alternativa (automação por protocolo).

## 9. Entregáveis

1. App CADCLI (fonte COBOL, build, dados de exemplo).
2. Harness de teste (sondagens, cenários, oráculo, relatório).
3. Casos de teste em linguagem natural para a Fase B.
4. Evidências das execuções.
5. `RESULTS.md` com matriz de viabilidade, métricas e veredito.

## 10. Riscos

| ID | Risco | Mitigação |
|---|---|---|
| R1 | O terminal não expõe o texto da tela (H1 falha) | Estratégias alternativas em ordem: área de transferência, depois screenshot + OCR. Sondagem antes de construir o app |
| R2 | Entrada só funciona com `--headed`: o teclado físico é tomado e uma tecla pode cair na janela errada. Há apps sensíveis abertos na sessão (gerenciador de senhas, chat) | Display X isolado (Xephyr) como padrão. Na sessão real, guarda de foco obrigatória antes de cada envio |
| R3 | O desktop medido pela ferramenta é GNOME; aqui é MATE | Já confirmado que `status` e `list-apps` funcionam no MATE. Sondagens cobrem o resto |
| R4 | AT-SPI pode não funcionar em display isolado | Sondagem dedicada. Recuo para a sessão real com guarda de foco |
| R5 | O tmux no meio do caminho altera teclas ou comportamento | Sondagem de controle sem tmux |
| R6 | Teclas de função capturadas pelo emulador ou por atalhos globais (F1, F10, F11, F12) | App usa só F3 e F12. Display isolado elimina atalhos globais |
| R7 | Ferramenta mudando rápido: cinco versões em oito dias (1.0.0 em 28/10 até 1.2.0 em 05/11/2026). Instalada: 1.0.2; npm: 1.2.0 | Fixar versão e registrá-la no relatório |
| R8 | Snapshots, screenshots e área de transferência podem conter conteúdo privado do desktop | Todo comando restrito à janela do app. `evidence/` fora do git. Dados sintéticos |
| R9 | Flakiness por tempo de redesenho da tela | Esperar por condição (texto presente), nunca por tempo fixo |
| R10 | `gnucobol3` exige `sudo`, que pede senha | Igor roda a instalação. Recuo: app equivalente em Python `curses` |
| R11 | App de brinquedo não representa um legado real (modo bloco 3270, emulador proprietário) | Veredito declarado como válido para "app ncurses em terminal Linux". Fase 2 cobre 3270 |
| R12 | Não determinismo e custo do LLM na Fase B | 3 repetições por caso, oráculo independente, custo registrado |

## 11. Fatos já verificados (2026-11-11)

- Ubuntu 26.04.1, x86_64, sessão X11, desktop MATE, `DISPLAY=:0`.
- `agent-desktop` 1.0.2 instalado; `status` devolve `accessibility: granted` e superfícies `window, sheet, alert, menu`.
- `agent-desktop list-apps` enxerga os apps da sessão MATE.
- Barramento AT-SPI em execução; `toolkit-accessibility` ligado.
- Presentes: Node 24, Python 3.12, pytest, tmux, xterm, mate-terminal, gnome-terminal, Xephyr, Xvfb, jq, tesseract, xclip, xdotool, wmctrl.
- Ausente: compilador COBOL (`cobc`). Pacote disponível: `gnucobol3` (3.2).

## 12. Decisões

| ID | Decisão | Resposta | Estado |
|---|---|---|---|
| D1 | Instalar `gnucobol3` com `sudo apt` | Sim. Igor roda a instalação na fase F1. O app fica em COBOL de verdade | Decidido por Igor em 2026-11-11 |
| D2 | Atualizar `agent-desktop` de 1.0.2 para 1.2.0 | Sim, e fixar a 1.2.0 | Decidido por Igor em 2026-11-11 |
| D3 | Onde rodar: display isolado (Xephyr) ou sessão real | Isolado primeiro. Se falhar, perguntar a Igor de novo antes de usar a sessão real | Decidido por Igor em 2026-11-11 |
| D4 | Qual agente de IA na Fase B | Padrão: Claude Code primeiro; segunda IA opcional | Pendente. Vale o padrão até Igor decidir |
| D5 | Controle de versão | Repositório público no GitHub: `igorferreira/poc-agent-desktop-test-automation`. `evidence/` continua fora do git | Decidido por Igor em 2026-11-12 |
| D6 | Limiares da seção 8 | Padrão: como propostos | Pendente. Vale o padrão até Igor decidir |

## 13. Fases

| Fase | Conteúdo | Portão de saída |
|---|---|---|
| F0 | Documentos de planejamento | Aprovação de Igor |
| F1 | Ambiente | Ferramentas instaladas, display de teste no ar |
| F2 | Sondagem de viabilidade com tela falsa | **G0:** existe ao menos uma estratégia de leitura e uma de entrada. Senão, a POC termina aqui com NO-GO |
| F3 | App CADCLI | Três telas funcionando à mão |
| F4 | Harness | Sondagens automatizadas e testes unitários passando |
| F5 | Fase A | Métricas dos cinco cenários |
| F6 | Fase B | Métricas dos cinco casos com agente |
| F7 | Fechamento | `RESULTS.md` com veredito |

## 14. Fontes

- README oficial: https://github.com/vercel-labs/agent-desktop
- Documentação: https://agent-browser.dev/desktop
- Pacote npm `agent-desktop` (1.2.0 em 2026-11-11)
- Guia Linux embutido no binário: `agent-desktop skills get platform` (lido na versão 1.0.2)
