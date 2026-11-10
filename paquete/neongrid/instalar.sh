#!/usr/bin/env bash
# NeonGrid - instalador. Solo toca tu usuario (sin sudo) y se puede deshacer.
#   ./instalar.sh                 instala y aplica el tema completo (KDE Plasma 6)
#   ./instalar.sh --grafico       lo mismo con ventanas de KDE (lo que hace el doble clic)
#   ./instalar.sh --sin-aplicar   solo copia los ficheros, sin cambiar tus ajustes
#   ./instalar.sh --sin-fondo     no instala ni pone el fondo animado
#   ./instalar.sh --sin-panel     no cambia tu barra/panel
#   ./instalar.sh --alacritty     tambien configura Alacritty si lo usas
# Para volver atras: ./revertir.sh   |   para quitarlo del todo: ./desinstalar.sh
set -euo pipefail
AQUI="$(cd "$(dirname "$0")" && pwd)"
APLICAR=1; SIN_FONDO=0; SIN_PANEL=0; ALACRITTY=0; GRAFICO=0
for a in "$@"; do case "$a" in
  --grafico) GRAFICO=1;; --sin-aplicar) APLICAR=0;; --sin-fondo) SIN_FONDO=1;; --sin-panel) SIN_PANEL=1;; --alacritty) ALACRITTY=1;;
  -h|--help) sed -n 2,12p "$0"; exit 0;; *) echo "Opcion desconocida: $a" >&2; exit 2;; esac; done
# shellcheck source=comun.sh
. "$AQUI/comun.sh"

# ---- 1. Comprobaciones ----
if [ "$APLICAR" = 1 ] && viva && ! plasma6; then
  fallo "$(t 'NeonGrid necesita KDE Plasma 6 y no lo detecto en este equipo (si tienes Plasma 5, no es compatible). No he tocado nada.' 'NeonGrid needs KDE Plasma 6 and I cannot detect it on this system (Plasma 5 is not supported). Nothing was changed.')"
fi
falta=(); for c in python3 kwriteconfig6 kreadconfig6 fc-cache; do command -v "$c" >/dev/null 2>&1 || falta+=("$c"); done
if [ ${#falta[@]} -gt 0 ]; then
  case "$(familia)" in arch) p="python kconfig fontconfig";; debian) p="python3 kde-cli-tools libkf6config-bin fontconfig";; fedora) p="python3 kf6-kconfig fontconfig";; suse) p="python3 kconfig fontconfig";; *) p="python3 kconfig fontconfig";; esac
  fallo "$(t 'Faltan estas herramientas:' 'Missing tools:') ${falta[*]}
$(t 'Instalalas tu mismo (NeonGrid nunca ejecuta sudo) con algo como:' 'Install them yourself (NeonGrid never runs sudo) with something like:')
  $(comando_deps "$p")
$(t 'Los nombres de paquete pueden variar segun la distribucion.' 'Package names may vary by distribution.')"
fi

# ---- 2. Que se va a hacer (en modo grafico se pregunta) ----
if [ "$GRAFICO" = 1 ]; then
  sel="$(kdialog --title "$TITULO" --checklist "$(t 'Se instalara el tema NeonGrid: colores, ventanas, iconos, cursor, terminal, fuentes y datos.
Antes se guarda una copia de tus ajustes y se puede deshacer. No usa sudo.

Marca lo que quieres aplicar:' 'NeonGrid will be installed: colors, windows, icons, cursor, terminal, fonts and data.
A backup of your settings is made first and it can be undone. No sudo.

Choose what to apply:')" \
      fondo "$(t 'Fondo animado de la ciudad (tambien en el bloqueo)' 'Animated city wallpaper (also on the lock screen)')" on \
      panel "$(t 'Sustituir mi barra por la barra superior de NeonGrid' 'Replace my panel with the NeonGrid top bar')" on \
      alacritty "$(t 'Configurar Alacritty (si lo uso)' 'Configure Alacritty (if I use it)')" off)" || exit 0
  case "$sel" in *fondo*) :;; *) SIN_FONDO=1;; esac
  case "$sel" in *panel*) :;; *) SIN_PANEL=1;; esac
  case "$sel" in *alacritty*) ALACRITTY=1;; esac
