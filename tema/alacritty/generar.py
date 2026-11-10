#!/usr/bin/env python3
"""NeonGrid - genera neongrid.toml (Alacritty >= 0.13) a partir de tema/paleta.py y tema/colores/NeonGrid.colorscheme.
Uso: python3 generar.py  -> tema/alacritty/neongrid.toml y copia en paquete/neongrid/neongrid/ejemplos/alacritty/"""
import re
import shutil
import sys
import tomllib
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[1]
sys.path.insert(0, str(RAIZ / 'tema'))
from paleta import PAL  # noqa: E402


def hx(c):
    return '#%02x%02x%02x' % tuple(c)


# ANSI: se toman del esquema de Konsole para que ambos terminales coincidan
esq = (RAIZ / 'tema/colores/NeonGrid.colorscheme').read_text()
col = {k: tuple(int(v) for v in val.split(',')) for k, val in re.findall(r'\[(Color\d(?:Intense)?)\]\nColor=([\d,]+)', esq)}
nombres = ['black', 'red', 'green', 'yellow', 'blue', 'magenta', 'cyan', 'white']
normal = '\n'.join(f'{n:<8}= "{hx(col[f"Color{i}"])}"' for i, n in enumerate(nombres))
bright = '\n'.join(f'{n:<8}= "{hx(col[f"Color{i}Intense"])}"' for i, n in enumerate(nombres))

TOML = f'''# NeonGrid - tema de Alacritty (0.13 o superior, formato TOML)
# Uso: copia este fichero a ~/.config/alacritty/neongrid.toml y en alacritty.toml pon:
#   [general]
#   import = ["~/.config/alacritty/neongrid.toml"]
# (Alacritty 0.14 o superior; en 0.13 `import = [...]` va suelto al principio del fichero, sin [general]).
# Generado por tema/alacritty/generar.py a partir de tema/paleta.py: no lo edites a mano.

[window]
# Opacidad 0.85, igual que Konsole en NeonGrid. Para que sea translucido de verdad hace falta
# compositor (KWin lo es por defecto en Plasma).
opacity = 0.85
# Desenfoque del fondo: en KDE Plasma (Wayland y X11) `blur = true` pide a KWin que desenfoque
# lo que hay detras. Si KWin no lo aplica, activa el efecto "Blur" en Ajustes > Efectos de escritorio.
blur = true
padding = {{ x = 10, y = 8 }}
dynamic_padding = true

[font]
# Departure Mono se instala con NeonGrid (share/fonts/neongrid). Si falta, Alacritty usa la monoespaciada del sistema.
normal = {{ family = "Departure Mono", style = "Regular" }}
size = 11.0

[cursor]
style = {{ shape = "Block", blinking = "Off" }}   # sin parpadeo (regla NeonGrid: nada > 3 Hz y modo calma)

[colors.primary]
background = "{hx(PAL['fondo'])}"
foreground = "{hx(PAL['texto'])}"
dim_foreground = "{hx(PAL['tenue'])}"

[colors.cursor]
text   = "{hx(PAL['fondo'])}"
cursor = "{hx(PAL['cian'])}"

[colors.vi_mode_cursor]
text   = "{hx(PAL['fondo'])}"
cursor = "{hx(PAL['magenta'])}"

[colors.selection]
text       = "{hx(PAL['texto'])}"
background = "{hx(PAL['sel'])}"

[colors.search.matches]
foreground = "{hx(PAL['fondo'])}"
background = "{hx(PAL['ambar'])}"

[colors.search.focused_match]
foreground = "{hx(PAL['fondo'])}"
background = "{hx(PAL['magenta'])}"

[colors.footer_bar]
foreground = "{hx(PAL['texto'])}"
background = "{hx(PAL['panel'])}"

[colors.hints.start]
foreground = "{hx(PAL['fondo'])}"
background = "{hx(PAL['cian'])}"

[colors.hints.end]
foreground = "{hx(PAL['fondo'])}"
background = "{hx(PAL['magenta'])}"

[colors.normal]
{normal}

[colors.bright]
{bright}

# ---------------------------------------------------------------------------
# Prompt con lambda en verde acido ({hx(PAL['verde'])}). Alacritty no define el prompt: lo hace tu shell.
#   bash  (~/.bashrc):  PS1='\\[\\e[38;2;57;255;136m\\]λ\\[\\e[0m\\] \\[\\e[38;2;0;229;255m\\]\\w\\[\\e[0m\\] '
#   zsh   (~/.zshrc):   PROMPT='%F{{#39ff88}}λ%f %F{{#00e5ff}}%~%f '
#   fish  (config.fish): function fish_prompt; set_color 39ff88; echo -n "λ "; set_color 00e5ff; echo -n (prompt_pwd); set_color normal; echo -n " "; end
'''

if __name__ == '__main__':
    (AQUI / 'neongrid.toml').write_text(TOML)
    tomllib.loads(TOML)          # valida
    dest = RAIZ / 'paquete/neongrid/neongrid/ejemplos/alacritty'
    dest.mkdir(parents=True, exist_ok=True)
    shutil.copy(AQUI / 'neongrid.toml', dest / 'neongrid.toml')
    print('TOML valido; escrito en', AQUI / 'neongrid.toml', 'y', dest / 'neongrid.toml')
