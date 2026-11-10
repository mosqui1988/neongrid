#!/usr/bin/env bash
# NeonGrid - CONFIGURAR: menu con ventanas de KDE para lo mas habitual (repos git, agenda, consejos, ciudad, calma).
# No hace falta tocar ficheros a mano; todo se guarda en ~/.config/neongrid/ (ver GUIA.md).
#   ./configurar.sh
set -uo pipefail
AQUI="$(cd "$(dirname "$0")" && pwd)"; GRAFICO=1
. "$AQUI/comun.sh"
command -v kdialog >/dev/null 2>&1 || { echo "$(t 'Necesito kdialog (paquete "kdialog").' 'I need kdialog (package "kdialog").')"; exit 1; }

CFG="$CONF/neongrid"; EJ="$AQUI/ejemplos"; [ -d "$EJ" ] || EJ="$AQUI/neongrid/ejemplos"; mkdir -p "$CFG"
for e in config.json agenda.txt consejos.txt repos.txt; do
  [ -e "$CFG/$e" ] || { [ -e "$EJ/$e" ] && cp "$EJ/$e" "$CFG/$e"; }
done
[ -e "$CFG/repos.txt" ] || : > "$CFG/repos.txt"

lista_repos() { grep -v -E '^[[:space:]]*(#|$)' "$CFG/repos.txt" 2>/dev/null | sed 's/^[[:space:]]*//; s/[[:space:]]*$//'; }
kd() { kdialog --title "$TITULO" "$@"; }

