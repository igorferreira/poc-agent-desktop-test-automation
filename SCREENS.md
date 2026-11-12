# SCREENS — Telas do CADCLI

Versão 0.1 · 2026-11-11 · Contrato entre quem escreve o app COBOL (T-030), quem escreve o oráculo (T-042) e quem escreve os casos de teste. Os cenários que usam estas telas estão em [TEST-PLAN.md](TEST-PLAN.md).

## 1. Regras gerais

- Tela de 80 colunas por 24 linhas. Coordenadas começam em 1: `(linha, coluna)`.
- Verde sobre preto.
- Só ASCII maiúsculo, sem acento, no app e nos dados. Isso evita problema de codificação no terminal e erro de OCR.
- Linha 1: cabeçalho. `CADCLI` na coluna 2, título na coluna 31, identificador da tela (`T01`, `T02`, `T03`) na coluna 78.
- Linha 23: teclas disponíveis, a partir da coluna 2.
- Linha 24: mensagem, a partir da coluna 2. Fica vazia quando não há mensagem.
- O identificador na linha 1 é a forma oficial de saber em que tela o app está.

Nos mapas abaixo, `_` marca posição de campo de entrada. O caractere que o GnuCOBOL realmente mostra em campo vazio ainda não foi verificado; as telas de referência reais são as capturas da tarefa T-032. Por isso o oráculo confere textos por posição, e não a tela inteira contra estes mapas.

## 2. T01 — Menu

```
    ....+....1....+....2....+....3....+....4....+....5....+....6....+....7....+....8
01   CADCLI                       CADASTRO DE CLIENTES                           T01
02
03
04
05           1-INCLUIR
06
07           2-CONSULTAR
08
09           9-SAIR
10
11
12           OPCAO .: _
13
14
15
16
17
18
19
20
21
22
23   F3=SAIR  ENTER=CONFIRMAR
24   OPCAO INVALIDA
```

| Elemento | Posição | Tamanho | Tipo |
|---|---|---|---|
| `1-INCLUIR` | (5, 10) | — | Texto fixo |
| `2-CONSULTAR` | (7, 10) | — | Texto fixo |
| `9-SAIR` | (9, 10) | — | Texto fixo |
| `OPCAO .:` | (12, 10) | — | Rótulo |
| Campo OPCAO | (12, 19) | 1 | Entrada, numérico |

Comportamento:

| Entrada | Resultado |
|---|---|
| `1` + Enter | Vai para T02 |
| `2` + Enter | Vai para T03 |
| `9` + Enter | Encerra o app |
| F3 | Encerra o app |
| Outro valor + Enter | Fica em T01, mensagem `OPCAO INVALIDA` |

Quando o app encerra, a sessão tmux `cadcli` termina e a janela do terminal fecha.

## 3. T02 — Inclusão de cliente

```
    ....+....1....+....2....+....3....+....4....+....5....+....6....+....7....+....8
01   CADCLI                       INCLUSAO DE CLIENTE                            T02
02
03
04     CODIGO .: ______
05     NOME ...: ______________________________
06     CPF ....: ___________
07     CIDADE .: ____________________
08     UF .....: __
09
10
11
12
13
14
15
16
17
18
19
20
21
22
23   F3=VOLTAR  F12=CANCELAR  ENTER=CONFIRMAR
24   CLIENTE INCLUIDO
```

| Campo | Rótulo em | Campo em | Tamanho | Tipo |
|---|---|---|---|---|
| CODIGO | (4, 4) | (4, 14) | 6 | Numérico |
| NOME | (5, 4) | (5, 14) | 30 | Alfanumérico |
| CPF | (6, 4) | (6, 14) | 11 | Numérico |
| CIDADE | (7, 4) | (7, 14) | 20 | Alfanumérico |
| UF | (8, 4) | (8, 14) | 2 | Alfanumérico |

Comportamento:

| Entrada | Resultado |
|---|---|
| Tab | Avança para o próximo campo. Não há avanço automático ao encher um campo |
| Enter | Valida. Com sucesso: grava o registro, limpa os campos, mensagem `CLIENTE INCLUIDO`, continua em T02 |
| Enter com erro | Não grava, mantém os campos, mostra a mensagem do primeiro erro |
| F12 | Limpa campos e mensagem, continua em T02, não grava |
| F3 | Volta para T01, não grava |

Validações, nesta ordem:

1. CODIGO já existe no arquivo: `CODIGO JA CADASTRADO`.
2. UF fora da lista das 27 unidades federativas: `UF INVALIDA`.

Campos numéricos são sempre digitados com todos os dígitos (`000100`, não `100`), para não depender de como o GnuCOBOL alinha entrada numérica parcial.

## 4. T03 — Consulta de cliente

