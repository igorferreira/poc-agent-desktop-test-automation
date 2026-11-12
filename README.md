# POC: agent-desktop em aplicação de tela verde

Prova de conceito para responder uma pergunta: o [`agent-desktop`](https://github.com/vercel-labs/agent-desktop) (Vercel Labs) consegue ler e operar um app antigo de tela verde, estilo COBOL, de forma confiável o bastante para automatizar testes?

O app de teste é o CADCLI, um cadastro de clientes em GnuCOBOL com telas de 80x24, rodando num terminal Linux. A POC termina com um veredito: GO, GO com ressalvas ou NO-GO.

## Estado

Planejamento concluído; execução em andamento. O andamento de cada tarefa está no [TASKS.md](TASKS.md).

## Documentos

| Documento | Conteúdo |
|---|---|
| [PRD.md](PRD.md) | Objetivo, hipóteses, cenários, métricas, riscos e decisões |
| [SPEC-TECH.md](SPEC-TECH.md) | Stack, estratégias de leitura e de entrada, oráculo, harness, segurança |
| [ARCH.md](ARCH.md) | Diagramas C4 em Mermaid |
| [SCREENS.md](SCREENS.md) | Layout exato das telas do CADCLI |
| [TEST-PLAN.md](TEST-PLAN.md) | Cenários C1–C5 passo a passo |
| [SETUP.md](SETUP.md) | Preparação da máquina |
| [TASKS.md](TASKS.md) | Tarefas, responsáveis e status |
| [AGENTS.md](AGENTS.md) | Instruções para agentes de IA que trabalham no repositório |

## Requisitos

Ubuntu com sessão X11, Node.js, Python 3.12, tmux, GnuCOBOL 3.2 e `agent-desktop` 1.2.0. Passo a passo no [SETUP.md](SETUP.md).

## Privacidade

Snapshots, screenshots e capturas da área de transferência podem conter conteúdo privado do desktop. As evidências das execuções ficam em `evidence/`, que não entra no git. Os dados do app são sintéticos.

## Licença

[MIT](LICENSE).
