# SETUP — Preparar o ambiente

Versão 0.1 · 2026-11-11 · Passo a passo da fase F1 do [TASKS.md](TASKS.md). O porquê de cada escolha está no [SPEC-TECH.md](SPEC-TECH.md).

Convenção: **verificado** foi conferido nesta máquina; **a validar** é proposta que a tarefa indicada ainda precisa confirmar. Não trate "a validar" como fato.

## 1. Pré-requisitos (verificado)

Já instalados: Node 24.21.0 (via nvm), npm 12.0.2, Python 3.12.10, pytest 8.3.5, git, tmux 3.6, `mate-terminal`, `xterm`, `Xephyr`, `dbus-run-session`, `marco` 1.26.2, `jq`, `tesseract`, `xclip`, `xdotool`, `wmctrl`.

Conferir de novo:

```bash
for c in node npm python3 pytest git tmux mate-terminal xterm Xephyr dbus-run-session marco jq tesseract; do
  command -v "$c" >/dev/null && echo "ok     $c" || echo "FALTA  $c"
done
```

Faltam: o compilador COBOL (seção 2) e a versão certa do `agent-desktop` (seção 3).

## 2. GnuCOBOL (tarefa T-011, feita por Igor)

O `sudo` pede senha, então este passo é do dono da máquina:

```bash
sudo apt install -y gnucobol3
cobc --version        # esperado: GnuCOBOL 3.2
```

Não instalar `gnucobol4`: é snapshot de desenvolvimento.

## 3. agent-desktop 1.2.0 (tarefa T-012)

O npm global fica dentro do nvm, no diretório do usuário. Não precisa de `sudo` (verificado).

```bash
npm install -g agent-desktop@1.2.0
agent-desktop version      # esperado: 1.2.0
agent-desktop status       # esperado: ok true, accessibility granted
```

O diretório de estado `~/.agent-desktop` precisa ser privado, senão `snapshot` falha com `INTERNAL`. Ele ainda não existe nesta máquina. Depois do primeiro comando que o criar:

```bash
chmod 700 ~/.agent-desktop
```

Não atualizar a versão no meio da POC. Se for inevitável, registrar em "Achados" no TASKS.md e repetir as sondagens.

## 4. Guias embutidos (tarefa T-013)

Ler na versão instalada, antes de escrever qualquer comando no harness:

```bash
agent-desktop skills get desktop
agent-desktop skills get platform
agent-desktop skills get agent-desktop-linux references/display-servers-and-input.md
agent-desktop skills get agent-desktop-linux references/capture-and-clipboard.md
agent-desktop skills get agent-desktop-linux references/troubleshooting.md
agent-desktop <comando> --help
```

Os nomes dos arquivos de referência foram conferidos na versão 1.0.2. Se mudaram na 1.2.0, o guia `platform` lista os atuais. Atualizar as seções 6 e 14 do SPEC-TECH com o que for encontrado.

## 5. Repositório (tarefa T-010)

Feito em 2026-11-12. Decisão D5: repositório público em https://github.com/igorferreira/poc-agent-desktop-test-automation, branch `main`.

O `.gitignore` exclui `evidence/`, `bin/`, `data/`, `__pycache__/` e `.pytest_cache/`. `evidence/` fica fora do git porque envelopes, screenshots e traces podem conter conteúdo do desktop. **O repositório é público: conferir `git status` antes de cada commit e nunca forçar a inclusão de um arquivo ignorado.**

Nesta máquina a variável `GITHUB_TOKEN` tem um token inválido e o `gh` a usa antes do login salvo. Enquanto não for corrigida, rodar o `gh` assim:

```bash
env -u GITHUB_TOKEN gh <comando>
```

## 6. Display isolado (tarefa T-014, a validar)

Decisão D3: tentar primeiro o display isolado. Ele não toma o teclado da sessão real, tem área de transferência própria e não tem atalhos globais.

