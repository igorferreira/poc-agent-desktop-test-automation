#!/usr/bin/env bash
# Guarda: roda agent-desktop SOMENTE no display isolado :2 com D-Bus proprio.
set -u
REAL_BUS="${DBUS_SESSION_BUS_ADDRESS:-}"   # barramento da sessao real, antes do source
ENVF="${XDG_RUNTIME_DIR:-}/cadcli-display.env"
[ -r "$ENVF" ] || { echo "ad2: $ENVF ausente; rode display-up.sh" >&2; exit 2; }
set -a; . "$ENVF"; set +a
[ "${DISPLAY:-}" = ":2" ] || { echo "ad2: DISPLAY=${DISPLAY:-} != :2; recusado" >&2; exit 2; }
[ -n "${DBUS_SESSION_BUS_ADDRESS:-}" ] || { echo "ad2: DBUS vazio; recusado" >&2; exit 2; }
if [ "$DBUS_SESSION_BUS_ADDRESS" = "$REAL_BUS" ] || [ "$DBUS_SESSION_BUS_ADDRESS" = "unix:path=/run/user/$(id -u)/bus" ]; then
  echo "ad2: DBUS igual ao da sessao real; recusado" >&2; exit 2
fi
[ -S /tmp/.X11-unix/X2 ] || { echo "ad2: X2 nao existe; recusado" >&2; exit 2; }
exec agent-desktop "$@"
