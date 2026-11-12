# AGENT — Como executar um caso da Fase B

Você é um agente de IA. Vai executar **um** caso de teste num app de tela verde, o CADCLI. O caso está em `cases/C<n>.md`. Este arquivo diz como ver a tela, como digitar e como entregar o resultado. Use só comandos de shell.

Quem decide se o caso passou é um oráculo independente, não você. Seu trabalho é fazer o que o caso pede e relatar com exatidão o que a tela mostrou.

## 1. Antes de começar

- O operador já subiu o ambiente (`python3 -m harness env up`), restaurou os dados e reiniciou o app. O app deve estar no menu (tela `T01`).
- Você **não** sobe, derruba nem reinicia nada. Se o ambiente não estiver pronto, pare e avise o operador.
- O operador passou um `run_id` (exemplo: `B-C3-r1-20261112-150000`). Sem `run_id`, pare e peça.
- Rode todo comando a partir da raiz do repositório (a pasta que contém `cases/`). Se o seu shell não guarda o diretório entre chamadas, comece cada comando com `cd <raiz> &&`.
- Variáveis de shell podem não sobreviver entre chamadas. Por isso todo bloco abaixo começa definindo `W`. Cole o window-id literal em cada bloco.
- Arquivos auxiliares (scripts, notas, saídas salvas) só podem ir em `evidence/<run_id>/`. Em nenhum outro lugar.

Primeiro comando do caso (marca o início e cria a pasta de evidência):

```bash
mkdir -p evidence/<run_id>/screens && date +%s > evidence/<run_id>/t0
```

## 2. O que você pode e não pode ler

Pode ler:

- `cases/AGENT.md` (este arquivo) e o `cases/C<n>.md` do seu caso.
- `SCREENS.md`, seções 1 a 6 (layout das telas, mensagens, teclas).
- As saídas dos comandos `scripts/ad2.sh` que você rodar.

Proibido ler ou rodar (é o oráculo ou entrega a resposta):

- `data/clientes.dat`, `app/` (inclusive `app/seed/` e o fonte COBOL).
- `tests/` inteiro, inclusive `tests/golden/`.
- `scripts/oracle_capture.sh` e qualquer `tmux` (`tmux capture-pane` inclusive).
- `harness/` (o código tem as respostas esperadas), `TEST-PLAN.md`, `SCREENS.md` seções 7 e 8.
- `evidence/` de outras execuções.
- `python3 -m harness run`, `verify`, `env up` e `env down`.

Você tem que ler a tela pelo `agent-desktop`. O que você declarar tem que ter vindo da tela, não de documento.

## 3. A única porta de entrada: `scripts/ad2.sh`

- Rode o `agent-desktop` **somente** por `scripts/ad2.sh <comando> ...`. Nunca chame `agent-desktop` direto, nem `npx agent-desktop`, nem `agent-desktop mcp`.
- O `ad2.sh` carrega sozinho o ambiente do display isolado (`$XDG_RUNTIME_DIR/cadcli-display.env`: `DISPLAY=:2` e um D-Bus próprio). Ele recusa rodar fora do display `:2`.
- **Não** rode `source "$XDG_RUNTIME_DIR/cadcli-display.env"` no seu shell. O `ad2.sh` compara o D-Bus de antes com o de depois de carregar o arquivo. Se você já carregou, os dois ficam iguais e ele recusa com `ad2: DBUS igual ao da sessao real; recusado`.
- Não exporte `DISPLAY` nem `DBUS_SESSION_BUS_ADDRESS` à mão.
- Para conferir que o ambiente está no ar, sem carregar nada:

```bash
grep '^DISPLAY=' "$XDG_RUNTIME_DIR/cadcli-display.env"     # esperado: DISPLAY=:2
```

Cada comando devolve um envelope JSON. Confira `"ok": true`. Em erro, leia `error.code`. Use `jq` para filtrar.

Opcional: o guia da ferramenta está em `scripts/ad2.sh skills get desktop`. Ajuda de um comando: `scripts/ad2.sh <comando> --help`. Não invente flags.

## 4. Achar a janela (window-id)

```bash
scripts/ad2.sh list-windows --app mate-terminal | jq -r '"ok=\(.ok) erro=\(.error.code // "-")", (.data[]? | select(.title == "CADCLI") | .id)'
```

