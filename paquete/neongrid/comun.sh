# NeonGrid - funciones comunes. Se carga con `. comun.sh` desde instalar/revertir/desinstalar.
# Rutas: respetan XDG_DATA_HOME / XDG_CONFIG_HOME (asi se prueba en una carpeta aislada).
DATA="${XDG_DATA_HOME:-$HOME/.local/share}"
CONF="${XDG_CONFIG_HOME:-$HOME/.config}"
RAIZ="$DATA/neongrid"; COPIA="$RAIZ/copia-previa"; LISTA="$RAIZ/instalado.lista"
TITULO="NeonGrid"
GRAFICO="${GRAFICO:-0}"
# NEONGRID_PRUEBA=1: escribe ajustes en CONF pero NO habla con el Plasma vivo (sin plasma-apply, qdbus ni reinicios).
PRUEBA="${NEONGRID_PRUEBA:-0}"

case "${LC_ALL:-${LC_MESSAGES:-${LANG:-es_ES}}}" in en*) IDIOMA=en;; *) IDIOMA=es;; esac
t() { if [ "$IDIOMA" = en ]; then printf '%s' "$2"; else printf '%s' "$1"; fi; }

[ "$GRAFICO" = 1 ] && ! command -v kdialog >/dev/null 2>&1 && GRAFICO=0

dialogo() { # dialogo TIPO TEXTO   (TIPO: msgbox | error | yesno | aviso)
  if [ "$GRAFICO" = 1 ]; then
    case "$1" in
      msgbox) kdialog --title "$TITULO" --msgbox "$2";;
      error)  kdialog --title "$TITULO" --error "$2";;
      aviso)  kdialog --title "$TITULO" --sorry "$2";;
      yesno)  kdialog --title "$TITULO" --yes-label "${YES:-Aceptar}" --no-label "${NO:-Cancelar}" --yesno "$2";;
    esac
  else
    echo "$2"; [ "$1" = yesno ] && return 0; return 0
  fi
}
fallo() { dialogo error "$1"; exit 1; }
info() { echo "==> $*"; }

QDBUS=""; for q in qdbus6 qdbus-qt6 qdbus; do command -v "$q" >/dev/null 2>&1 && { QDBUS="$q"; break; }; done
viva() { [ "$PRUEBA" != 1 ]; }   # true si se puede tocar el Plasma vivo
shell_script() { # shell_script 'codigo JS'  -> lo ejecuta en plasmashell
  viva && [ -n "$QDBUS" ] && "$QDBUS" org.kde.plasmashell /PlasmaShell org.kde.PlasmaShell.evaluateScript "$1" >/dev/null 2>&1; return 0; }
reiniciar_plasma() { viva || return 0
  systemctl --user restart plasma-plasmashell.service 2>/dev/null || { kquitapp6 plasmashell >/dev/null 2>&1; sleep 1; (kstart plasmashell >/dev/null 2>&1 &); }; }
kwin_recargar() { viva && [ -n "$QDBUS" ] && "$QDBUS" org.kde.KWin /KWin reconfigure >/dev/null 2>&1; return 0; }

plasma6() { local v; v="$(plasmashell --version 2>/dev/null | awk '{print $2}')"; [ "${v%%.*}" -ge 6 ] 2>/dev/null; }

familia() { # imprime arch | debian | fedora | suse | otra
  local id="" like=""; [ -r /etc/os-release ] && . /etc/os-release && { id="${ID:-}"; like="${ID_LIKE:-}"; }
  case " $id $like " in *" arch "*|*" cachyos "*|*" manjaro "*|*" endeavouros "*) echo arch;;
    *" debian "*|*" ubuntu "*) echo debian;; *" fedora "*|*" rhel "*) echo fedora;;
    *" suse "*|*" opensuse"*) echo suse;; *) echo otra;; esac; }
comando_deps() { # comando_deps "paq1 paq2" -> LINEA a MOSTRAR (nunca se ejecuta)
  case "$(familia)" in
    arch) echo "sudo pacman -S --needed $1";; debian) echo "sudo apt install $1";;
    fedora) echo "sudo dnf install $1";; suse) echo "sudo zypper install $1";;
    *) echo "$(t 'instala con el gestor de paquetes de tu distribucion:' 'install with your distribution package manager:') $1";; esac; }

# Ficheros de ~/.config que NeonGrid puede cambiar y que se guardan antes (una sola vez: se conserva el estado ORIGINAL)
FICHEROS_CONF=(kdeglobals kwinrc plasmarc plasmashellrc plasma-org.kde.plasma.desktop-appletsrc konsolerc kcminputrc kscreenlockerrc ksplashrc alacritty/alacritty.toml)
