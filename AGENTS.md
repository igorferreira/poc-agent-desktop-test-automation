# AGENTS — Instruções para qualquer agente de IA

Este repositório é uma POC: descobrir se o `agent-desktop` (Vercel Labs) serve para automatizar testes de um app de tela verde estilo COBOL. O resultado é um veredito (GO, GO com ressalvas ou NO-GO) sustentado por evidência.

## Estado atual

Existem o app COBOL (`app/`), a tela falsa e o harness (`harness/`). Comandos reais, a partir da raiz:

```bash
app/build.sh                                  # compila bin/cadcli (cobc)
app/reset.sh                                  # restaura data/clientes.dat a partir do seed
python3 -m pytest -q tests/test_ad.py tests/test_screen.py tests/test_keys.py tests/test_oracle.py tests/test_report.py
python3 -m harness env up | env down          # tmux -L cadcli + Xephyr :2 + mate-terminal rodando app/run.sh
python3 -m harness run [--scenario C3] [--reps N] [--read l2|l3]   # evidence/<run_id>/
python3 -m harness verify C3 --result evidence/<run_id>/agent-result.json
python3 -m harness report [--phase-a-l2 DIR] [--phase-a-l3 DIR]   # gera RESULTS.md
python3 -m harness probe [P2 ... P8]          # sondagens com a tela falsa; evidence/probes-<run_id>/
```

`harness report` existe (lê `evidence/`, escreve `RESULTS.md`); `harness probe` existe (sobe e derruba o próprio ambiente; P8c é manual, T-029). Não rode `tests/test_fake_screen.py` nem `tests/test_integration_display.py` com o ambiente no ar (mesma sessão tmux). Detalhes em [SPEC-TECH.md](SPEC-TECH.md) seção 9.

O estado de cada tarefa está no [TASKS.md](TASKS.md).

## Ordem de leitura

| # | Documento | Para quê |
|---|---|---|
| 1 | [PRD.md](PRD.md) | O que a POC quer provar, cenários, métricas, riscos, decisões |
| 2 | [SPEC-TECH.md](SPEC-TECH.md) | Stack, estratégias de leitura e de entrada, oráculo, harness, segurança |
| 3 | [ARCH.md](ARCH.md) | Diagramas C4 e decisões de arquitetura |
| 4 | [SCREENS.md](SCREENS.md) | Layout exato das telas, mensagens e arquivo de dados do CADCLI |
| 5 | [TEST-PLAN.md](TEST-PLAN.md) | Cenários C1–C5 passo a passo, formato dos casos da Fase B |
| 6 | [SETUP.md](SETUP.md) | Como preparar a máquina |
| 7 | [TASKS.md](TASKS.md) | O que fazer, em que ordem, e o que já foi feito |

## Como trabalhar

1. Pegue no TASKS.md uma tarefa `TODO` cujas dependências estejam `DONE`.
2. Marque `DOING`. Ao terminar, marque `DONE` só se o critério "Pronto quando" foi cumprido **e verificado**. Atualize o TASKS.md no mesmo trabalho.
3. Descobriu algo que contradiz um documento? Corrija o documento e registre em "Achados" no TASKS.md, com data.
4. Decisão que cabe ao Igor (itens do PRD seção 12, uso da sessão real, qualquer `sudo`): pergunte, não assuma.

## Regras de segurança

A sessão gráfica real do usuário tem apps sensíveis abertos. As regras completas estão no SPEC-TECH seção 11 e são obrigatórias. Resumo:

- Todo comando do `agent-desktop` leva o `--window-id` da janela `CADCLI`. Nunca `snapshot`, `screenshot` ou `find` em outra janela.
- Antes de cada envio com `--headed`: focar a janela, confirmar que a janela ativa é a `CADCLI`, e só então enviar. Se não confirmar, abortar.
- Display isolado (Xephyr) é o padrão. Usar a sessão real só com autorização do Igor.
- Leitura pela área de transferência na sessão real só com autorização explícita.
- `evidence/` nunca entra no git nem em upload. Só dados sintéticos.
- Não reiniciar o barramento AT-SPI nem outros serviços da sessão do usuário.

## Uso do agent-desktop

A ferramenta traz os próprios guias. Antes do primeiro uso, rode e siga:

```bash
agent-desktop skills get desktop
agent-desktop skills get platform
```

- Não invente flags. Rode `agent-desktop <comando> --help` na versão fixada (1.2.0).
- Cada comando devolve um envelope JSON. Confira `ok`. Em erro, leia `error.code` e só repita o comando se `error.disposition.retry` for `safe`.
- Refs valem só para o snapshot que as criou. Em `STALE_REF`, tire outro snapshot.

## Convenções

- Documentos em português. Código e nomes de arquivo sem acento.
- "Verificado" é o que foi conferido na máquina ou na fonte oficial. "A validar" não é fato.
- Sincronização por condição com timeout. Nunca `sleep` fixo.
- O sucesso de um cenário é decidido pelo oráculo (tmux e arquivo de dados), nunca pelo agente que o executou.
- Harness em Python 3.12, só biblioteca padrão. Dependência nova exige justificativa no SPEC-TECH.
- Commit e push só quando o Igor pedir.