- A primeira linha mostra `ok` e `error.code`. As demais são os ids das janelas com título exato `CADCLI`.
- Sem janela nenhuma, `data` vem `null`. Por isso o `.data[]?`: com `.data[]` o `jq` quebra.
- Esperado: exatamente uma linha de id, no formato `w-...`. Esse é o `W`.
- Zero ids ou mais de um: pare e avise o operador.
- Exceção: no C2, depois de sair do sistema, nenhuma janela `CADCLI` é o resultado esperado. Não é erro para parar. Grave o resultado.
- Sempre `list-windows` com `--app mate-terminal`. Nunca sem `--app`.

## 5. Ler a tela

### L2 (principal): menu Editar, área de transferência

É a mesma sequência do harness: limpar a área de transferência; abrir o menu `Editar` e clicar `Selecionar tudo`; abrir `Editar` de novo e clicar `Copiar`; ler a área de transferência. Os cliques são semânticos (sem `--headed`) e não precisam da guarda de foco. Cada ref vale só para o `find` que a criou, por isso há um `find` antes de cada `click`.

```bash
W='w-COLE-AQUI'
(
  set -o pipefail
  scripts/ad2.sh clipboard-clear | jq -e '.ok == true' >/dev/null || { echo "ERRO: clipboard-clear"; exit 1; }
  for ITEM in 'Selecionar tudo' 'Copiar'; do
    M=$(scripts/ad2.sh find --window-id "$W" --role menu --name Editar --exact --first | jq -er '.data.match.ref_id') \
      || { echo "ERRO: menu Editar nao encontrado"; exit 1; }
    scripts/ad2.sh click "$M" | jq -e '.ok == true' >/dev/null || { echo "ERRO: click Editar"; exit 1; }
    I=$(scripts/ad2.sh find --window-id "$W" --role menuitem --name "$ITEM" --exact --first | jq -er '.data.match.ref_id') \
      || { echo "ERRO: item $ITEM nao encontrado"; exit 1; }
    scripts/ad2.sh click "$I" | jq -e '.ok == true' >/dev/null || { echo "ERRO: click $ITEM"; exit 1; }
  done
  scripts/ad2.sh clipboard-get --format text | jq -er '.data.text' | cat -n
)
```

Como interpretar:

- A saída é a tela, uma linha por linha, numerada pelo `cat -n`. Linha 1 é a primeira.
- A tela tem 24 linhas. Se vierem menos, as que faltam estão vazias. Linha 24 vazia = sem mensagem.
- O texto termina com uma quebra de linha, por isso o `cat -n` mostra uma 25ª linha vazia. Ignore-a, ou troque `| cat -n` por `| head -24 | cat -n`.
- Saiu `null`, nada, ou `ERRO`: repita a leitura **uma** vez. Falhou de novo: pare (seção 8).
- Se a leitura falhou no meio, o menu `Editar` pode ter ficado aberto. Não envie tecla nenhuma antes de uma leitura completa dar certo.
- A área de transferência é do display isolado, por isso `clipboard-*` não leva `--window-id`. É a única exceção à regra do `--window-id`.

### L3 (alternativa): screenshot

Use só se a L2 falhar duas vezes seguidas e você conseguir ver imagens.

```bash
W='w-COLE-AQUI'; N=01
scripts/ad2.sh screenshot --window-id "$W" "$PWD/evidence/<run_id>/screens/tela-$N.png" | jq '.ok'
```

Depois abra o PNG com a sua ferramenta de ler imagem. Cuidado com `0`/`O`, `1`/`I` e `J`/`3`: o app só usa maiúsculas e dígitos, e código e CPF são só dígitos.

### Como entender a tela

- Linha 1: `CADCLI` à esquerda, título no centro, identificador da tela à direita (`T01`, `T02` ou `T03`). O identificador é a forma oficial de saber em que tela você está.
- Linha 23: teclas disponíveis naquela tela (por exemplo `F3=...`, `ENTER=...`).
- Linha 24: mensagem do sistema. Vazia quando não há mensagem.
- Campo numérico vazio aparece como zeros (`000000`). Campo de texto vazio aparece como `_`.
- Depois de um erro, o app repinta o formulário e um espaço dentro de campo preenchido pode aparecer como `_` (exemplo: `UF_ERRADA`). Isso é só na tela.

## 6. Mandar texto e teclas

### Regra de ouro: guarda de foco antes de cada envio

Uma tecla física vai para a janela que tiver o foco, seja ela qual for. Antes de **cada** envio (texto ou tecla): `focus-window` na CADCLI, depois conferir em `list-windows` que a janela `W` tem `is_focused: true`. Sem confirmação: **não envie** e pare. Os blocos abaixo já fazem isso. Não remova a guarda.

### Texto (dígitos, letras maiúsculas, espaço)

Texto vai por `--headed type` no nó `Terminal` da janela. A ref do nó vem de um `find` feito logo antes.

