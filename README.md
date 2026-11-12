# POC: agent-desktop em aplicação de tela verde

Prova de conceito para saber se o [`agent-desktop`](https://github.com/vercel-labs/agent-desktop) (Vercel Labs) consegue ler e operar um app antigo de tela verde de forma confiável o bastante para automatizar testes. O app de teste é o CADCLI, um cadastro de clientes em GnuCOBOL (telas 80x24) rodando num terminal Linux.

## Resultado

- **Veredito PROPOSTO: GO com ressalvas.** A decisão final é do Igor. Só mate-terminal, display isolado, leitura pela área de transferência e entrada `--headed`.
- **Fase A (sem IA):** 50/50 repetições com leitura L2; 120 leituras, 100,0% exatas. Leitura por OCR (L3) é inviável: 0,0% exatas.
- **Fase B (agente de IA):** 15/15 casos (3 repetições por caso).
- **Custo estimado:** US$ 50,43 em preço de API (71,1 milhões de tokens), não a cobrança real. Detalhes em [CUSTOS.md](CUSTOS.md).

Números e limitações completos em [RESULTS.md](RESULTS.md).

## Requisitos e instalação

Ubuntu com sessão X11, Node.js, Python 3.12, tmux, Xephyr, `mate-terminal` e `tesseract`. Passo a passo em [SETUP.md](SETUP.md). O essencial:

```bash
sudo apt install -y gnucobol3                 # cobc 3.2; não usar gnucobol4
npm install -g agent-desktop@1.2.0            # versão fixada
chmod 700 ~/.agent-desktop                    # (mkdir -m 700 se não existir) senão snapshot falha com INTERNAL
```

## Reproduzir

Na raiz do repositório, nesta ordem:

```bash
app/build.sh                                      # compila bin/cadcli
python3 -m pytest -q tests/                       # testes (sem o ambiente no ar)
python3 -m harness probe                          # sondagens P2-P8 (sobe e derruba o próprio ambiente)
python3 -m harness env up                         # tmux + Xephyr :2 + mate-terminal com o app
python3 -m harness run --reps 10 --read l2        # Fase A, C1-C5; evidência em evidence/<run_id>/
python3 -m harness env down
python3 -m harness report                         # gera RESULTS.md a partir de evidence/
```

Para a leitura por OCR, repita o `run` com `--read l3` e passe os dois diretórios ao `report` (`--phase-a-l2 DIR --phase-a-l3 DIR`).

**Fase B (agente de IA):** siga [cases/OPERADOR.md](cases/OPERADOR.md).

## Segurança

Tudo roda num display isolado (Xephyr `:2`), sem tocar na sessão gráfica real. Não rode na sessão real sem ler o [SPEC-TECH.md](SPEC-TECH.md) seção 11. Snapshots, screenshots e área de transferência podem conter conteúdo privado: `evidence/` fica fora do git e os dados do app são sintéticos.

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
| [G0-VIABILIDADE.md](G0-VIABILIDADE.md) | Matriz de viabilidade das sondagens P2–P8 |
| [RESULTS.md](RESULTS.md) | Resultados das Fases A e B, hipóteses, limitações e veredito proposto |
| [CUSTOS.md](CUSTOS.md) | Consumo de tokens e custo estimado |
| [cases/](cases/) | Casos da Fase B (C1–C5), `AGENT.md` e `OPERADOR.md` |

## Licença

[MIT](LICENSE).
