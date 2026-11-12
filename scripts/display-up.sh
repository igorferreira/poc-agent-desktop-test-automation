#!/usr/bin/env bash
# Sobe display isolado: Xephyr :2 + D-Bus proprio + AT-SPI + marco + terminal CADCLI.
# Uso: display-up.sh [--terminal mate-terminal|xterm] [--direct]
# --direct: sem tmux; o terminal roda a tela falsa direto (sondagem P8b).
set -euo pipefail

TERM_KIND=mate-terminal
DIRECT=0
while [ $# -gt 0 ]; do
  case "$1" in
    --terminal) TERM_KIND="${2:-}"; shift 2;;
    --direct) DIRECT=1; shift;;
    *) echo "argumento invalido: $1" >&2; exit 2;;
  esac
done
case "$TERM_KIND" in mate-terminal|xterm) ;; *) echo "terminal invalido: $TERM_KIND" >&2; exit 2;; esac

RT="${XDG_RUNTIME_DIR:?XDG_RUNTIME_DIR vazio}"
ENVF="$RT/cadcli-display.env"
PIDF="$RT/cadcli-display.pids"
NUM=2

[ -e "$PIDF" ] && { echo "ja existe $PIDF; rode display-down.sh antes" >&2; exit 1; }
[ -e "/tmp/.X11-unix/X$NUM" ] && { echo "display :$NUM ocupado" >&2; exit 1; }

# Sessao tmux provisoria, so se a real ainda nao existe.
if [ "$DIRECT" = 0 ] && ! tmux -L cadcli has-session -t cadcli 2>/dev/null; then
  setsid tmux -L cadcli -f /dev/null new-session -d -s cadcli -x 80 -y 24 bash
  tmux -L cadcli set -g status off
  echo "sessao tmux provisoria criada (bash)"
fi

# Sem -ac: controle de acesso mantido.
Xephyr ":$NUM" -screen 1024x768 -br -noreset -title CADCLI-DISPLAY >/dev/null 2>&1 &
XPID=$!
for _ in $(seq 50); do [ -S "/tmp/.X11-unix/X$NUM" ] && break; sleep 0.1; done
[ -S "/tmp/.X11-unix/X$NUM" ] || { kill "$XPID" 2>/dev/null; echo "Xephyr nao subiu" >&2; exit 1; }

# Sessao propria (setsid): o pid vira o pgid, e o down mata o grupo todo.
rm -f "$ENVF"
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export TERM_KIND ENVF DIRECT DIR
DISPLAY=":$NUM" setsid dbus-run-session -- bash -c '
  printf "DISPLAY=:2\nDBUS_SESSION_BUS_ADDRESS=%s\n" "$DBUS_SESSION_BUS_ADDRESS" > "$ENVF.tmp"
  /usr/libexec/at-spi-bus-launcher --launch-immediately --a11y=1 &
  for _ in $(seq 50); do
    dbus-send --session --print-reply --dest=org.freedesktop.DBus /org/freedesktop/DBus \
      org.freedesktop.DBus.NameHasOwner string:org.a11y.Bus 2>/dev/null | grep -q true && break
    sleep 0.1
  done
  marco &
  if [ "$DIRECT" = 1 ]; then
    if [ "$TERM_KIND" = xterm ]; then
      exec xterm -T CADCLI -geometry 80x24 -e python3 "$DIR/fake_screen.py"
    else
      exec mate-terminal --disable-factory --title=CADCLI --geometry=80x24 -e "python3 $DIR/fake_screen.py"
    fi
  elif [ "$TERM_KIND" = xterm ]; then
    exec xterm -T CADCLI -geometry 80x24 -e tmux -L cadcli attach -t cadcli
  else
    exec mate-terminal --disable-factory --title=CADCLI --geometry=80x24 \
      -e "tmux -L cadcli attach -t cadcli"
  fi
' >"$RT/cadcli-display.log" 2>&1 &
SPID=$!
echo "xephyr=$XPID" > "$PIDF"
echo "session=$SPID" >> "$PIDF"

for _ in $(seq 50); do [ -s "$ENVF.tmp" ] && break; sleep 0.1; done
[ -s "$ENVF.tmp" ] || { echo "sessao D-Bus nao subiu" >&2; exit 1; }
mv "$ENVF.tmp" "$ENVF"
echo "pronto: source $ENVF"
