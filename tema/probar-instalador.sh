#!/usr/bin/env bash
# Prueba el ciclo instalar -> quitar -> reinstalar -> desinstalar en una casa FALSA (nunca toca tu escritorio).
# Comprueba que: los ajustes cambian al instalar, quedan IDENTICOS tras quitar, y no queda nada tras desinstalar.
set -uo pipefail
R="$(cd "$(dirname "$0")/.." && pwd)"; PKG="$R/paquete/neongrid"
T="$(mktemp -d "${TMPDIR:-/tmp}/neongrid-prueba.XXXXXX")"; H="$T/home"
mkdir -p "$H/.config/alacritty" "$H/.local/share"
cd "$H/.config"
printf '[General]\nColorScheme=BreezeDark\nfont=Noto Sans,10\n[Icons]\nTheme=breeze-dark\n' > kdeglobals
printf '[Theme]\nname=breeze-dark\n' > plasmarc
printf '[Mouse]\ncursorTheme=breeze_cursors\n' > kcminputrc
printf '[org.kde.kdecoration2]\ntheme=Breeze\n' > kwinrc
printf '[Containments][1]\nplugin=org.kde.panel\n' > plasma-org.kde.plasma.desktop-appletsrc
cp -a "$H/.config" "$T/original"
export HOME="$H" XDG_DATA_HOME="$H/.local/share" XDG_CONFIG_HOME="$H/.config" NEONGRID_PRUEBA=1 LANG=es_ES.UTF-8
ok=0; mal=0
ver() { if [ "$1" = 0 ]; then echo "  OK   $2"; ok=$((ok+1)); else echo "  FALLA $2"; mal=$((mal+1)); fi; }
cd "$PKG"
echo "== 1. instalar"
./instalar.sh >"$T/inst1.log" 2>&1; ver $? "instalar.sh termina sin error"
grep -q "ColorScheme=NeonGrid" "$H/.config/kdeglobals"; ver $? "esquema de colores aplicado"
grep -q "cursorTheme=NeonGrid-cursors" "$H/.config/kcminputrc"; ver $? "cursor aplicado"
grep -q "__aurorae__svg__NeonGrid" "$H/.config/kwinrc"; ver $? "decoracion de ventanas aplicada"
[ -e "$H/.local/share/color-schemes/NeonGrid.colors" ]; ver $? "fichero de colores copiado"
[ -e "$H/.local/share/konsole/NeonGrid.profile" ]; ver $? "perfil de Konsole copiado"
[ -e "$H/.local/share/neongrid/revertir.sh" ]; ver $? "scripts de quitar/desinstalar disponibles tras instalar"
[ -e "$H/.local/share/applications/neongrid-quitar.desktop" ]; ver $? "acceso 'Quitar' en el menu"
echo "== 2. quitar (revertir)"
"$H/.local/share/neongrid/revertir.sh" >"$T/rev.log" 2>&1; ver $? "revertir.sh termina sin error"
diff -r "$T/original" "$H/.config" -x neongrid >"$T/diff.txt" 2>&1; ver $? "los ajustes quedan IDENTICOS a los originales"
[ -s "$T/diff.txt" ] && head -20 "$T/diff.txt"
[ -e "$H/.local/share/color-schemes/NeonGrid.colors" ]; ver $? "los ficheros de NeonGrid siguen ahi (se puede reinstalar)"
echo "== 3. reinstalar (la copia original se conserva)"
./instalar.sh >"$T/inst2.log" 2>&1; ver $? "reinstalar sin error"
grep -q "ColorScheme=NeonGrid" "$H/.config/kdeglobals"; ver $? "vuelve a aplicarse"
echo "== 4. desinstalar"
"$H/.local/share/neongrid/desinstalar.sh" >"$T/des.log" 2>&1; ver $? "desinstalar.sh termina sin error"
diff -r "$T/original" "$H/.config" -x neongrid >"$T/diff2.txt" 2>&1; ver $? "ajustes identicos a los originales tras desinstalar"
resto="$(find "$H/.local/share" "$H/.icons" -iname '*neongrid*' 2>/dev/null | head)"
[ -z "$resto" ]; ver $? "no queda ningun fichero de NeonGrid en .local/share ni .icons"
[ -n "$resto" ] && echo "$resto"
echo; echo "Resultado: $ok correctas, $mal fallos.   (casa falsa: $T)"
[ "$mal" = 0 ]
