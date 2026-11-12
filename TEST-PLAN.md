# TEST-PLAN — Cenários da POC

Versão 0.1 · 2026-11-11 · Detalha os cenários C1–C5 do [PRD.md](PRD.md). Telas, mensagens e arquivo de dados estão em [SCREENS.md](SCREENS.md). Estratégias de leitura e de entrada estão no [SPEC-TECH.md](SPEC-TECH.md), seção 7.

## 1. Como os cenários são usados

Os mesmos cinco cenários rodam nas duas fases:

| | Fase A | Fase B |
|---|---|---|
| Quem conduz | Harness, sequência fixa de comandos | Agente de IA, a partir de um caso em linguagem natural |
| Repetições | 10 por cenário e por estratégia viável | 3 por caso |
| Quem julga | Oráculo | Oráculo |

## 2. Regras comuns

**Pré-condição de toda repetição**

1. Ambiente no ar e janela `CADCLI` localizada pelo `window-id`.
2. `data/clientes.dat` restaurado a partir de `app/seed/clientes.dat`.
3. App reiniciado, mostrando T01.

**Envio de teclas.** Sempre pela estratégia de entrada do `agent-desktop` em teste, depois da guarda de foco (SPEC-TECH seção 11). Depois de cada envio, esperar a condição da coluna "Esperado", com timeout. Sem espera de tempo fixo.

**Julgamento.** Um passo passa quando a tela capturada pelo tmux mostra o que a coluna "Esperado" descreve. Um cenário passa quando todos os passos passam e o estado final confere. A tela lida pelo `agent-desktop` não entra no julgamento do cenário.

**Fidelidade de leitura.** Em todo passo marcado com **[L]**, a tela é lida pela estratégia de leitura em teste e comparada com a captura do tmux. Essa comparação alimenta a métrica de fidelidade do PRD seção 8, separada do sucesso do cenário.

**Timeout.** Um passo que não atinge o esperado no tempo limite falha, e a repetição termina ali. O valor do timeout é definido na implementação do harness e registrado em `meta.json`.

## 3. Dados de teste

Todos sintéticos. O seed tem os clientes `000001` (MARIA DA SILVA, RIO DE JANEIRO, RJ) e `000002` (JOAO PEREIRA, SAO PAULO, SP).

| Uso | CODIGO | NOME | CPF | CIDADE | UF |
|---|---|---|---|---|---|
| C2, digitação descartada | `000123` | — | — | — | — |
| C3, inclusão válida | `000100` | `ANA TESTE` | `33333333333` | `CURITIBA` | `PR` |
| C4, consulta sem resultado | `000999` | — | — | — | — |
| C5, código duplicado | `000001` | `DUPLICADO` | `44444444444` | `NITEROI` | `RJ` |
| C5, UF inválida | `000101` | `UF ERRADA` | `55555555555` | `RECIFE` | `XX` |

## 4. Cenários

### C1 — Ler o menu

Prova a hipótese H1. Nenhuma tecla é enviada.

| Passo | Ação | Esperado |
|---|---|---|
| 1 **[L]** | Ler a tela | Linha 1 contém `CADCLI`, `CADASTRO DE CLIENTES` e `T01`. Linhas 5, 7 e 9 contêm `1-INCLUIR`, `2-CONSULTAR` e `9-SAIR`. Linha 12 contém `OPCAO .:` |

Estado final: T01; arquivo de dados igual ao seed.

Na Fase B o agente declara o título da tela e as opções do menu.

### C2 — Navegar

Prova a hipótese H2 para dígitos, Enter, F12 e F3.

| Passo | Ação | Esperado |
|---|---|---|
| 1 **[L]** | Digitar `1`, Enter | Linha 1 contém `T02` |
| 2 **[L]** | Digitar `000123` | Linha 4 contém `000123` |
| 3 **[L]** | F12 | Linha 1 contém `T02`. Linha 4 não contém `000123` |
| 4 **[L]** | F3 | Linha 1 contém `T01` |
| 5 | Digitar `9`, Enter | A sessão tmux `cadcli` não existe mais |

Estado final: app encerrado; arquivo de dados igual ao seed.

Na Fase B o agente declara a sequência de telas que viu.

### C3 — Incluir um cliente

Prova H1 e H2 em formulário, com Tab e Backspace, e confere a persistência.

| Passo | Ação | Esperado |
|---|---|---|
| 1 | Digitar `1`, Enter | Linha 1 contém `T02` |
| 2 | Digitar `000100`, Tab | Linha 4 contém `000100` |
| 3 **[L]** | Digitar `ANA TESTEX`, Backspace, Tab | Linha 5 contém `ANA TESTE` e não contém `TESTEX` |
| 4 | Digitar `33333333333`, Tab | Linha 6 contém `33333333333` |
| 5 | Digitar `CURITIBA`, Tab | Linha 7 contém `CURITIBA` |
| 6 **[L]** | Digitar `PR`, Enter | Linha 24 contém `CLIENTE INCLUIDO` |