```bash
W='w-COLE-AQUI'; TEXTO='000100'
(
  case "$TEXTO" in ''|*[![:upper:][:digit:]\ ]*) echo "ABORTAR: texto vazio ou com caractere proibido"; exit 1;; esac
  scripts/ad2.sh focus-window --window-id "$W" | jq -e '.ok == true' >/dev/null || { echo "ABORTAR: focus-window falhou"; exit 1; }
  ok=0
  for i in $(seq 20); do
    scripts/ad2.sh list-windows --app mate-terminal \
      | jq -e --arg w "$W" 'any(.data[]; .id == $w and .is_focused == true)' >/dev/null && { ok=1; break; }
  done
  [ "$ok" = 1 ] || { echo "ABORTAR: foco nao confirmado"; exit 1; }
  T=$(scripts/ad2.sh find --window-id "$W" --role textfield --name Terminal --exact --first | jq -er '.data.match.ref_id') \
    || { echo "ERRO: no Terminal nao encontrado"; exit 1; }
  scripts/ad2.sh --headed type "$T" "$TEXTO"
)
```

- O texto não pode ter Tab nem nova linha. Tab e Enter são teclas (abaixo).
- Campos numéricos (código, CPF) vão sempre com todos os dígitos: `000100`, não `100`.
- Para trocar um valor já digitado no campo, digite de novo todos os dígitos: eles sobrescrevem o anterior. Em `T03`, um código novo de 6 dígitos substitui o anterior.

### Teclas

Teclas vão por `press` com `--window-id`, sem `--headed`.

| Tecla na tela (linha 23) | `TECLA` |
|---|---|
| ENTER | `return` |
| Tab (próximo campo) | `tab` |
| Backspace (apaga à esquerda) | `delete` (no `agent-desktop`, `delete` é o Backspace; verificado) |
| F3 | `f3` |
| F12 | `f12` |

```bash
W='w-COLE-AQUI'; TECLA='return'
(
  case "$TECLA" in return|tab|delete|f3|f12) ;; *) echo "ABORTAR: tecla proibida"; exit 1;; esac
  scripts/ad2.sh focus-window --window-id "$W" | jq -e '.ok == true' >/dev/null || { echo "ABORTAR: focus-window falhou"; exit 1; }
  ok=0
  for i in $(seq 20); do
    scripts/ad2.sh list-windows --app mate-terminal \
      | jq -e --arg w "$W" 'any(.data[]; .id == $w and .is_focused == true)' >/dev/null && { ok=1; break; }
  done
  [ "$ok" = 1 ] || { echo "ABORTAR: foco nao confirmado"; exit 1; }
  scripts/ad2.sh press "$TECLA" --window-id "$W"
)
```

- Só essas cinco teclas. Nenhuma combinação (`ctrl+...`, `alt+...`). Nunca `--force`.
- Você pode colocar vários envios num comando só, desde que cada envio tenha a própria guarda.
- Pode definir a guarda como função de shell no mesmo comando e chamá-la antes de cada envio. Exemplo (Tab e depois ENTER):

```bash
W='w-COLE-AQUI'
(
  guarda() {
    scripts/ad2.sh focus-window --window-id "$W" | jq -e '.ok == true' >/dev/null || return 1
    for i in $(seq 20); do
      scripts/ad2.sh list-windows --app mate-terminal \
        | jq -e --arg w "$W" 'any(.data[]; .id == $w and .is_focused == true)' >/dev/null && return 0
    done
    return 1
  }
  guarda || { echo "ABORTAR: foco nao confirmado"; exit 1; }
  scripts/ad2.sh press tab --window-id "$W"
  guarda || { echo "ABORTAR: foco nao confirmado"; exit 1; }
  scripts/ad2.sh press return --window-id "$W"
)
```

  Para texto, a ordem é a mesma do bloco de texto: `guarda`, `find` do nó `Terminal`, `--headed type`.

### Como operar o app

- Menu (`T01`): digite o número da opção e aperte ENTER.
- Formulário (`T02`): o cursor começa no primeiro campo. Digite o valor e aperte Tab para ir ao próximo. O campo cheio **não** avança sozinho. No último campo, ENTER confirma o formulário.
- Errou a digitação num formulário antes de confirmar: F12 limpa o formulário em `T02`. Comece o formulário de novo.
- Siga a linha 23 para saber o que cada tecla faz em cada tela.

### Esperar o efeito