# ajusta_json CLAVE VALOR_JSON  -> cambia una clave de config.json sin tocar el resto
ajusta_json() {
  python3 - "$CFG/config.json" "$1" "$2" <<'PY'
import json, sys
p, k, v = sys.argv[1:4]
try:
    d = json.load(open(p, encoding="utf-8"))
except Exception:
    d = {}
d[k] = json.loads(v)
json.dump(d, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
PY
}
lee_json() { python3 - "$CFG/config.json" "$1" <<'PY'
import json, sys
try:
    print(json.dumps(json.load(open(sys.argv[1], encoding="utf-8")).get(sys.argv[2])))
except Exception:
    print("null")
PY
}

# ------------------------------------------------------------------ repos git
anadir_repo() {
  local d corto
  d="$(kd --getexistingdirectory "$HOME" 2>/dev/null)" || return 0
  [ -n "$d" ] || return 0
  d="${d%/}"
  if [ ! -d "$d/.git" ]; then
    kd --sorry "$(t "Esa carpeta no es un repositorio git (no tiene .git dentro):
$d

Elige la carpeta del proyecto, la que contiene .git." "That folder is not a git repository (no .git inside):
$d

Pick the project folder, the one containing .git.")"; return 0
  fi
  corto="$d"; case "$d" in "$HOME"/*) corto="~${d#"$HOME"}";; esac
  if lista_repos | grep -qxF "$corto"; then kd --msgbox "$(t 'Ya estaba en la lista:' 'Already in the list:') $corto"; return 0; fi
  if [ -z "$(lista_repos)" ]; then
    kd --yes-label "$(t 'Seguir' 'Continue')" --no-label "$(t 'Cancelar' 'Cancel')" --yesno "$(t \
"Ahora NeonGrid busca repos solo por tus carpetas habituales (Proyectos, src, dev...).

Si añades este, vigilará SOLO los que tú añadas. Puedes volver al modo automático desde este mismo menú." \
"Right now NeonGrid finds repos by itself in your usual folders (Projects, src, dev...).

If you add this one, it will watch ONLY the ones you add. You can go back to automatic from this menu.")" || return 0
  fi
  [ -s "$CFG/repos.txt" ] && [ -n "$(tail -c1 "$CFG/repos.txt")" ] && echo >> "$CFG/repos.txt"
  echo "$corto" >> "$CFG/repos.txt"
  kd --passivepopup "$(t 'Añadido:' 'Added:') $corto" 4
}

quitar_repo() {
  local args=() l sel tmp
  while IFS= read -r l; do [ -n "$l" ] && args+=("$l" "$l" off); done < <(lista_repos)
  if [ ${#args[@]} -eq 0 ]; then kd --msgbox "$(t 'No hay ningún repo en la lista (ahora se buscan solos).' 'No repos in the list (they are found automatically).')"; return 0; fi
  sel="$(mktemp)"
  kd --separate-output --checklist "$(t 'Marca los que quieres quitar:' 'Tick the ones to remove:')" "${args[@]}" > "$sel" 2>/dev/null || { rm -f "$sel"; return 0; }
  if [ -s "$sel" ]; then
    tmp="$(mktemp)"
    awk 'NR==FNR { s[$0] = 1; next } { l = $0; gsub(/^[ \t]+|[ \t]+$/, "", l); if (!(l in s)) print $0 }' "$sel" "$CFG/repos.txt" > "$tmp" && mv "$tmp" "$CFG/repos.txt"
    kd --passivepopup "$(t 'Quitados.' 'Removed.')" 3
  fi
  rm -f "$sel"
}

repos_automatico() {
  kd --yes-label "$(t 'Sí, automático' 'Yes, automatic')" --no-label "$(t 'Cancelar' 'Cancel')" --yesno "$(t \
'¿Volver a la búsqueda automática? Se vaciará tu lista de repos (queda el fichero con las instrucciones).' \
'Go back to automatic search? Your repo list will be emptied (the file stays, with instructions).')" || return 0
  grep -E '^[[:space:]]*(#|$)' "$CFG/repos.txt" > "$CFG/repos.txt.tmp" 2>/dev/null; mv "$CFG/repos.txt.tmp" "$CFG/repos.txt"
  kd --passivepopup "$(t 'Listo: búsqueda automática.' 'Done: automatic search.')" 4
}

# ------------------------------------------------------------------ ciudad
poner_ciudad() {
  local v r
  v="$(kd --inputbox "$(t \
'Tu ciudad en coordenadas «latitud longitud», por ejemplo:  39.47 -0.38
(Valencia: 39.47 -0.38 · Madrid: 40.42 -3.70 · Barcelona: 41.39 2.17)
Búscalas en cualquier mapa (clic derecho → qué hay aquí).
Déjalo VACÍO para el modo automático (zona horaria del sistema).' \
'Your city as "latitude longitude", e.g.:  39.47 -0.38
(Valencia: 39.47 -0.38 · Madrid: 40.42 -3.70 · Barcelona: 41.39 2.17)
Find them on any map (right click → what is here).
Leave EMPTY for automatic mode (system time zone).')" "" 2>/dev/null)" || return 0
  v="$(printf '%s' "$v" | sed 's/^[[:space:]]*//; s/[[:space:]]*$//')"
  if [ -z "$v" ]; then ajusta_json ciudad null; kd --passivepopup "$(t 'Ciudad: automática.' 'City: automatic.')" 4; return 0; fi
  r="$(python3 - "$v" <<'PY'
import re, sys
s = sys.argv[1].strip()
if ";" in s: p = s.split(";")
elif re.search(r"\s", s): p = s.split()
elif s.count(",") == 1: p = s.split(",")
else: sys.exit(1)
try:
    la, lo = (float(x.replace(",", ".").strip()) for x in p[:2]) if len(p) == 2 else (None, None)
except Exception:
    sys.exit(1)
if la is None or not (-90 <= la <= 90 and -180 <= lo <= 180): sys.exit(1)
print('{"lat": %s, "lon": %s}' % (la, lo))
PY
)" || { kd --sorry "$(t 'No he entendido las coordenadas. Usa dos números separados por un espacio, por ejemplo: 39.47 -0.38' 'I could not read the coordinates. Use two numbers separated by a space, e.g.: 39.47 -0.38')"; return 0; }
  ajusta_json ciudad "$r"
  kd --passivepopup "$(t 'Ciudad guardada.' 'City saved.') $r" 4
}

