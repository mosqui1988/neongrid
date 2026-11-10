#!/usr/bin/env bash
# NeonGrid - QUITAR: deja tu escritorio como estaba antes de instalar (usa la copia de tus ajustes).
# No borra los ficheros de NeonGrid, asi que puedes volver a ponerlo con ./instalar.sh.
#   ./revertir.sh [--grafico] [--silencioso]
set -uo pipefail
AQUI="$(cd "$(dirname "$0")" && pwd)"; GRAFICO=0; SILENCIOSO=0
for a in "$@"; do case "$a" in --grafico) GRAFICO=1;; --silencioso) SILENCIOSO=1;; esac; done
. "$AQUI/comun.sh"

[ -e "$COPIA/manifiesto" ] || fallo "$(t 'No encuentro la copia de tus ajustes originales (¿NeonGrid no estaba instalado, o se aplico sin cambiar ajustes?). No he tocado nada.' 'I cannot find the backup of your original settings (was NeonGrid not installed, or installed without changing settings?). Nothing was changed.')"
if [ "$GRAFICO" = 1 ] && [ "$SILENCIOSO" = 0 ]; then
  YES="$(t 'Quitar' 'Remove')"; NO="$(t 'Cancelar' 'Cancel')"
  dialogo yesno "$(t 'Se restauraran tus ajustes de antes de NeonGrid (colores, ventanas, fondo, barra, cursor...). Los ficheros de NeonGrid se quedan por si quieres volver a ponerlo.' 'Your pre-NeonGrid settings will be restored (colors, windows, wallpaper, panel, cursor...). NeonGrid files stay in case you want it back.')" || exit 0
fi

info "$(t 'Restaurando ajustes' 'Restoring settings')"
while read -r estado f; do
  [ -z "$f" ] && continue
  case "$estado" in
    tenia) mkdir -p "$CONF/$(dirname "$f")"; cp -a "$COPIA/conf/$f" "$CONF/$f";;
    nuevo) rm -f "$CONF/$f";;
  esac
done < "$COPIA/manifiesto"

if viva; then
  esq="$(kreadconfig6 --file kdeglobals --group General --key ColorScheme 2>/dev/null)"; [ -n "$esq" ] && plasma-apply-colorscheme "$esq" >/dev/null 2>&1
  tema="$(kreadconfig6 --file plasmarc --group Theme --key name 2>/dev/null)"; plasma-apply-desktoptheme "${tema:-default}" >/dev/null 2>&1
  cur="$(kreadconfig6 --file kcminputrc --group Mouse --key cursorTheme 2>/dev/null)"; plasma-apply-cursortheme "${cur:-breeze_cursors}" >/dev/null 2>&1
  command -v dbus-send >/dev/null 2>&1 && {
    dbus-send --session --type=signal /KIconLoader org.kde.KIconLoader.iconChanged int32:0 2>/dev/null
    dbus-send --session --type=signal /KGlobalSettings org.kde.KGlobalSettings.notifyChange int32:4 int32:0 2>/dev/null; }
  kwin_recargar
  info "$(t 'Reiniciando el escritorio (unos segundos)' 'Restarting the desktop shell (a few seconds)')"; reiniciar_plasma
fi
mkdir -p "$RAIZ"; echo revertido > "$RAIZ/estado"
[ "$SILENCIOSO" = 1 ] && exit 0
dialogo msgbox "$(t 'Listo: tu escritorio esta como antes. Si algo se ve a medias, cierra sesion y vuelve a entrar.' 'Done: your desktop is back as it was. If something looks half-changed, log out and back in.')"