- `type` e `press` respondem `delivered_unverified`. Entrega não prova efeito.
- Depois de cada passo que deve mudar a tela (ENTER, F3, F12, ou o fim de uma digitação que você quer conferir), leia a tela (seção 5).
- Ainda não mudou: leia de novo. No máximo 5 leituras. Não use `sleep`.
- Não mudou depois de 5 leituras: pare (seção 8).

## 7. Regras de segurança (obrigatórias)

1. Só `scripts/ad2.sh`. Nunca `agent-desktop` direto.
2. Todo comando que mira uma janela leva `--window-id` da CADCLI. Nunca `snapshot`, `screenshot` ou `find` sem `--window-id` ou em outra janela.
3. `list-windows` sempre com `--app mate-terminal`. Não use `list-apps`, nem `focus-window --app` ou `--title`.
4. Guarda de foco antes de cada envio. Sem foco confirmado, nada é enviado e o caso para.
5. Só as teclas da tabela da seção 6. Nunca `--force`.
6. Só os dados do caso. Todos são sintéticos. Não digite mais nada.
7. Não mexa em processos: não reinicie D-Bus nem AT-SPI, não mate processo, não use `tmux`, não rode `app/reset.sh` nem `app/run.sh`.
8. Não edite arquivo do repositório. Você só escreve em `evidence/<run_id>/`. Não faça commit. `evidence/` não vai para o git.
9. Não use a sessão gráfica real (`DISPLAY=:0`). Nunca.

## 8. Se algo falhar

- **Não improvise fora da janela.** Não tente consertar o ambiente.
- `ad2: ... recusado`: problema de ambiente. Pare e avise o operador.
- Envelope com `"ok": false`: leia `error.code` e `error.disposition`.
  - Repita o mesmo comando, **uma** vez, só se `error.disposition.retry` for `safe`.
  - `STALE_REF`: a ref venceu. Rode o bloco inteiro de novo (ele faz um `find` novo).
  - `TIMEOUT` com `lock_timeout`: outro processo está digitando. Pare e avise o operador.
  - `type` ou `press` com erro e `delivery` diferente de `not_delivered`: **não** reenvie. Leia a tela para saber se chegou.
- Foco não confirmado (`ABORTAR`): pare. Não envie nada.
- Tela diferente do que o caso espera e você não sabe por quê: pare.
- A janela `CADCLI` sumiu antes do fim do caso: pare.

Ao parar, grave mesmo assim o `agent-result.json` (seção 9), com o que você já viu, e acrescente a chave `"abortado": "<motivo em uma frase>"`.

## 9. Gravar o resultado

Ao terminar (ou ao parar), grave `evidence/<run_id>/agent-result.json`:

```bash
D=$(( $(date +%s) - $(cat evidence/<run_id>/t0) ))     # duration_s
cat > evidence/<run_id>/agent-result.json <<EOF
{
  "case": "C<n>",
  "agent": "claude-code",
  "model": "<identificador do modelo>",
  "claims": { "<chave do C<n>.md>": "TEXTO LIDO NA TELA" },
  "tool_calls": <numero>,
  "duration_s": $D,
  "tokens": null
}
EOF
jq . evidence/<run_id>/agent-result.json
```

| Chave | Valor |
|---|---|
| `case` | Identificador do caso, exatamente como no nome do arquivo: `"C1"` a `"C5"` |
| `agent` | Nome da ferramenta de IA: `"claude-code"`, `"codex"` etc. |
| `model` | Identificador do modelo que o ambiente informar. Não sabe: `"desconhecido"` |
| `claims` | Objeto com as chaves que o seu `cases/C<n>.md` pede. Nada além delas |
| `tool_calls` | Inteiro: número de chamadas de ferramenta que você fez neste caso. Conta a leitura dos dois `.md` e o comando que grava este JSON. Vários `ad2.sh` dentro de uma chamada contam como uma |
| `duration_s` | Inteiro: segundos desde o `t0` (o `$D` acima) |
| `tokens` | Inteiro com o total de tokens, se você souber. Senão `null` |
| `abortado` | Só se você parou antes do fim: o motivo |
| `aprovacao_manual` | Só se você roda como subagente e os comandos não passaram por aprovação manual do operador: `false` |

O heredoc sem aspas (`<<EOF`) troca `$D` pelo número. Por isso não use `$` nem crase nos valores.

Regras dos valores em `claims`:

- Texto exatamente como na tela, em maiúsculas, sem espaços nas pontas.
- Listas são listas JSON (`["A", "B"]`), na ordem pedida.
- Declare só o que você leu na tela. Não leu: deixe a chave de fora e explique em `abortado`.

O `jq .` no fim tem que imprimir o JSON sem erro. Depois disso, o caso acabou. Não rode `harness verify`: isso é do operador.
