#!/usr/bin/env python3
"""Genera colores/NeonGrid.colors (KDE), colores/NeonGrid.colorscheme y NeonGrid.profile (Konsole)
a partir de paleta.py. No instala nada: solo escribe en esta carpeta."""
import os, sys
from paleta import PAL, contraste
HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.join(HERE, 'colores'); os.makedirs(OUT, exist_ok=True)
rgb = lambda k: ','.join(map(str, PAL[k]))
OPACIDAD = float(sys.argv[1]) if len(sys.argv) > 1 else 0.85


def grupo(bg, alt, extra=None):
    d = dict(BackgroundAlternate=alt, BackgroundNormal=bg, DecorationFocus=rgb('cian'), DecorationHover=rgb('magenta'),
             ForegroundActive=rgb('magenta_t'), ForegroundInactive=rgb('tenue'), ForegroundLink=rgb('cian'),
             ForegroundNegative=rgb('rojo_t'), ForegroundNeutral=rgb('ambar'), ForegroundNormal=rgb('texto'),
             ForegroundPositive=rgb('verde'), ForegroundVisited=rgb('violeta_claro'))
    d.update(extra or {}); return d


S = {
    'Colors:View': grupo(rgb('fondo'), rgb('alterno')),
    'Colors:Window': grupo(rgb('panel'), rgb('alterno')),
    'Colors:Button': grupo(rgb('boton'), rgb('panel')),
    'Colors:Complementary': grupo(rgb('fondo'), rgb('alterno')),
    'Colors:Header': grupo(rgb('panel'), rgb('alterno')),
    'Colors:Tooltip': grupo(rgb('fondo'), rgb('alterno')),
    'Colors:Selection': grupo(rgb('sel'), rgb('sel'), dict(ForegroundNormal=rgb('texto'), ForegroundInactive=rgb('texto'), ForegroundActive=rgb('texto'),
                                                              ForegroundLink=rgb('texto'), ForegroundVisited=rgb('texto'), DecorationFocus=rgb('cian'), DecorationHover=rgb('cian'))),
}
txt = ["[ColorEffects:Disabled]\nColor=40,44,64\nColorAmount=0\nColorEffect=0\nContrastAmount=0.65\nContrastEffect=1\nIntensityAmount=0.1\nIntensityEffect=2\n",
       "[ColorEffects:Inactive]\nChangeSelectionColor=true\nColor=60,64,96\nColorAmount=0.025\nColorEffect=2\nContrastAmount=0.1\nContrastEffect=2\nEnable=false\nIntensityAmount=0\nIntensityEffect=0\n"]
for g, kv in S.items(): txt.append(f"[{g}]\n" + ''.join(f"{k}={v}\n" for k, v in sorted(kv.items())))
txt.append("[General]\nColorScheme=NeonGrid\nName=NeonGrid\nshadeSortColumn=true\n")
txt.append(f"[KDE]\ncontrast=4\n")
txt.append(f"[WM]\nactiveBackground={rgb('fondo')}\nactiveBlend={rgb('cian')}\nactiveForeground={rgb('texto')}\n"
           f"inactiveBackground={rgb('panel')}\ninactiveBlend={rgb('violeta')}\ninactiveForeground={rgb('tenue')}\n")
open(f'{OUT}/NeonGrid.colors', 'w').write('\n'.join(txt))

# ---- Konsole: ANSI con contraste >= 7:1 sobre el fondo (el negro es solo fondo de programas)
ansi = [('panel', 'boton'), ('rojo_t', 'rojo_t'), ('verde', 'verde'), ('ambar', 'ambar'),
        ('cian', 'cian'), ('magenta_t', 'magenta_t'), ('cian', 'texto'), ('texto', 'texto')]
normal = [(24, 30, 56), PAL['rojo_t'], (46, 222, 120), (232, 160, 24), (120, 160, 255), PAL['magenta_t'], (30, 205, 230), (200, 214, 236)]
intenso = [(70, 82, 126), (255, 160, 176), PAL['verde'], (255, 205, 100), (170, 196, 255), (255, 170, 242), PAL['cian'], PAL['texto']]
k = ["[General]\nDescription=NeonGrid\nOpacity=%.2f\nWallpaper=\n" % OPACIDAD,
     f"[Background]\nColor={rgb('fondo')}\n[BackgroundIntense]\nColor={rgb('panel')}\n[BackgroundFaint]\nColor={rgb('fondo')}\n",
     f"[Foreground]\nColor={rgb('texto')}\n[ForegroundIntense]\nColor=255,255,255\n[ForegroundFaint]\nColor={rgb('tenue')}\n"]
for i in range(8):
    k.append(f"[Color{i}]\nColor={','.join(map(str, normal[i]))}\n[Color{i}Intense]\nColor={','.join(map(str, intenso[i]))}\n"
             f"[Color{i}Faint]\nColor={','.join(map(str, normal[i]))}\n")
open(f'{OUT}/NeonGrid.colorscheme', 'w').write('\n'.join(k))
open(f'{OUT}/NeonGrid.profile', 'w').write(
    "[Appearance]\nColorScheme=NeonGrid\nFont=Departure Mono,11,-1,5,400,0,0,0,0,0,0,0,0,0,0,1\nCursorShape=0\n\n"
    "[General]\nName=NeonGrid\nParent=FALLBACK/\n\n[Scrolling]\nHistorySize=10000\n")
bad = [(i, contraste(normal[i], PAL['fondo'])) for i in range(1, 8)] + [(f'{i}i', contraste(intenso[i], PAL['fondo'])) for i in range(1, 8)]
print('Konsole: contraste ANSI sobre fondo ->', ' '.join(f'{n}:{c:.1f}' for n, c in bad))
print('opacidad', OPACIDAD, '-> colores/')