```
    ....+....1....+....2....+....3....+....4....+....5....+....6....+....7....+....8
01   CADCLI                       CONSULTA DE CLIENTE                            T03
02
03
04     CODIGO .: 000001
05
06     NOME ...: MARIA DA SILVA
07     CPF ....: 11111111111
08     CIDADE .: RIO DE JANEIRO
09     UF .....: RJ
10
11
12
13
14
15
16
17
18
19
20
21
22
23   F3=VOLTAR  ENTER=CONSULTAR
24
```

| Campo | Rótulo em | Campo em | Tamanho | Tipo |
|---|---|---|---|---|
| CODIGO | (4, 4) | (4, 14) | 6 | Entrada, numérico |
| NOME | (6, 4) | (6, 14) | 30 | Saída |
| CPF | (7, 4) | (7, 14) | 11 | Saída |
| CIDADE | (8, 4) | (8, 14) | 20 | Saída |
| UF | (9, 4) | (9, 14) | 2 | Saída |

Comportamento:

| Entrada | Resultado |
|---|---|
| Código existente + Enter | Mostra NOME, CPF, CIDADE e UF. Linha 24 vazia |
| Código inexistente + Enter | Limpa os campos de saída, mensagem `CLIENTE NAO ENCONTRADO` |
| F3 | Volta para T01 |

## 5. Mensagens

Todas na linha 24, coluna 2. Texto exato:

| Mensagem | Tela | Quando |
|---|---|---|
| `OPCAO INVALIDA` | T01 | Opção diferente de 1, 2 e 9 |
| `CLIENTE INCLUIDO` | T02 | Inclusão gravada |
| `CODIGO JA CADASTRADO` | T02 | Código já existe |
| `UF INVALIDA` | T02 | UF fora da lista |
| `CLIENTE NAO ENCONTRADO` | T03 | Código não existe |
| `CADASTRO CHEIO` | T02 | Tabela em memória com 100 registros. Não testada |

## 6. Teclas

| Tecla | Uso |
|---|---|
| Enter | Confirma a tela |
| Tab | Próximo campo |
| Backspace | Apaga o caractere à esquerda |
| F3 | Volta ou sai |
| F12 | Cancela a edição em T02 |

F1, F10 e F11 ficam de fora porque emuladores de terminal e desktops costumam capturá-las.

## 7. Arquivo de dados

`data/clientes.dat`, um cliente por linha, 69 colunas, sem separador:

| Campo | Colunas | Tamanho | Preenchimento |
|---|---|---|---|
| CODIGO | 1–6 | 6 | Zeros à esquerda |
| NOME | 7–36 | 30 | Espaços à direita |
| CPF | 37–47 | 11 | — |
| CIDADE | 48–67 | 20 | Espaços à direita |
| UF | 68–69 | 2 | — |

A UF fica por último de propósito: como nunca é vazia, a linha tem sempre 69 colunas, mesmo que a gravação remova espaços no fim.

Estado inicial, em `app/seed/clientes.dat`:

```
000001MARIA DA SILVA                11111111111RIO DE JANEIRO      RJ
000002JOAO PEREIRA                  22222222222SAO PAULO           SP
```

Os CPFs são sequências de dígitos repetidos, inválidas pela regra do CPF. Não pertencem a ninguém.

## 8. Verificado na implementação (GnuCOBOL 3.2.0, tmux 80x24, 2026-11-12)

- **Campo vazio:** alfanumérico mostra `_` por posição. Numérico (CODIGO, CPF) mostra zeros (`000000`, `00000000000`), não `_`. Os mapas das seções 3 e 4 usam `_` só como marca de campo. Vale também depois de limpar (F12, inclusão gravada).
- **Digitação:** o primeiro dígito digitado sobrescreve a posição 1; digitar os 6 dígitos completos substitui os zeros. O campo OPCAO de T01 é alfanumérico (1 caractere) no app, para aparecer como `_`; qualquer valor diferente de 1, 2 e 9 dá `OPCAO INVALIDA`.
- **Backspace:** apaga o caractere à esquerda dentro do campo (`ANA TESTEX` + BSpace = `ANA TESTE`). **Tab:** avança ao próximo campo; campo preenchido por inteiro não avança sozinho.
- **Espaço no fim da gravação:** o `LINE SEQUENTIAL` remove espaços no fim da linha. Como a UF é o último campo e nunca vazia, a linha gravada tem 69 colunas (conferido com `cat -A`).
- **Enter com erro:** o cursor volta ao primeiro campo (4, 14) com o conteúdo anterior mantido. Observação: ao repintar, espaço dentro de um campo preenchido aparece como `_` (ex.: `UF_ERRADA`), só na tela; o dado em memória está certo. O oráculo não deve comparar o NOME de um erro com a digitação literal.
- **Códigos de CRT STATUS:** Enter = 0000, F3 = 1003, F12 = 1012 (com `COB_SCREEN_EXCEPTIONS=Y`).
- **Capturas de referência:** `tests/golden/*.txt` (capture-pane de cada tela e mensagem).
