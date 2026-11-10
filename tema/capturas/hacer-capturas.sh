#!/usr/bin/env bash
# NeonGrid - genera las capturas y los GIF animados del fondo (para el README y el blog).
# No toca tu escritorio: lanza el fondo dentro de un KWin virtual con datos de demostracion.
# Necesita: qml6, kwin_wayland, ffmpeg, ImageMagick (magick). Uso: hacer-capturas.sh <carpeta-salida> [momento...]
#   momentos: noche dia amanecer atardecer ciclo resoluciones   (por defecto, todos)
set -euo pipefail
AQUI="$(cd "$(dirname "$0")" && pwd)"; PR="$AQUI/../fondo/pruebas"
OUT="$(mkdir -p "${1:?uso: hacer-capturas.sh <carpeta-salida> [momentos]}" && cd "$1" && pwd)"; shift || true
MOM=("$@"); [ ${#MOM[@]} -eq 0 ] && MOM=(noche dia amanecer atardecer ciclo resoluciones)
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
declare -A HORA=([noche]=22 [dia]=12.5 [amanecer]=7.7 [atardecer]=17.0)

lanzar() { # lanzar <guion con la orden>  (probar.sh ejecuta UN fichero dentro del KWin virtual)
  "$PR/probar.sh" "$TMP/h" "$TMP/log" "$1" >/dev/null 2>&1 || true
}
rafaga() { # rafaga <momento> <hora>  -> <salida>/<momento>.gif y <momento>.png
  local m="$1" h="$2" d="$TMP/$1"; mkdir -p "$d"
  printf '#!/bin/sh\nexec qml6 -I "%s/stub" "%s/prueba.qml" -- paquete="%s" hora=%s inicio=6000 fin=60000 rafaga=300 salida=%s/f w=1920 h=1200 "cfg.ComandoDatos=cat %s/datos-presentacion.json"\n' \
    "$PR" "$PR" "$(readlink -f "$PR/../../../paquete/neongrid/share/plasma/wallpapers/org.neongrid.wallpaper")" "$h" "$d" "$PR" > "$TMP/run.sh"; chmod +x "$TMP/run.sh"
  for intento in 1 2 3; do
    lanzar "$TMP/run.sh"
    # el registro dice a que fotograma de la animacion (bucle de 96) corresponde cada captura: se quedan 96 consecutivos
    python3 - "$TMP/log" "$d" <<'PY' && break
import re, sys
log, d = sys.argv[1:3]
seen = {}
for l in open(log, errors="replace"):
    r = re.match(r"qml: captura (\d+) fotograma (\d+)", l)
    if r: seen.setdefault(int(r[2]), int(r[1]))
f0 = next((f for f in sorted(seen) if all(f + k in seen for k in range(96))), None)
assert f0 is not None, f"no hay 96 fotogramas consecutivos (hay {len(seen)} distintos): repite con menos carga en el equipo"
sel = [seen[f0 + k] for k in range(96)]
open(d + "/lista.txt", "w").write("".join(f"file '{d}/f-{n}.png'\nduration 0.125\n" for n in sel))
open(d + "/mitad.txt", "w").write(str(sel[40]))
PY
    echo "  (intento $intento fallido, repito)"
  done
  ffmpeg -v error -y -f concat -safe 0 -i "$d/lista.txt" -vf "scale=1200:-1:flags=area,split[a][b];[a]palettegen=max_colors=160:stats_mode=full[p];[b][p]paletteuse=dither=bayer:bayer_scale=4:diff_mode=rectangle" -loop 0 "$OUT/$m.gif"
  cp "$d/f-$(cat "$d/mitad.txt").png" "$OUT/$m.png"
  echo "  $m: $(du -h "$OUT/$m.gif" | cut -f1)"
}
ciclo() { # 24 horas en 120 fotogramas -> ciclo.gif
  local d="$TMP/ciclo"; mkdir -p "$d"
  printf '#!/bin/sh\nexec qml6 -I "%s/stub" "%s/prueba.qml" -- paquete="%s" hora=0 inicio=6000 fin=120000 ciclo=0:24:120:250 salida=%s/f w=1920 h=1200 "cfg.ComandoDatos=cat %s/datos-presentacion.json"\n' \
    "$PR" "$PR" "$(readlink -f "$PR/../../../paquete/neongrid/share/plasma/wallpapers/org.neongrid.wallpaper")" "$d" "$PR" > "$TMP/run.sh"
  lanzar "$TMP/run.sh"
  ffmpeg -v error -y -framerate 12 -i "$d/f-%d.png" -vf "scale=1200:-1:flags=area,split[a][b];[a]palettegen=max_colors=200:stats_mode=full[p];[b][p]paletteuse=dither=bayer:bayer_scale=4" -loop 0 "$OUT/ciclo.gif"
  echo "  ciclo: $(du -h "$OUT/ciclo.gif" | cut -f1)"
}
resoluciones() { # una captura por resolucion; la pantalla virtual tiene el MISMO tamano (si no, una ventana mayor se recorta sola)
  local r w h d
  for r in ${RES:-1024x768 1280x720 1366x768 1280x1024 1440x900 1920x1080 2560x1440 2560x1600 3440x1440 3840x2160}; do
    w="${r%x*}"; h="${r#*x}"; d="$TMP/res-$r"; mkdir -p "$d"
    printf '#!/bin/sh\nexec qml6 -I "%s/stub" "%s/prueba.qml" -- paquete="%s" hora=22 capturas=7000 fin=9000 salida=%s/f w=%s h=%s "cfg.ComandoDatos=cat %s/datos-presentacion.json"\n' \
      "$PR" "$PR" "$(readlink -f "$PR/../../../paquete/neongrid/share/plasma/wallpapers/org.neongrid.wallpaper")" "$d" "$w" "$h" "$PR" > "$TMP/run.sh"
    NG_W="$(( w > 1920 ? w : 1920 ))" NG_H="$(( (h > 1200 ? h : 1200) + 100 ))" lanzar "$TMP/run.sh"   # pantalla virtual >= ventana
    local tam; tam="$(identify -format '%wx%h' "$d/f-0.png" 2>/dev/null || echo ninguna)"
    [ "$tam" = "$r" ] || { echo "  AVISO: $r salio como $tam (la captura no es de esa resolucion)"; continue; }
    cp "$d/f-0.png" "$OUT/resolucion-$r.png"; echo "  $r: ok"
  done
}
for m in "${MOM[@]}"; do
  case "$m" in ciclo) ciclo;; resoluciones) resoluciones;; *) rafaga "$m" "${HORA[$m]}";; esac
done