Estado final: T02. O arquivo de dados tem três linhas; as duas primeiras são as do seed e a terceira é:

```
000100ANA TESTE                     33333333333CURITIBA            PR
```

Na Fase B o agente declara a mensagem que viu depois de confirmar.

### C4 — Consultar

Prova a leitura de dados que mudam conforme a entrada.

| Passo | Ação | Esperado |
|---|---|---|
| 1 | Digitar `2`, Enter | Linha 1 contém `T03` |
| 2 **[L]** | Digitar `000001`, Enter | Linha 6 contém `MARIA DA SILVA`. Linha 7 contém `11111111111`. Linha 8 contém `RIO DE JANEIRO`. Linha 9 contém `RJ`. Linha 24 vazia |
| 3 **[L]** | Digitar `000999`, Enter | Linha 24 contém `CLIENTE NAO ENCONTRADO`. Linha 6 não contém `MARIA DA SILVA` |
| 4 | F3 | Linha 1 contém `T01` |

Estado final: T01; arquivo de dados igual ao seed.

Na Fase B o agente declara nome, CPF, cidade e UF do cliente `000001` e a mensagem da segunda consulta. O harness compara essas declarações com o seed.

### C5 — Erros de validação

Prova a leitura de mensagens na linha 24 e que entrada inválida não grava nada.

| Passo | Ação | Esperado |
|---|---|---|
| 1 **[L]** | Digitar `5`, Enter | Linha 1 contém `T01`. Linha 24 contém `OPCAO INVALIDA` |
| 2 | Digitar `1`, Enter | Linha 1 contém `T02` |
| 3 **[L]** | Digitar `000001`, Tab, `DUPLICADO`, Tab, `44444444444`, Tab, `NITEROI`, Tab, `RJ`, Enter | Linha 24 contém `CODIGO JA CADASTRADO` |
| 4 | F12 | Linha 24 vazia. Linha 4 não contém `000001` |
| 5 **[L]** | Digitar `000101`, Tab, `UF ERRADA`, Tab, `55555555555`, Tab, `RECIFE`, Tab, `XX`, Enter | Linha 24 contém `UF INVALIDA` |

Estado final: T02; arquivo de dados igual ao seed.

Na Fase B o agente declara as três mensagens, na ordem.

## 5. Cobertura

| Requisito | Onde |
|---|---|
| Leitura de tela fixa | C1 |
| Leitura de dados dinâmicos | C4 |
| Leitura da linha de mensagem | C3, C4, C5 |
| Texto e dígitos | C2, C3, C4, C5 |
| Enter | C2, C3, C4, C5 |
| Tab | C3, C5 |
| Backspace | C3 |
| F3 | C2, C4 |
| F12 | C2, C5 |
| Persistência | C3 |
| Entrada inválida não grava | C5 |

## 6. Fase B: formato dos casos e do resultado

Cada caso fica em `cases/C<n>.md` (tarefa T-060) com quatro partes: objetivo, pré-condição, o que fazer, o que declarar. O caso descreve a intenção de negócio e os dados; não lista teclas. O agente descobre as teclas pela linha 23 da tela e pode consultar o SCREENS.md.

Exemplo do "o que fazer" de C3:

> Inclua um cliente novo com código 000100, nome ANA TESTE, CPF 33333333333, cidade CURITIBA e UF PR. Confirme a inclusão e diga qual mensagem o sistema mostrou.

Ao terminar, o agente grava `evidence/<run_id>/agent-result.json`:

```json
{
  "case": "C3",
  "agent": "nome da ferramenta de IA",
  "model": "modelo usado",
  "claims": { "mensagem": "CLIENTE INCLUIDO" },
  "tool_calls": 0,
  "duration_s": 0,
  "tokens": null
}
```

`claims` por caso:

| Caso | Chaves |
|---|---|
| C1 | `titulo`, `opcoes` (lista) |
| C2 | `telas` (lista, na ordem) |
| C3 | `mensagem` |
| C4 | `nome`, `cpf`, `cidade`, `uf`, `mensagem` |
| C5 | `mensagens` (lista, na ordem) |

`python3 -m harness verify C<n>` julga o caso pelo estado final do oráculo e compara `claims` com o esperado. Um caso só passa se as duas coisas conferirem: o estado final está certo e o agente relatou o que de fato estava na tela.

## 7. Fora deste plano

- Teste de carga ou de desempenho do app.
- Redimensionamento da janela, troca de fonte ou de tema do terminal.
- Entrada com acentos ou minúsculas.
- Recuperação depois de foco perdido no meio de um cenário: a repetição é abortada e contada como falha.
