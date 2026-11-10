#!/usr/bin/env bash
# NeonGrid - DESINSTALAR: revierte tus ajustes y borra todos los ficheros que instalo NeonGrid.
#   ./desinstalar.sh [--grafico] [--todo]     --todo borra tambien ~/.config/neongrid (tu agenda y consejos)
set -uo pipefail
AQUI="$(cd "$(dirname "$0")" && pwd)"; GRAFICO=0; TODO=0
for a in "$@"; do case "$a" in --grafico) GRAFICO=1;; --todo) TODO=1;; esac; done
. "$AQUI/comun.sh"

if [ "$GRAFICO" = 1 ]; then
  YES="$(t 'Desinstalar' 'Uninstall')"; NO="$(t 'Cancelar' 'Cancel')"
  dialogo yesno "$(t 'Se restauraran tus ajustes de antes y se borrara NeonGrid del equipo (tema, fondo, iconos, cursor, fuentes y datos).' 'Your previous settings will be restored and NeonGrid will be deleted (theme, wallpaper, icons, cursor, fonts and data).')" || exit 0
  kdialog --title "$TITULO" --yesno "$(t '¿Borrar tambien tu agenda, consejos y ajustes de NeonGrid (~/.config/neongrid)?' 'Also delete your NeonGrid agenda, tips and settings (~/.config/neongrid)?')" --yes-label "$(t 'Si, borrar' 'Yes, delete')" --no-label "$(t 'No, conservar' 'No, keep')" && TODO=1
fi

if [ -e "$COPIA/manifiesto" ]; then "$AQUI/revertir.sh" --silencioso
else echo "$(t 'No hay copia de ajustes: se borran solo los ficheros.' 'No settings backup: only files are deleted.')"; fi

info "$(t 'Borrando ficheros de NeonGrid' 'Deleting NeonGrid files')"
if [ -e "$LISTA" ]; then
  while IFS= read -r p; do
    [ -z "$p" ] && continue
    # seguridad: solo rutas dentro de las carpetas del usuario y con el nombre de NeonGrid
    case "$p" in "$DATA"/*|"$HOME"/.icons/*) case "$p" in *[Nn]eon[Gg]rid*|*org.neongrid*) rm -rf "$p";; esac;; esac
  done < "$LISTA"
fi
fc-cache -f "$DATA/fonts" >/dev/null 2>&1 || true
[ "$TODO" = 1 ] && rm -rf "$CONF/neongrid"
# la carpeta de datos propia, al final (este script esta dentro de ella cuando se ejecuta desde el menu)
case "$RAIZ" in */neongrid) rm -rf "$RAIZ";; esac
dialogo msgbox "$(t 'NeonGrid desinstalado. Tu escritorio esta como antes.' 'NeonGrid uninstalled. Your desktop is back as it was.')"
exit 0
