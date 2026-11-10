#!/usr/bin/env python3
"""Genera el tema de Plasma `NeonGrid` (desktoptheme) en SVG de pixeles. Solo stdlib.
Salida: ../../paquete/neongrid/share/plasma/desktoptheme/NeonGrid/
Uso: python3 generar.py [carpeta_salida]
Plasma 6 usa automaticamente el tema `default` para todo SVG que falte, asi que no hace falta (ni existe)
un campo `Inherits`: aqui solo se sustituye lo que define el aspecto."""
import os, sys, json, shutil
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'aurorae'))
from pixelsvg import *   # noqa

QUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.abspath(os.path.join(QUI, '..', '..'))
SALIDA = sys.argv[1] if len(sys.argv) > 1 else os.path.join(RAIZ, 'paquete', 'neongrid', 'share', 'plasma', 'desktoptheme', 'NeonGrid')
BAYER = [[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]
NEGRO = (0, 0, 0)
BLANCO = (255, 255, 255)


def escribe(ruta, txt):
    ruta = os.path.join(SALIDA, ruta)
    os.makedirs(os.path.dirname(ruta), exist_ok=True)
    with open(ruta, 'w') as f:
        f.write(txt)


def emite(ruta, grupos, ancho=None, extra_grupos=()):
    """grupos: lista de (id, lienzo)."""
    grupos = list(grupos) + list(extra_grupos)
    ancho = ancho or max(len(c[0]) for _, c in grupos)
    s, _ = apilar(grupos, ancho)
    escribe(ruta, s)


def pieza_unica(id_, w, h, col, a=1.0):
    c = lienzo(w, h)
    rect(c, 0, 0, w, h, col, a)
    return (id_, c)


def tile_hint():
    return ('hint-tile-center', [[('#ff00ff', 0.0)]])


# ---------------------------------------------------------------- marcos con borde neon y esquinas biseladas
def fn_caja(borde, relleno, alfa, bisel, halo=.30, scan=True, brillo=True):
    def fn(x, y, W, H):
        r = anillo(x, y, W, H, bisel)
        if r is None:
            return None
        if r == 0:
            dx, dy = min(x, W - 1 - x), min(y, H - 1 - y)
            esq = brillo and dx < bisel + 4 and dy < bisel + 4 and (dx + dy) < bisel + 5
            return hx(mix(borde, BLANCO, .55) if esq else borde), 1.0
        base = relleno
        if scan and y % 4 == 3:
            base = mix(base, NEGRO, .06)
        if r == 1 and halo:
            return hx(mix(base, borde, halo)), alfa
        return hx(base), alfa
    return fn


def fn_mascara(bisel):
    def fn(x, y, W, H):
        return None if anillo(x, y, W, H, bisel) is None else ('#000000', 1.0)
    return fn


def fn_sombra_dura(lado):
    """Sombra dura de 2 px desplazada abajo-derecha (solo bordes derecho/inferior)."""
    def fn(x, y, W, H):
        der, aba = x >= W - lado, y >= H - lado
        return ('#000000', .60) if (der or aba) and not (x < lado and y < lado) and not (x < lado) and not (y < lado) else None
    return fn


def marco_popup(m, bisel, alfa, borde, relleno=None, halo=.30, mascara=True, sombra=2):
    relleno = relleno or P['fondo']
    t = []
    t += con_prefijo('', marco9((m,) * 4, (4, 4), fn_caja(borde, relleno, alfa, bisel, halo)))
    t.append(tile_hint())
    t += pistas('', (m + 2,) * 4, 0)
    if mascara:
        t += con_prefijo('mask-', marco9((m,) * 4, (4, 4), fn_mascara(bisel)))
    if sombra:
        t += con_prefijo('shadow-', marco9((sombra,) * 4, (4, 4), fn_sombra_dura(sombra)))
        t += pistas('shadow-', (sombra,) * 4, 0)
    return t


# alfa por variante: la base (default) es translucida, `opaque`/`solid` sin alfa, `translucent` mas clara
VARIANTES = {'': .93, 'opaque': 1.0, 'solid': 1.0, 'translucent': .74}


def popups():
    for var, a in VARIANTES.items():
        pre = (var + '/') if var else ''
        emite(pre + 'dialogs/background.svg', marco_popup(6, 4, a, P['cian']))
        emite(pre + 'widgets/tooltip.svg', marco_popup(5, 3, a if var else .96, P['cian'], P['panel']))
        if var in ('', 'solid', 'translucent'):
            emite(pre + 'widgets/background.svg', marco_popup(6, 4, a, P['cian']))
    emite('widgets/translucentbackground.svg', marco_popup(6, 4, .74, P['cian']))


# ---------------------------------------------------------------- barra superior
def fn_panel(alfa, borde=P['cian']):
    sup, inf = P['panel'], P['fondo']
    def fn(x, y, W, H):
        # lado del borde: 2 px en cada extremo; el inferior (el unico visible en una barra superior) es el cian
        dx, dy = min(x, W - 1 - x), min(y, H - 1 - y)
        if H - 1 - y == 0:
            return hx(borde), 1.0
        if H - 1 - y == 1:
            return hx(mix(inf, borde, .35)), alfa
        if y == 0:
            return hx(mix(sup, borde, .20)), alfa
        if x == 0 or x == W - 1:
            return hx(mix(inf, borde, .35)), alfa
        t = (y - 1) / max(1, H - 4)
        c = mix(sup, inf, min(1, max(0, t)))
        if BAYER[y % 4][x % 4] / 16 < ((t * 3) % 1):      # degradado con tramado ordenado (sin suavizar)
            c = mix(sup, inf, min(1, (int(t * 3) + 1) / 3))
        else:
            c = mix(sup, inf, int(t * 3) / 3)
        if y % 4 == 3:
            c = mix(c, NEGRO, .10)                         # lineas de escaneo
        return hx(c), alfa
    return fn


def panel():
    for var, a in {'': .94, 'opaque': 1.0, 'solid': 1.0, 'translucent': .72}.items():
        pre = (var + '/') if var else ''
        t = con_prefijo('', marco9((2, 2, 2, 2), (4, 30), fn_panel(a)))
        t += con_prefijo('floating-', marco9((2, 2, 2, 2), (4, 30), fn_panel(a)))
        t += [tile_hint()]
        # sombra dura bajo la barra
        t += con_prefijo('shadow-', marco9((0, 0, 0, 2), (4, 4), lambda x, y, W, H: ('#000000', .5) if y >= H - 2 else None))
        emite(pre + 'widgets/panel-background.svg', t)


# ---------------------------------------------------------------- tareas (administrador de tareas, solo iconos)
def fn_tarea(estado, lado):
    cian, mag = P['cian'], P['magenta']
    def fn(x, y, W, H):
        r_ul = {'bottom': H - 1 - y, 'right': W - 1 - x, 'left': x}[lado]
        a_lo = {'bottom': x, 'right': y, 'left': y}[lado]          # posicion a lo largo del subrayado
        a_len = {'bottom': W, 'right': H, 'left': H}[lado]
        ul = r_ul < 2
        if estado == 'normal':
            return None
        if estado == 'hover':
            if ul:
                return hx(mix(P['fondo'], cian, .55)), 1.0
            return hx(P['texto']), .08
        if estado == 'focus':
            if ul:
                return hx(cian), 1.0
            return hx(cian), .16
        if estado == 'attention':
            if ul:
                return (hx(mag), 1.0) if (a_lo // 2) % 2 == 0 else None         # subrayado discontinuo
            return hx(mag), .20
        if estado == 'minimized':
            if r_ul == 1:
                return (hx(P['violeta_claro']), 1.0) if a_lo % 4 == 0 else None  # punteado hueco
            return None
        if estado == 'progress':
            if ul:
                return hx(cian), 1.0
            return hx(cian), .30
    return fn


def tareas():
    t = []
    for pre, lado, m in (('', 'bottom', (2, 2, 2, 4)), ('north-', 'bottom', (2, 2, 2, 4)),
                         ('west-', 'right', (2, 2, 4, 2)), ('east-', 'left', (4, 2, 2, 2))):
        for est in ('normal', 'hover', 'focus', 'attention', 'minimized', 'progress'):
            t += con_prefijo(f'{pre}{est}-', marco9(m, (4, 4), fn_tarea(est, lado)))
            t += pistas(f'{pre}{est}-', m, 0)
    emite('widgets/tasks.svg', t)


# ---------------------------------------------------------------- escritorios virtuales como rombos
def rombo(n, relleno=None, borde=None, grosor=2, a_rel=1.0):
    """SVG de rombo n x n (poligono; el lienzo se estira al tamano de la celda)."""
    h = n / 2
    pts = lambda r: ' '.join(f'{h + dx * r:g},{h + dy * r:g}' for dx, dy in ((0, -1), (1, 0), (0, 1), (-1, 0)))
    out = []
    if borde:
        out.append(f'<path fill="{borde}" fill-rule="evenodd" d="M{h},0 L{n},{h} L{h},{n} L0,{h} Z '
                   f'M{h},{grosor * 1.6:g} L{n - grosor * 1.6:g},{h} L{h},{n - grosor * 1.6:g} L{grosor * 1.6:g},{h} Z"/>')
    if relleno:
        k = grosor * 1.6 if borde else 0
        out.append(f'<polygon fill="{relleno}" fill-opacity="{a_rel}" points="{h},{k:g} {n - k:g},{h} {h},{n - k:g} {k:g},{h}"/>')
    return out


def pager():
    n = 24
    cuerpo = []
    est = {'normal': dict(borde=hx(mix(P['violeta'], P['violeta_claro'], .35))),
           'hover': dict(borde=hx(P['cian']), relleno=hx(P['cian']), a_rel=.25),
           'active': dict(relleno=hx(P['cian']), borde=hx(P['cian']))}
    for nombre, kw in est.items():
        # frame sin bordes: solo `-center`, que se estira a toda la celda
        cuerpo.append(f'<g id="{nombre}-center">\n<rect width="{n}" height="{n}" fill="#000" fill-opacity="0"/>\n'
                      + '\n'.join(rombo(n, **kw)) + '\n</g>')
    cuerpo.append('<g id="hint-tile-center"><rect width="1" height="1" fill="#f0f" fill-opacity="0"/></g>')
    escribe('widgets/pager.svg', svg(n, n, '\n'.join(cuerpo)).replace(' shape-rendering="crispEdges"', ''))


# ---------------------------------------------------------------- botones, campos de texto, barras...
def fn_borde_simple(borde, relleno, alfa, bisel, halo=0.0, fill_a=None):
    return fn_caja(borde, relleno, alfa, bisel, halo, scan=False, brillo=False)


def widgets_basicos():
    f, p, v = P['fondo'], P['panel'], P['violeta']
    vd = mix(P['violeta'], P['fondo'], .45)
    # --- boton
    t = []
    m = (4, 4, 4, 4)
    for nom, borde, rel, halo in (('normal', vd, P['boton'], 0), ('hover', P['cian'], P['boton'], .30), ('focus', P['cian'], P['boton'], .0),
                                  ('pressed', P['cian'], P['sel'], 0)):
        t += con_prefijo(f'{nom}-', marco9(m, (4, 4), fn_borde_simple(borde, rel, 1.0, 2, halo)))
        t += pistas(f'{nom}-', m, 0)
    for nom, borde, rel in (('toolbutton-hover', P['cian'], mix(P['fondo'], P['cian'], .18)), ('toolbutton-focus', P['cian'], P['fondo']),
                            ('toolbutton-pressed', P['cian'], P['sel'])):
        a = 0.0 if nom.endswith('focus') else 1.0
        t += con_prefijo(f'{nom}-', marco9(m, (4, 4), fn_borde_simple(borde, rel, 0.55 if not nom.endswith('focus') else 0.0, 2)))
        t += pistas(f'{nom}-', m, 0)
    t += con_prefijo('mask-normal-', marco9(m, (4, 4), fn_mascara(2)))
    emite('widgets/button.svg', t)
    # --- campo de texto
    t = []
    for nom, borde, halo in (('base', vd, 0), ('hover', P['violeta_claro'], 0), ('focus', P['cian'], .30)):
        t += con_prefijo(f'{nom}-', marco9(m, (4, 4), fn_borde_simple(borde, P['fondo'], 1.0, 2, halo)))
        t += pistas(f'{nom}-', m, 0)
    t += con_prefijo('focusframe-', marco9((3, 3, 3, 3), (4, 4), lambda x, y, W, H: (hx(P['cian']), .5) if anillo(x, y, W, H, 0) == 0 else None))
    t += pistas('focusframe-', (3, 3, 3, 3), 0) + [tile_hint(), ('hint-focus-over-base', [[('#f0f', 0.0)]])]
    emite('widgets/lineedit.svg', t)
    # --- pestanas
    t = []
    for orient, lado in (('north', 'top'), ('south', 'bottom'), ('west', 'left'), ('east', 'right')):
        def fn(x, y, W, H, lado=lado):
            d = {'top': y, 'bottom': H - 1 - y, 'left': x, 'right': W - 1 - x}[lado]
            if anillo(x, y, W, H, 3) is None:
                return None
            if d < 2:
                return hx(P['cian']), 1.0
            return hx(P['alterno']), .96
        t += con_prefijo(f'{orient}-active-tab-', marco9((4, 4, 4, 4), (4, 4), fn))
        t += pistas(f'{orient}-active-tab-', (4, 4, 4, 4), 0)
    emite('widgets/tabbar.svg', t + [tile_hint()])
    # --- deslizador: ranura 6 px y asa en rombo
    t = []
    t += con_prefijo('groove-', marco9((2, 2, 2, 2), (4, 2), fn_borde_simple(vd, P['fondo'], 1.0, 0)))
    t += con_prefijo('groove-highlight-', marco9((2, 2, 2, 2), (4, 2), fn_borde_simple(P['cian'], mix(P['fondo'], P['cian'], .55), 1.0, 0)))
    t += [tile_hint(), ('hint-handle-size', [[('#f0f', 0.0)] * 16 for _ in range(16)])]
    for o in ('horizontal', 'vertical'):
        for st, col in (('handle', P['cian']), ('hover', P['texto']), ('focus', P['magenta_t'])):
            t.append((f'{o}-slider-{st}', rombo_lienzo(16, col)))
    emite('widgets/slider.svg', t)
    # --- barra de progreso / medidor
    t = []
    t += con_prefijo('bar-inactive-', marco9((2, 2, 2, 2), (4, 4), fn_borde_simple(vd, P['fondo'], 1.0, 0)))
    t += con_prefijo('bar-active-', marco9((2, 2, 2, 2), (4, 4), fn_borde_simple(P['cian'], mix(P['fondo'], P['cian'], .6), 1.0, 0)))
    t += [tile_hint(), ('hint-bar-size', [[('#f0f', 0.0)] * 4 for _ in range(8)])]
    emite('widgets/bar_meter_horizontal.svg', t)
    # --- barra de desplazamiento
    t = []
    for o in ('vertical', 'horizontal'):
        t += con_prefijo(f'background-{o}-', marco9((2, 2, 2, 2), (4, 4), fn_borde_simple(mix(P['violeta'], P['fondo'], .7), P['alterno'], .9, 0)))
        t += pistas(f'background-{o}-', (2, 2, 2, 2), 0)
    t += con_prefijo('slider-', marco9((2, 2, 2, 2), (4, 4), fn_borde_simple(P['violeta'], mix(P['panel'], P['violeta'], .45), 1.0, 0)))
    t += con_prefijo('mouseover-slider-', marco9((2, 2, 2, 2), (4, 4), fn_borde_simple(P['cian'], mix(P['panel'], P['cian'], .35), 1.0, 0)))
    t += [tile_hint(), ('hint-scrollbar-size', [[('#f0f', 0.0)] * 10 for _ in range(10)])]
    emite('widgets/scrollbar.svg', t)
    # --- listas (seleccion cian)
    t = []
    for nom, borde, rel, a in (('normal', None, P['fondo'], 0.0), ('hover', P['cian'], P['cian'], .12), ('selected', P['cian'], P['sel'], 1.0),
                               ('selected+hover', P['cian'], mix(P['sel'], P['cian'], .20), 1.0)):
        if borde is None:
            t += con_prefijo(f'{nom}-', marco9((3, 3, 3, 3), (4, 4), lambda x, y, W, H: None))
        else:
            t += con_prefijo(f'{nom}-', marco9((3, 3, 3, 3), (4, 4), fn_borde_simple(borde, rel, a, 2) if a > .5 else
                                               (lambda x, y, W, H, b=borde, r=rel, a=a: (hx(r), a) if anillo(x, y, W, H, 2) is not None else None)))
        t += pistas(f'{nom}-', (3, 3, 3, 3), 0)
    emite('widgets/viewitem.svg', t + [tile_hint()])
    # --- cabecera de plasmoide
    t = []
    for nom, lado in (('header', 'b'), ('footer', 't')):
        def fn(x, y, W, H, lado=lado):
            if (lado == 'b' and y == H - 1) or (lado == 't' and y == 0):
                return hx(mix(P['fondo'], P['cian'], .45)), 1.0
            return hx(P['alterno']), .70
        t += con_prefijo(f'{nom}-', marco9((2, 2, 2, 2), (4, 4), fn))
        t += pistas(f'{nom}-', (2, 2, 2, 2), 0)
    t.append(('hint-stretch-borders', [[('#f0f', 0.0)]]))
    emite('widgets/plasmoidheading.svg', t)
    # --- lineas separadoras
    t = [pieza_unica('horizontal-line', 4, 1, mix(P['violeta'], P['fondo'], .35)), pieza_unica('vertical-line', 1, 4, mix(P['violeta'], P['fondo'], .35))]
    emite('widgets/line.svg', t)


def rombo_lienzo(n, col):
    """Rombo escalonado n x n (con borde oscuro de 1 px) como lienzo de pixeles."""
    c = lienzo(n, n)
    h = (n - 1) / 2
    for y in range(n):
        for x in range(n):
            d = abs(x - h) + abs(y - h)
            if d <= h + .6:
                c[y][x] = (hx(P['fondo'] if d > h - 1.4 else col), 1.0)
    return c


# ---------------------------------------------------------------- iconos del panel: nucleo hexagonal y bateria
def nucleo(N=16, u=2):
    """Hexagono 'nucleo' con >_ . N = lado de la rejilla logica, u = pixeles reales por celda."""
    c = lienzo(N * u, N * u)
    h = (N - 1) / 2
    R = N / 2 - .1
    dentro = lambda x, y: 0 <= x < N and 0 <= y < N and abs(y - h) <= R * .866 and abs(x - h) + abs(y - h) / 1.732 <= R
    def pix(x, y, col):
        rect(c, x * u, y * u, u, u, col)
    for y in range(N):
        for x in range(N):
            if dentro(x, y):
                borde = not all(dentro(x + dx, y + dy) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
                pix(x, y, hx(P['cian']) if borde else hx(P['fondo']))
    if N == 16:
        for (x, y) in ((4, 5), (5, 6), (6, 7), (5, 8), (4, 9)):                    # >
            pix(x, y, hx(mix(P['cian'], BLANCO, .55)))
        for x in range(8, 12):                                                      # _
            pix(x, 9, hx(P['magenta']))
    else:
        for (x, y) in ((6, 7), (7, 8), (8, 9), (9, 10), (8, 11), (7, 12), (6, 13)):
            pix(x, y, hx(mix(P['cian'], BLANCO, .55)))
        for x in range(11, 16):
            pix(x, 13, hx(P['magenta']))
    return c


def bateria():
    """Bateria de 6 rallitas. Elementos con los ids del tema por defecto (22-22-*, y los generales)."""
    N = 22
    def cuerpo_vacio():
        c = lienzo(N, N)
        for (x, y, w, h) in ((2, 6, 17, 1), (2, 15, 17, 1), (2, 6, 1, 10), (18, 6, 1, 10)):    # contorno (hueco)
            rect(c, x, y, w, h, P['tenue'])
        rect(c, 19, 9, 2, 4, P['tenue'])                  # polo
        return c
    def barras(k, col):
        c = lienzo(N, N)
        for i in range(k):
            rect(c, 4 + i * 2 + i, 8, 2, 6, col)          # 6 rallitas de 2 px, paso 3 (4..19)
        return c
    def color(p):
        return P['rojo'] if p <= 20 else (P['ambar'] if p <= 40 else P['cian'])
    grupos = []
    for pre in ('22-22-', ''):
        grupos.append((pre + 'Battery', cuerpo_vacio()))
        for p in range(0, 101, 10):
            k = 0 if p == 0 else max(1, round(p * 6 / 100))
            grupos.append((f'{pre}Fill{p}', barras(k, color(p))))
        # alimentador de red: rayo
        rayo = lienzo(N, N)
        mascara(rayo, ['...XX', '..XX.', '.XXXX', '..XX.', '.XX..', 'XX...'], 7, 8, P['verde'], 1.0, 1)
        grupos.append((pre + 'AcAdapter', rayo))
        nd = lienzo(N, N)
        mascara(nd, ['X.X', '.X.', 'X.X'], 9, 9, P['tenue'], 1.0, 1)
        grupos.append((pre + 'Unavailable', nd))
        grupos.append((pre + 'battery-ups', cuerpo_vacio()))
    emite('icons/battery.svg', grupos)


# ---------------------------------------------------------------- metadatos y colores
META = {'KPackageStructure': 'Plasma/Theme',
        'KPlugin': {'Id': 'NeonGrid', 'Name': 'NeonGrid', 'Name[es]': 'NeonGrid',
                    'Description': 'Pixel-art cyberpunk Plasma theme: neon top bar, bevelled popups, cyan and magenta accents',
                    'Description[es]': 'Tema de Plasma cyberpunk en pixel art: barra superior de neon, ventanas emergentes biseladas, acentos cian y magenta',
                    'Authors': [{'Name': 'NeonGrid'}], 'Category': 'Plasma Theme', 'License': 'GPL-2.0+', 'Version': '1.0'},
        'X-Plasma-API': '5.0'}


def main():
    if os.path.isdir(SALIDA):
        shutil.rmtree(SALIDA)
    os.makedirs(SALIDA)
    popups(); panel(); tareas(); pager(); widgets_basicos(); bateria()
    emite('icons/nucleo.svg', [('nucleo', nucleo())])
    emite('icons/nucleo-22.svg', [('nucleo', nucleo(22, 1))])
    escribe('metadata.json', json.dumps(META, indent=2, ensure_ascii=False) + '\n')
    shutil.copy(os.path.join(RAIZ, 'tema', 'colores', 'NeonGrid.colors'), os.path.join(SALIDA, 'colors'))
    print('plasma ->', SALIDA)


if __name__ == '__main__':
    main()
