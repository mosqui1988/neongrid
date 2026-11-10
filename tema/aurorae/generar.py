#!/usr/bin/env python3
"""Genera la decoracion de ventanas Aurorae `NeonGrid` (solo stdlib).
Salida: ../../paquete/neongrid/share/aurorae/themes/NeonGrid/  (SVG de pixeles + NeonGridrc + metadata)
Uso: python3 generar.py [carpeta_salida]"""
import os, sys, json
from pixelsvg import *   # noqa

RAIZ = os.path.abspath(os.path.join(AQUI, '..', '..'))
SALIDA = sys.argv[1] if len(sys.argv) > 1 else os.path.join(RAIZ, 'paquete', 'neongrid', 'share', 'aurorae', 'themes', 'NeonGrid')

TOP = 28          # alto del titulo (2 borde + 24 + 2)
BORDE = 4         # 2 px de neon + 2 px de halo escalonado hacia dentro
BISEL = 4         # chaflan a 45 grados (debe ser <= BORDE: las esquinas miden BORDE x TITULO)
NEGRO = (0, 0, 0)


def estilo(activo):
    if activo:
        linea = P['cian']
        return dict(linea=linea, brillo=mix(linea, (255, 255, 255), .55), titulo=mix(P['panel'], P['cian'], .10),
                    cuerpo=P['fondo'], halo=(.35, .15), divisor=mix(linea, P['fondo'], .5))
    linea = mix(P['violeta'], P['fondo'], .45)
    return dict(linea=linea, brillo=mix(linea, (255, 255, 255), .10), titulo=mix(P['panel'], P['violeta'], .06),
                cuerpo=P['panel'], halo=(0, 0), divisor=mix(linea, P['fondo'], .5))


def celda(s):
    def fn(x, y, W, H):
        r = anillo(x, y, W, H, BISEL)
        if r is None:
            return None
        titulo = y < TOP
        base = s['titulo'] if titulo else s['cuerpo']
        alfa = .96 if titulo else .94
        if titulo and 4 <= y < TOP - 1 and y % 4 == 3:          # lineas de escaneo ~9 % de negro, solo en el titulo
            base = mix(base, NEGRO, .09)
        if r < 2:
            lado = min(x, W - 1 - x) < 2 and y < 14             # corchete: tramo vertical brillante junto a la esquina
            esq = (min(x, W - 1 - x) + min(y, H - 1 - y)) < BISEL + 2 and min(x, W - 1 - x) < BORDE and min(y, H - 1 - y) < BORDE
            return hx(s['brillo'] if (lado or esq) else s['linea']), 1.0
        if r < 4 and s['halo'][r - 2]:
            return hx(mix(base, s['linea'], s['halo'][r - 2])), alfa
        if titulo and y == TOP - 1:
            return hx(s['divisor']), 1.0
        return hx(base), alfa
    return fn


def decoracion():
    grupos = []
    for pre, activo in (('decoration-', True), ('decoration-inactive-', False)):
        trozos = marco9((BORDE, TOP, BORDE, BORDE), (4, 4), celda(estilo(activo)))
        grupos += con_prefijo(pre, trozos)
    return apilar(grupos, 12)


# ---- botones: rejilla logica de 10x10 (u = 2 px) => 20x20 px
GLIFOS = {
    'close':       ['..........', '..........', '..X....X..', '...X..X...', '....XX....', '....XX....', '...X..X...', '..X....X..', '..........', '..........'],
    'maximize':    ['..........', '..........', '..XXXXXX..', '..X....X..', '..X....X..', '..X....X..', '..X....X..', '..XXXXXX..', '..........', '..........'],
    'restore':     ['..........', '....XXXXX.', '....X...X.', '..XXXXX.X.', '..X...XXX.', '..X...X...', '..X...X...', '..XXXXX...', '..........', '..........'],
    'minimize':    ['..........', '..........', '..........', '..........', '..........', '..........', '..........', '..XXXXXX..', '..XXXXXX..', '..........'],
    'keepabove':   ['..........', '..........', '....XX....', '...XXXX...', '..XXXXXX..', '.XXXXXXXX.', '..........', '..XXXXXX..', '..........', '..........'],
    'keepbelow':   ['..........', '..XXXXXX..', '..........', '.XXXXXXXX.', '..XXXXXX..', '...XXXX...', '....XX....', '..........', '..........', '..........'],
    'alldesktops': ['..........', '....XX....', '...X..X...', '..X....X..', '..X....X..', '...X..X...', '....XX....', '..........', '..........', '..........'],
    'shade':       ['..........', '..XXXXXX..', '..XXXXXX..', '..........', '....XX....', '...XXXX...', '....XX....', '..........', '..........', '..........'],
    'help':        ['..........', '...XXXX...', '..XX..XX..', '......XX..', '.....XX...', '....XX....', '..........', '....XX....', '..........', '..........'],
}
# alldesktops: rombo con punto central (forma de los escritorios virtuales)
GLIFOS['alldesktops'] = ['..........', '....XX....', '...X..X...', '..X.XX.X..', '.X.XXXX.X.', '.X.XXXX.X.', '..X.XX.X..', '...X..X...', '....XX....', '..........']

