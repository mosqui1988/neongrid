#!/bin/sh
# caso.sh <salida> <hora> <fin_ms> <capturas> [w] [h] [extra cfg.*=...]
D="$(dirname "$(readlink -f "$0")")"
PQ="$D/../../../paquete/neongrid/share/plasma/wallpapers/org.neongrid.wallpaper"
S="$1"; HORA="$2"; FIN="$3"; CAP="$4"; W="${5:-1920}"; H="${6:-1200}"; shift 6 2>/dev/null || shift $#
exec qml6 -I "$D/stub" "$D/prueba.qml" -- paquete="$(readlink -f "$PQ")" hora="$HORA" fin="$FIN" capturas="$CAP" salida="$S" w="$W" h="$H" \
  "cfg.ComandoDatos=cat $D/datos-ejemplo.json" "$@"
