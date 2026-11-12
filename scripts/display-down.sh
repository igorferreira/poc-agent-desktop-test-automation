#!/usr/bin/env bash
# Derruba so o que display-up.sh criou. Nao mexe na sessao tmux.
RT="${XDG_RUNTIME_DIR:?XDG_RUNTIME_DIR vazio}"
PIDF="$RT/cadcli-display.pids"
[ -f "$PIDF" ] || { echo "nada a derrubar"; exit 0; }
SPID=$(sed -n 's/^session=//p' "$PIDF")
XPID=$(sed -n 's/^xephyr=//p' "$PIDF")
# Pid file velho (reboot/crash + pid reaproveitado) nao pode matar processo do usuario:
# so age se o pid ainda e o que o up criou (dbus-run-session lider do proprio grupo / Xephyr).
if [[ "$SPID" =~ ^[0-9]+$ && "$SPID" -gt 1 && "$(ps -o pgid= -p "$SPID" 2>/dev/null | tr -d ' ')" = "$SPID" \
   && "$(ps -o comm= -p "$SPID" 2>/dev/null)" == dbus-run-sess* ]]; then
  # -SPID: grupo da sessao (dbus, at-spi, marco, terminal).
  kill -- "-$SPID" 2>/dev/null
fi
sleep 0.5
if [[ "$XPID" =~ ^[0-9]+$ && "$XPID" -gt 1 && "$(ps -o comm= -p "$XPID" 2>/dev/null)" = "Xephyr" ]]; then
  kill "$XPID" 2>/dev/null
fi
rm -f "$PIDF" "$RT/cadcli-display.env" "$RT/cadcli-display.env.tmp" "$RT/cadcli-display.log"
echo "display derrubado"