fi

# ---- 3. Pasos ----
hacer_copia() {
  [ -e "$COPIA/manifiesto" ] && { info "$(t 'Ya hay copia del estado original: se conserva' 'Original-state backup already exists: kept')"; return 0; }
  mkdir -p "$COPIA/conf"; : > "$COPIA/manifiesto.tmp"
  for f in "${FICHEROS_CONF[@]}"; do
    if [ -e "$CONF/$f" ]; then mkdir -p "$COPIA/conf/$(dirname "$f")"; cp -a "$CONF/$f" "$COPIA/conf/$f"; echo "tenia $f" >> "$COPIA/manifiesto.tmp"
    else echo "nuevo $f" >> "$COPIA/manifiesto.tmp"; fi
  done
  date -Iseconds > "$COPIA/fecha"; mv "$COPIA/manifiesto.tmp" "$COPIA/manifiesto"   # el manifiesto existe solo si la copia esta completa
  info "$(t 'Copia de tus ajustes guardada en' 'Backup of your settings saved in') $COPIA"
}

copiar() { # copiar ORIGEN_REL DESTINO  (rutas relativas a AQUI / absoluta) y lo anota en la lista
  local o="$AQUI/$1" d="$2"
  [ -e "$o" ] || { echo "   (omitido, no existe en el paquete: $1)"; return 0; }
  rm -rf "$d"; mkdir -p "$(dirname "$d")"; cp -a "$o" "$d"; echo "$d" >> "$LISTA.nuevo"
}

