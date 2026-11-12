#!/usr/bin/env bash
# Derruba so o que display-up.sh criou. Nao mexe na sessao tmux.
RT="${XDG_RUNTIME_DIR:?XDG_RUNTIME_DIR vazio}"
PIDF="$RT/cadcli-display.pids"
[ -f "$PIDF" ] || { echo "nada a derrubar"; exit 0; }
SPID=$(sed -n 's/^session=//p' "$PIDF")
XPID=$(sed -n 's/^xephyr=//p' "$PIDF")
# -SPID: grupo da sessao (dbus, at-spi, marco, terminal).
[ -n "$SPID" ] && kill -- "-$SPID" 2>/dev/null
sleep 0.5
[ -n "$XPID" ] && kill "$XPID" 2>/dev/null
rm -f "$PIDF" "$RT/cadcli-display.env" "$RT/cadcli-display.env.tmp" "$RT/cadcli-display.log"
echo "display derrubado"