CAJA = ['.XXXXXXXX.'] + ['XXXXXXXXXX'] * 8 + ['.XXXXXXXX.']
DEACT = mix(P['violeta'], P['fondo'], .45)


def estados_boton(nombre):
    cierre = nombre == 'close'
    acento = mix(P['magenta_t'], (255, 255, 255), .3) if cierre else P['cian']   # contraste >= 7:1
    pleno = P['magenta'] if cierre else P['cian']
    hover_f = mix(P['fondo'], P['magenta'] if cierre else P['cian'], .28)
    # (prefijo, color de caja o None, color del borde de caja, color de glifo)
    return {
        'active':         (None, None, acento),
        'hover':          (hover_f, pleno, P['texto']),
        'pressed':        (pleno, pleno, P['fondo']),
        'inactive':       (None, None, P['tenue']),
        'deactivated':    (None, None, DEACT),
        'hover-inactive': (mix(P['panel'], P['violeta'], .35), P['violeta'], P['texto']),
        'pressed-inactive': (P['violeta'], P['violeta'], P['fondo']),
    }


def boton(nombre):
    grupos = []
    for est, (caja, borde, glifo) in estados_boton(nombre).items():
        c = lienzo(10, 10)
        if caja is not None:
            for j, fila in enumerate(CAJA):
                for i, ch in enumerate(fila):
                    if ch == 'X':
                        marco_ = i in (0, 9) or j in (0, 9) or (i in (1, 8) and j in (1, 8))
                        c[j][i] = (hx(borde if marco_ else caja), 1.0)
        for j, fila in enumerate(GLIFOS[nombre]):
            for i, ch in enumerate(fila):
                if ch == 'X':
                    c[j][i] = (hx(glifo), 1.0)
        # escala x2 (cada pixel logico = 2x2 reales)
        g = lienzo(20, 20)
        for j in range(10):
            for i in range(10):
                if c[j][i]:
                    rect(g, i * 2, j * 2, 2, 2, c[j][i][0], c[j][i][1])
        grupos.append((f'{est}-center', g))
    return apilar(grupos, 20, sep=0)


RC = f'''[General]
ActiveTextColor={','.join(str(v) for v in P['texto'])}
InactiveTextColor={','.join(str(v) for v in P['tenue'])}
Animation=false
AnimationTime=0

[Layout]
BorderLeft={BORDE}
BorderRight={BORDE}
BorderBottom={BORDE}
TitleEdgeTop=2
TitleEdgeBottom=2
TitleEdgeLeft={BORDE}
TitleEdgeRight={BORDE}
TitleEdgeTopMaximized=2
TitleEdgeBottomMaximized=2
TitleEdgeLeftMaximized={BORDE}
TitleEdgeRightMaximized={BORDE}
TitleHeight=24
TitleBorderLeft=8
TitleBorderRight=8
TitleAlignment=Left
TitleVerticalAlignment=Center
ButtonWidth=20
ButtonHeight=20
ButtonSpacing=4
ButtonMarginTop=2
ButtonMarginTopMaximized=2
PaddingTop=0
PaddingBottom=0
PaddingLeft=0
PaddingRight=0
ExplicitButtonSpacer=0
'''

DESKTOP = '''[Desktop Entry]
Name=NeonGrid
Name[es]=NeonGrid
Comment=Pixel-art cyberpunk window decoration: bevelled corners, neon border, cyan when active, violet when inactive
Comment[es]=Decoracion de ventanas cyberpunk en pixel art: esquinas biseladas, borde neon, cian activa y violeta inactiva
Type=Service
X-KDE-PluginInfo-Name=NeonGrid
X-KDE-PluginInfo-Version=1.0
X-KDE-PluginInfo-License=GPL-2.0+
'''

def escribe(ruta, txt):
    os.makedirs(os.path.dirname(ruta), exist_ok=True)
    with open(ruta, 'w') as f:
        f.write(txt)


def main():
    s, pos = decoracion()
    escribe(f'{SALIDA}/decoration.svg', s)
    escribe(os.path.join(AQUI, '_layout.json'), json.dumps(pos))     # solo lo usa vista-previa.py (no se empaqueta)
    for n in GLIFOS:
        escribe(f'{SALIDA}/{n}.svg', boton(n)[0])
    escribe(f'{SALIDA}/NeonGridrc', RC)
    escribe(f'{SALIDA}/metadata.desktop', DESKTOP)
    print('aurorae ->', SALIDA)


if __name__ == '__main__':
    main()