principal() {
  mkdir -p "$RAIZ"; : > "$LISTA.nuevo"
  [ -e "$LISTA" ] && cat "$LISTA" >> "$LISTA.nuevo"
  [ "$APLICAR" = 1 ] && hacer_copia

  info "$(t 'Copiando ficheros' 'Copying files')"
  copiar share/color-schemes/NeonGrid.colors "$DATA/color-schemes/NeonGrid.colors"
  copiar share/konsole/NeonGrid.colorscheme "$DATA/konsole/NeonGrid.colorscheme"
  copiar share/konsole/NeonGrid.profile "$DATA/konsole/NeonGrid.profile"
  copiar share/aurorae/themes/NeonGrid "$DATA/aurorae/themes/NeonGrid"
  copiar share/plasma/desktoptheme/NeonGrid "$DATA/plasma/desktoptheme/NeonGrid"
  [ "$SIN_FONDO" = 1 ] || copiar share/plasma/wallpapers/org.neongrid.wallpaper "$DATA/plasma/wallpapers/org.neongrid.wallpaper"
  copiar share/plasma/look-and-feel/org.neongrid.desktop "$DATA/plasma/look-and-feel/org.neongrid.desktop"
  copiar share/icons/NeonGrid "$DATA/icons/NeonGrid"
  copiar share/icons/NeonGrid-cursors "$DATA/icons/NeonGrid-cursors"
  copiar share/fonts/neongrid "$DATA/fonts/neongrid"
  # datos, textos, ejemplos y los propios scripts (para poder revertir/desinstalar despues)
  for d in fuentes i18n ejemplos panel; do copiar "neongrid/$d" "$RAIZ/$d"; done
  copiar GUIA.md "$RAIZ/GUIA.md"
  for s in comun.sh instalar.sh revertir.sh desinstalar.sh configurar.sh LEEME.md; do [ -e "$AQUI/$s" ] && cp -a "$AQUI/$s" "$RAIZ/$s"; done
  chmod +x "$RAIZ"/*.sh "$RAIZ"/fuentes/*.py 2>/dev/null || true
  # accesos del menu para quitar/desinstalar sin buscar la carpeta del paquete
  mkdir -p "$DATA/applications"
  for x in configurar:configurar quitar:revertir desinstalar:desinstalar; do
    n="${x%%:*}"; s="${x##*:}"; f="$DATA/applications/neongrid-$n.desktop"
    case "$n" in
      configurar) nom="$(t 'Configurar' 'Configure')"; ico=preferences-system; arg="";;
      quitar) nom="$(t 'Quitar' 'Remove')"; ico=preferences-desktop-theme; arg=" --grafico";;
      *) nom="$(t 'Desinstalar' 'Uninstall')"; ico=preferences-desktop-theme; arg=" --grafico";;
    esac
    printf '[Desktop Entry]\nType=Application\nName=%s NeonGrid\nComment=NeonGrid\nExec=%s%s\nIcon=%s\nTerminal=false\nCategories=Settings;\n' \
      "$nom" "$RAIZ/$s.sh" "$arg" "$ico" > "$f"; echo "$f" >> "$LISTA.nuevo"
  done
  # cursor: Plasma solo lo busca en ~/.icons
  if [ -d "$DATA/icons/NeonGrid-cursors" ]; then mkdir -p "$HOME/.icons"; ln -sfn "$DATA/icons/NeonGrid-cursors" "$HOME/.icons/NeonGrid-cursors"; echo "$HOME/.icons/NeonGrid-cursors" >> "$LISTA.nuevo"; fi
  # configuracion del usuario de ejemplo (nunca pisa la que ya tiene)
  mkdir -p "$CONF/neongrid"
  for e in config.json agenda.txt consejos.txt repos.txt; do [ -e "$CONF/neongrid/$e" ] || { [ -e "$RAIZ/ejemplos/$e" ] && cp "$RAIZ/ejemplos/$e" "$CONF/neongrid/$e"; }; done
  sort -u "$LISTA.nuevo" > "$LISTA"; rm -f "$LISTA.nuevo"
  fc-cache -f "$DATA/fonts" >/dev/null 2>&1 || true

  if [ "$APLICAR" = 0 ]; then info "$(t 'Copiado. No se ha cambiado ningun ajuste.' 'Copied. No setting was changed.')"; return 0; fi

  info "$(t 'Aplicando ajustes' 'Applying settings')"
  local K="kwriteconfig6"
  $K --file kdeglobals --group General --key ColorScheme NeonGrid
  $K --file kdeglobals --group Icons --key Theme NeonGrid
  $K --file plasmarc --group Theme --key name NeonGrid
  $K --file kcminputrc --group Mouse --key cursorTheme NeonGrid-cursors
  $K --file kwinrc --group org.kde.kdecoration2 --key library org.kde.kwin.aurorae
  $K --file kwinrc --group org.kde.kdecoration2 --key theme __aurorae__svg__NeonGrid
  $K --file konsolerc --group "Desktop Entry" --key DefaultProfile NeonGrid.profile
  if fc-list 2>/dev/null | grep -qi "Chakra Petch"; then
    f="Chakra Petch,10,-1,5,400,0,0,0,0,0,0,0,0,0,0,1"
    for k in font menuFont toolBarFont; do $K --file kdeglobals --group General --key "$k" "$f"; done
  fi
  fc-list 2>/dev/null | grep -qi "Departure Mono" && $K --file kdeglobals --group General --key fixed "Departure Mono,10,-1,5,400,0,0,0,0,0,0,0,0,0,0,1"
  if [ "$SIN_FONDO" = 0 ]; then $K --file kscreenlockerrc --group Greeter --key WallpaperPlugin org.neongrid.wallpaper; fi
  if [ "$ALACRITTY" = 1 ] && [ -e "$RAIZ/ejemplos/alacritty/neongrid.toml" ]; then mkdir -p "$CONF/alacritty"; cp "$RAIZ/ejemplos/alacritty/neongrid.toml" "$CONF/alacritty/alacritty.toml"; fi

  if viva; then
    plasma-apply-colorscheme NeonGrid >/dev/null 2>&1 || true
    plasma-apply-desktoptheme NeonGrid >/dev/null 2>&1 || true
    plasma-apply-cursortheme breeze_cursors >/dev/null 2>&1 || true; sleep 1   # fuerza el evento de cambio (si no, KWin no recarga)
    plasma-apply-cursortheme NeonGrid-cursors >/dev/null 2>&1 || true
    command -v dbus-send >/dev/null 2>&1 && {
      dbus-send --session --type=signal /KIconLoader org.kde.KIconLoader.iconChanged int32:0 2>/dev/null || true
      dbus-send --session --type=signal /KGlobalSettings org.kde.KGlobalSettings.notifyChange int32:4 int32:0 2>/dev/null || true; }
    kwin_recargar
    if [ "$SIN_FONDO" = 0 ]; then
      shell_script 'var ds = desktops(); for (var i = 0; i < ds.length; i++) { ds[i].wallpaperPlugin = "org.neongrid.wallpaper"; }'
    fi
    # Desactiva los elementos visuales de otros temas (widgets en escritorio y paneles). No desinstala nada:
    # solo los quita de la vista; Quitar NeonGrid restaura la disposicion anterior (appletsrc de la copia).
    shell_script 'var ajenos = ["pixelzen.hud", "pixelzen.barra"];   // se compara por sufijo del id del widget
      function limpia(c) { var ws = c.widgets(); for (var j = 0; j < ws.length; j++) { for (var a = 0; a < ajenos.length; a++) { var t = String(ws[j].type); if (t.indexOf(ajenos[a], t.length - ajenos[a].length) >= 0) { ws[j].remove(); break; } } } }
      var ds = desktops(); for (var i = 0; i < ds.length; i++) limpia(ds[i]);
      if (typeof panels === "function") { var ps = panels(); for (var i = 0; i < ps.length; i++) limpia(ps[i]); }'
    if [ "$SIN_PANEL" = 0 ] && [ -e "$RAIZ/panel/aplicar-panel.js" ]; then
      L="$(grep -m1 '^launchers=' "$CONF/plasma-org.kde.plasma.desktop-appletsrc" 2>/dev/null | cut -d= -f2- || true)"
      L="${L:-applications:systemsettings.desktop,preferred://filemanager,preferred://browser,applications:org.kde.konsole.desktop}"
      js="$(sed -e "s|__LANZADORES__|$L|" -e "s|__NUCLEO__|$DATA/plasma/desktoptheme/NeonGrid/icons/nucleo-22.svg|" "$RAIZ/panel/aplicar-panel.js")"
      shell_script "$js"
    fi
    info "$(t 'Reiniciando el escritorio (unos segundos)' 'Restarting the desktop shell (a few seconds)')"; reiniciar_plasma
  fi
}

if [ "$GRAFICO" = 1 ]; then
  LOG="$(mktemp "${TMPDIR:-/tmp}/neongrid-instalar.XXXXXX")"
  kdialog --title "$TITULO" --passivepopup "$(t 'Instalando NeonGrid... unos segundos.' 'Installing NeonGrid... a few seconds.')" 8 2>/dev/null &
  set +e; ( set -e; principal ) >"$LOG" 2>&1; rc=$?; set -e
  [ $rc -eq 0 ] || fallo "$(t 'No se ha podido instalar. Tus ajustes originales no se han perdido.' 'Installation failed. Your original settings are safe.')

$(tail -n 6 "$LOG")

$(t 'Registro completo:' 'Full log:') $LOG"
  dialogo msgbox "$(t 'Listo. NeonGrid esta instalado.

Para volver a como estaba:  Quitar NeonGrid
Para borrarlo del todo:       Desinstalar NeonGrid
(los dos estan tambien en el menu de aplicaciones)' 'Done. NeonGrid is installed.

To go back to how it was:  Remove NeonGrid
To delete it completely:     Uninstall NeonGrid
(both are also in the applications menu)')"
else
  principal
  echo "$(t 'Listo. Para volver atras:' 'Done. To go back:') $RAIZ/revertir.sh   |   $(t 'quitarlo del todo:' 'remove completely:') $RAIZ/desinstalar.sh"
fi
