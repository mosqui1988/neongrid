#!/bin/sh
# Ejecuta una orden grafica dentro de un KWin --virtual con D-Bus y HOME propios (no toca el escritorio real).
# Uso: probar.sh <carpeta-temporal> <log> <guion>   (NG_W / NG_H = tamano de la pantalla virtual, por defecto 1920x1300; una ventana mayor se recorta sola)
T="$1"; LOG="$2"; shift 2
mkdir -p "$T/home/.config" "$T/home/.local/share" "$T/home/.cache"
export NG_SESION_CMD="$*" NG_SESION_LOG="$LOG"
env -u WAYLAND_DISPLAY -u DISPLAY HOME="$T/home" XDG_CONFIG_HOME="$T/home/.config" XDG_DATA_HOME="$T/home/.local/share" \
    XDG_CACHE_HOME="$T/home/.cache" QT_FORCE_STDERR_LOGGING=1 QT_QPA_PLATFORM=wayland \
    timeout 300 dbus-run-session -- kwin_wayland --virtual --socket "ng-prueba-$$" --width "${NG_W:-1920}" --height "${NG_H:-1300}" \
    --no-lockscreen --no-global-shortcuts --no-kactivities --exit-with-session "$(dirname "$(readlink -f "$0")")/sesion.sh" > "$T/kwin.log" 2>&1