# ------------------------------------------------------------------ modo calma
modo_calma() {
  local ahora txt
  ahora="$(lee_json calma)"
  if [ "$ahora" = "true" ]; then txt="$(t 'Ahora está ACTIVADO.' 'It is currently ON.')"; else txt="$(t 'Ahora está desactivado.' 'It is currently off.')"; fi
  kd --yes-label "$(t 'Activar' 'Turn on')" --no-label "$(t 'Desactivar' 'Turn off')" --cancel-label "$(t 'Cancelar' 'Cancel')" \
     --yesnocancel "$(t "Modo calma: menos movimiento (el zepelín flota menos, el texto va más lento, sin parpadeos).
$txt" "Calm mode: less motion (the blimp floats less, slower text, no blinking).
$txt")"
  case $? in 0) ajusta_json calma true;; 1) ajusta_json calma false;; *) return 0;; esac
  kd --passivepopup "$(t 'Guardado. Se nota en menos de un minuto.' 'Saved. Takes effect within a minute.')" 4
}

# edita un fichero de texto en una ventana propia de KDE (no depende del editor por defecto ni de que su ventana salga delante)
editar_texto() { # editar_texto FICHERO "AYUDA"
  local f="$1" nuevo
  nuevo="$(kd --textinputbox "$2" "$(cat "$f" 2>/dev/null)" 760 520 2>/dev/null)" || return 0   # Cancelar = no cambia nada
  printf '%s\n' "$nuevo" > "$f"
  kd --passivepopup "$(t 'Guardado.' 'Saved.')" 3
}

# ------------------------------------------------------------------ menu
while :; do
  op="$(kd --menu "$(t '¿Qué quieres configurar?' 'What do you want to configure?')" \
    repo     "$(t 'Git: añadir un repositorio (eliges la carpeta)' 'Git: add a repository (pick the folder)')" \
    quitar   "$(t 'Git: quitar repositorios' 'Git: remove repositories')" \
    auto     "$(t 'Git: volver a la búsqueda automática' 'Git: back to automatic search')" \
    agenda   "$(t 'Agenda: editar los avisos del día' 'Agenda: edit the daily reminders')" \
    consejos "$(t 'Consejos del zepelín: editar las frases' 'Blimp tips: edit the phrases')" \
    ciudad   "$(t 'Mi ciudad (afina amanecer y atardecer)' 'My city (fine-tunes sunrise and sunset)')" \
    calma    "$(t 'Modo calma: sí / no' 'Calm mode: on / off')" \
    guia     "$(t 'Abrir la guía completa' 'Open the full guide')" 2>/dev/null)" || break
  case "$op" in
    repo) anadir_repo;;
    quitar) quitar_repo;;
    auto) repos_automatico;;
    agenda) editar_texto "$CFG/agenda.txt" "$(t 'Agenda: una línea por aviso, «HH:MM texto» (24 h). Las líneas que empiezan por # se ignoran. Pulsa Aceptar para guardar.' 'Agenda: one line per reminder, "HH:MM text" (24 h). Lines starting with # are ignored. Press OK to save.')";;
    consejos) editar_texto "$CFG/consejos.txt" "$(t 'Consejos del zepelín: una frase por línea, cortas, sin emojis (se verán en MAYÚSCULAS y sin acentos). Las líneas con # se ignoran. Aceptar guarda.' 'Blimp tips: one short phrase per line, no emojis (shown in CAPITALS, no accents). Lines starting with # are ignored. OK saves.')";;
    ciudad) poner_ciudad;;
    calma) modo_calma;;
    guia) kd --textbox "$AQUI/GUIA.md" 820 640 2>/dev/null;;
    *) break;;
  esac
done