As flags abaixo existem nos binários desta máquina (verificado). A receita completa, e o `agent-desktop` funcionando dentro dela, ainda não foram testados.

```bash
# 1. Servidor X aninhado. Sem -ac, para manter o controle de acesso.
Xephyr :2 -screen 1024x768 -br -noreset -title CADCLI-DISPLAY &

# 2. Sessão tmux com o app (ou com a tela falsa, na fase F2). Ver SPEC-TECH seção 5.

# 3. Barramento D-Bus próprio, AT-SPI, gerenciador de janelas e terminal.
DISPLAY=:2 dbus-run-session -- bash -c '
  echo "$DBUS_SESSION_BUS_ADDRESS" > "$XDG_RUNTIME_DIR/cadcli-dbus.addr"
  /usr/libexec/at-spi-bus-launcher --launch-immediately --a11y=1 &
  marco &
  mate-terminal --disable-factory --title=CADCLI --geometry=80x24 \
    -e "tmux -L cadcli attach -t cadcli"
'
```

`--disable-factory` faz o `mate-terminal` abrir um processo novo em vez de reaproveitar o da sessão real. Sem isso a janela pode abrir no `DISPLAY=:0`.

Para o `agent-desktop` falar com esse display, e não com a sessão real:

```bash
export DISPLAY=:2
export DBUS_SESSION_BUS_ADDRESS="$(cat "$XDG_RUNTIME_DIR/cadcli-dbus.addr")"
agent-desktop status
agent-desktop list-apps      # deve listar só o terminal do display isolado
```

Critério de pronto: `status` saudável e `list-apps` mostrando o terminal do display `:2` e nenhum app da sessão real. Se `list-apps` mostrar apps da sessão real, o comando está no barramento errado: parar e corrigir antes de qualquer outro comando.

Derrubar: fechar a janela do terminal encerra a sessão D-Bus; depois encerrar o `Xephyr` e rodar `tmux -L cadcli kill-server`.

## 7. Sessão real (recuo)

Só se o display isolado falhar, **e só depois de perguntar a Igor** (decisão D3). Na sessão real, a entrada com `--headed` toma o teclado físico e uma tecla vai para a janela que tiver o foco.

Se for autorizado:

- Fechar ou minimizar apps sensíveis (gerenciador de senhas, mensageiros).
- Seguir as seis regras do SPEC-TECH seção 11, sem exceção.
- Não usar a estratégia L2 (área de transferência) sem autorização explícita.
- Não tocar no teclado nem no mouse durante uma execução.

## 8. Checklist de saída da F1

- [ ] `cobc --version` responde 3.2
- [ ] `agent-desktop version` responde 1.2.0
- [ ] `agent-desktop status` saudável na sessão real
- [ ] `~/.agent-desktop` com permissão 700
- [ ] Guias embutidos lidos; SPEC-TECH seções 6 e 14 atualizadas
- [x] Repositório git criado, `evidence/` ignorado
- [ ] Display isolado: funciona, ou a falha está documentada em "Achados"

## 9. Problemas conhecidos

Só o que tem fonte. O resto se descobre nas sondagens e vai para "Achados".

| Sintoma | Causa | Correção | Fonte |
|---|---|---|---|
| `snapshot` falha com `INTERNAL` | `~/.agent-desktop` não é privado | `chmod 700 ~/.agent-desktop` | README oficial |
| `AMBIGUOUS_TARGET` ao agir no terminal | Há outros terminais abertos | Passar `--window-id` da janela `CADCLI` | README oficial |
| `type` devolve `POLICY_DENIED` | Entrada em terminal exige `--headed` | Usar a estratégia I2 | Guia Linux embutido (1.0.2) |
| F3 e F12 não chegam ao app | GnuCOBOL não devolve teclas de função por padrão | Rodar com `COB_SCREEN_EXCEPTIONS=Y` | A validar em T-030 |
| Janela abre no display errado | `mate-terminal` reaproveitou o processo da sessão real | `--disable-factory` | `mate-terminal --help` |
