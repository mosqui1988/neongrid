#!/usr/bin/env python3
"""NeonGrid - generador del cursor `NeonGrid-cursors` (formato Xcursor, tamanos 24/32/48).

Herramienta de CONSTRUCCION (usa Pillow solo para rasterizar mascaras; el escritor Xcursor es Python puro).
Uso:  python3 generar.py     -> paquete/neongrid/share/icons/NeonGrid-cursors/{index.theme,cursors/}
Luego:  python3 verificar.py -> lee los ficheros, valida cabecera/tabla y escribe vista-previa.png

Estilo: cuerpo oscuro, borde cian, punta magenta y 1 px de contorno oscuro para verse sobre cualquier fondo.
Las formas se definen en una rejilla de 32 unidades y se rasterizan sin suavizado a cada tamano.
Recuerda: KDE solo busca temas de cursor en `icons/` (ver aprendizaje cursor-kde-solo-busca-en-icons).
"""
import math
import os
import shutil
import struct
import sys
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[1]
sys.path.insert(0, str(RAIZ / 'tema'))
from paleta import PAL  # noqa: E402

OUT = RAIZ / 'paquete/neongrid/share/icons/NeonGrid-cursors'
TAMANOS = (24, 32, 48)

CY = PAL['cian'] + (255,)
MG = PAL['magenta'] + (255,)
MGT = PAL['magenta_t'] + (255,)
GR = PAL['verde'] + (255,)
AM = PAL['ambar'] + (255,)
RD = PAL['rojo'] + (255,)
RDT = PAL['rojo_t'] + (255,)
VIO = PAL['violeta'] + (255,)
FILL = PAL['panel'] + (255,)
CONTORNO = (4, 5, 14, 255)


def mezcla(a, b, t):
    return tuple(int(a[i] * t + b[i] * (1 - t)) for i in range(3)) + (255,)


# ------------------------------------------------------------ rasterizado
class Ctx:
    def __init__(self, n):
        self.n = n
        self.f = n / 32.0

    def s(self, v):
        return round(v * self.f)

    def pts(self, pts):
        return [(self.s(x), self.s(y)) for x, y in pts]


def poly(pts):
    def f(d, c):
        d.polygon(c.pts(pts), fill=255)
    return f


def rect(x0, y0, x1, y1):
    def f(d, c):
        d.rectangle([c.s(x0), c.s(y0), max(c.s(x1) - 1, c.s(x0)), max(c.s(y1) - 1, c.s(y0))], fill=255)
    return f


def anillo(cx, cy, r, w):
    def f(d, c):
        d.ellipse([c.s(cx - r), c.s(cy - r), c.s(cx + r) - 1, c.s(cy + r) - 1], outline=255, width=max(1, c.s(w)))
    return f


def linea(x0, y0, x1, y1, w):
    def f(d, c):
        d.line([c.s(x0), c.s(y0), c.s(x1), c.s(y1)], fill=255, width=max(1, c.s(w)))
    return f


def disco(cx, cy, r):
    def f(d, c):
        d.ellipse([c.s(cx - r), c.s(cy - r), c.s(cx + r) - 1, c.s(cy + r) - 1], fill=255)
    return f


def sello(rows, ox, oy, u):
    """Mapa de bits (cadenas con X) como union de cuadrados de u unidades."""
    def f(d, c):
        for j, fila in enumerate(rows):
            for i, ch in enumerate(fila):
                if ch == 'X':
                    d.rectangle([c.s(ox + i * u), c.s(oy + j * u), max(c.s(ox + (i + 1) * u) - 1, c.s(ox + i * u)),
                                 max(c.s(oy + (j + 1) * u) - 1, c.s(oy + j * u))], fill=255)
    return f


def forma(n, partes, borde=CY, relleno=FILL, magenta=None, contorno=True, grosor=None):
    """Rasteriza la union de `partes` con relleno, borde (1-2 px), contorno oscuro y punta magenta."""
    c = Ctx(n)
    m = Image.new('L', (n, n), 0)
    d = ImageDraw.Draw(m)
    for p in partes:
        p(d, c)
    t = grosor or (1 if n < 40 else 2)
    interior = m.filter(ImageFilter.MinFilter(2 * t + 1))
    borde_m = ImageChops.subtract(m, interior)
    ext = ImageChops.subtract(m.filter(ImageFilter.MaxFilter(2 * t + 1)), m) if contorno else None
    out = Image.new('RGBA', (n, n), (0, 0, 0, 0))
    px = out.load()
    mm, ii, bb = m.load(), interior.load(), borde_m.load()
    ee = ext.load() if ext else None
    for y in range(n):
        for x in range(n):
            if ii[x, y]:
                px[x, y] = relleno
            elif bb[x, y]:
                col = borde
                if magenta and magenta((x + .5) / c.f, (y + .5) / c.f):
                    col = MG
                px[x, y] = col
            elif ee and ee[x, y]:
                px[x, y] = CONTORNO
    return out


def apila(*imgs):
    base = imgs[0].copy()
    for i in imgs[1:]:
        base.alpha_composite(i)
    return base


def cerca(px, py, r):
    return lambda x, y: (x - px) ** 2 + (y - py) ** 2 <= r * r


# ------------------------------------------------------------ formas (rejilla de 32)
FLECHA = [(3, 2), (3, 26), (9, 20), (14, 29), (18, 27), (13, 18), (21, 18)]
MANO = [(11, 4), (13, 3), (15, 4), (16, 12), (18, 11), (20, 12), (21, 13), (24, 13), (26, 15), (27, 17), (27, 24), (24, 28),
        (12, 28), (9, 23), (6, 18), (8, 16), (11, 19)]
EW = [(2, 16), (9, 9), (9, 14), (23, 14), (23, 9), (30, 16), (23, 23), (23, 18), (9, 18), (9, 23)]
IBEAM = [(11, 4), (21, 4), (21, 7), (18, 7), (18, 25), (21, 25), (21, 28), (11, 28), (11, 25), (14, 25), (14, 7), (11, 7)]


def rota(pts, ang, esc=1.0, c=(16, 16)):
    a = math.radians(ang)
    ca, sa = math.cos(a), math.sin(a)
    return [(round(c[0] + ((x - c[0]) * ca - (y - c[1]) * sa) * esc, 1), round(c[1] + ((x - c[0]) * sa + (y - c[1]) * ca) * esc, 1)) for x, y in pts]


def esc_desde(pts, k, o=(3, 2)):
    return [(o[0] + (x - o[0]) * k, o[1] + (y - o[1]) * k) for x, y in pts]


SIG_MAS = ['.X.', 'XXX', '.X.']
Q = ['XX.', '..X', '.X.', '...', '.X.']
MAS5 = ['..X..', '..X..', 'XXXXX', '..X..', '..X..']
LINK = ['XXXX', 'X..X', '.XXX', '..X.']
MENU = ['XXX', '...', 'XXX', '...', 'XXX']


def c_flecha(n):
    return forma(n, [poly(FLECHA)], magenta=cerca(3, 2, 6)), (3, 2)


def c_flecha_con(n, simbolo, color):
    base = forma(n, [poly(FLECHA)], magenta=cerca(3, 2, 6))
    if simbolo == '?':
        s = forma(n, [sello(Q, 21, 18, 2.4)], borde=color, relleno=color)
    elif simbolo == '+':
        s = forma(n, [sello(MAS5, 20, 19, 2.2)], borde=color, relleno=color)
    elif simbolo == 'l':
        s = forma(n, [sello(LINK, 20, 20, 2.8)], borde=color, relleno=color)
    else:
        s = forma(n, [sello(MENU, 21, 19, 2.6)], borde=color, relleno=color)
    return apila(base, s), (3, 2)


def c_mano(n):
    return forma(n, [poly(MANO)], magenta=lambda x, y: y < 9), (13, 3)


def c_ibeam(n):
    return forma(n, [poly(IBEAM)], magenta=cerca(16, 16, 3.5)), (16, 16)


def c_ibeam_v(n):
    return forma(n, [poly([(y, x) for x, y in IBEAM])], magenta=cerca(16, 16, 3.5)), (16, 16)


def c_cruz(n):
    base = forma(n, [rect(3, 15, 13, 18), rect(19, 15, 29, 18), rect(15, 3, 18, 13), rect(15, 19, 18, 29)])
    centro = forma(n, [rect(14, 14, 18, 18)], borde=MG, relleno=MG)
    return apila(base, centro), (16, 16)


def c_doble(ang, esc=1.0):
    return lambda n: (forma(n, [poly(rota(EW, ang, esc))], magenta=lambda x, y: (x - 16) ** 2 + (y - 16) ** 2 > 90), (16, 16))


def c_mover(n):
    return forma(n, [poly(EW), poly(rota(EW, 90))], magenta=lambda x, y: (x - 16) ** 2 + (y - 16) ** 2 > 110), (16, 16)


def c_prohibido(n):
    return forma(n, [anillo(16, 16, 12, 4), linea(8, 24, 24, 8, 4)], borde=RDT, relleno=RD), (16, 16)


def c_lupa(mas):
    def f(n):
        base = forma(n, [anillo(13, 13, 9, 3), linea(19, 19, 28, 28, 4)], magenta=lambda x, y: x > 21 and y > 21)
        sg = forma(n, [rect(9, 12, 18, 15)] + ([rect(12, 9, 15, 18)] if mas else []), borde=MG, relleno=MG, contorno=False)
        return apila(base, sg), (13, 13)
    return f


def c_grab(n):
    return forma(n, [rect(9, 8, 12, 16), rect(13, 5, 16, 16), rect(17, 6, 20, 16), rect(21, 9, 24, 16), rect(8, 14, 25, 27), rect(5, 15, 9, 21)],
                 magenta=lambda x, y: y < 9), (16, 16)


def c_grabbing(n):
    return forma(n, [rect(8, 12, 26, 27), rect(9, 10, 12, 13), rect(13, 9, 16, 13), rect(17, 9, 20, 13), rect(21, 10, 24, 13), rect(6, 16, 9, 22)],
                 magenta=lambda x, y: y < 13), (16, 18)


def puntos_espera(n, cx, cy, r, u, frame):
    c = Ctx(n)
    capas = []
    orden = []
    for i in range(8):
        a = i / 8 * 2 * math.pi - math.pi / 2
        orden.append((i, cx + r * math.cos(a), cy + r * math.sin(a)))
    rampa = [MG, MGT, CY, mezcla(PAL['cian'], PAL['fondo'], .6), mezcla(PAL['violeta'], PAL['fondo'], .8), mezcla(PAL['violeta'], PAL['fondo'], .55),
             mezcla(PAL['violeta'], PAL['fondo'], .4), mezcla(PAL['violeta'], PAL['fondo'], .3)]
    for i, x, y in orden:
        col = rampa[(frame - i) % 8]
        capas.append(forma(n, [rect(x - u / 2, y - u / 2, x + u / 2, y + u / 2)], borde=col, relleno=col, grosor=1))
    return apila(*capas)


def c_espera(frame):
    return lambda n: (puntos_espera(n, 16, 16, 10, 5, frame), (16, 16))


def c_progreso(frame):
    def f(n):
        base = forma(n, [poly(esc_desde(FLECHA, .8))], magenta=cerca(3, 2, 6))
        return apila(base, puntos_espera(n, 23.5, 23.5, 5.5, 3.2, frame)), (3, 2)
    return f


BASE = {
    'default': c_flecha, 'pointer': c_mano, 'text': c_ibeam, 'vertical-text': c_ibeam_v, 'crosshair': c_cruz,
    'move': c_mover, 'ew-resize': c_doble(0), 'ns-resize': c_doble(90), 'nwse-resize': c_doble(45, .9), 'nesw-resize': c_doble(-45, .9),
    'not-allowed': c_prohibido, 'help': lambda n: c_flecha_con(n, '?', AM), 'copy': lambda n: c_flecha_con(n, '+', GR),
    'alias': lambda n: c_flecha_con(n, 'l', CY), 'context-menu': lambda n: c_flecha_con(n, 'm', CY),
    'grab': c_grab, 'grabbing': c_grabbing, 'zoom-in': c_lupa(True), 'zoom-out': c_lupa(False),
}
ANIM = {'wait': c_espera, 'progress': c_progreso}

ALIAS = {
    'default': 'left_ptr arrow top_left_arrow right_ptr X_cursor draft_large draft_small dnd-ask dnd-move dnd-link',
    'pointer': 'hand hand1 hand2 pointing_hand openhand e29285e634086352946a0e7090d73106 9d800788f1b08800ae810202380a0822',
    'text': 'xterm ibeam', 'crosshair': 'cross tcross cross_reverse diamond_cross plus cell',
    'move': 'fleur all-scroll size_all grab-all dnd-none',
    'ew-resize': 'col-resize sb_h_double_arrow size_hor h_double_arrow e-resize w-resize split_h left_side right_side 14fef782d02440884392942c11205230',
    'ns-resize': 'row-resize sb_v_double_arrow size_ver v_double_arrow n-resize s-resize split_v top_side bottom_side 2870a09082c103050810ffdffffe0204',
    'nwse-resize': 'size_fdiag nw-resize se-resize top_left_corner bottom_right_corner c7088f0f3e6c8088236ef8e1e3e70000 bd_double_arrow',
    'nesw-resize': 'size_bdiag ne-resize sw-resize top_right_corner bottom_left_corner fcf1c3c7cd4491d801f1e1c78f100000 fd_double_arrow',
    'not-allowed': 'crossed_circle no-drop forbidden circle dnd-no-drop 03b6e0fcb3499374a867c041f52298f0',
    'help': 'question_arrow whats_this left_ptr_help d9ce0ab605698f320427677b458ad60b',
    'grabbing': 'closedhand dnd-grabbing fcf21c00b30f7e3f83fe0dfd12e71cff', 'grab': 'dnd_grab',
    'zoom-in': 'zoom_in', 'zoom-out': 'zoom_out', 'copy': 'dnd-copy 1081e37283d90000800003c07f3ef6bf',
    'alias': '3085a0e285b5c0f0c0 dnd-link-alias', 'context-menu': 'context_menu',
    'wait': 'watch', 'progress': 'left_ptr_watch half-busy 08e8e1c95fe2fc01f976f1e063a24ccd',
}


# ------------------------------------------------------------ Xcursor
XC_IMAGE = 0xfffd0002


def pixeles(im):
    """ARGB premultiplicado (lo que exige Xcursor)."""
    out = []
    raw = im.tobytes()
    for i in range(0, len(raw), 4):
        r, g, b, a = raw[i:i + 4]
        if a == 0:
            out.append(0)
        else:
            out.append((a << 24) | ((r * a // 255) << 16) | ((g * a // 255) << 8) | (b * a // 255))
    return out


def escribe_xcursor(ruta, cuadros):
    """cuadros: lista de (tamano_nominal, im RGBA, (xhot, yhot), retardo_ms)."""
    n = len(cuadros)
    pos = 16 + 12 * n
    toc, cuerpo = b'', b''
    for (nominal, im, hot, delay) in cuadros:
        w, h = im.size
        toc += struct.pack('<III', XC_IMAGE, nominal, pos + len(cuerpo))
        px = pixeles(im)
        cuerpo += struct.pack('<IIIIIIIII', 36, XC_IMAGE, nominal, 1, w, h, hot[0], hot[1], delay)
        cuerpo += struct.pack('<%dI' % len(px), *px)
    Path(ruta).write_bytes(b'Xcur' + struct.pack('<III', 16, 0x10000, n) + toc + cuerpo)


def hot_en(hot, n):
    return min(n - 1, max(0, round(hot[0] * n / 32))), min(n - 1, max(0, round(hot[1] * n / 32)))


def construir():
    if OUT.exists():
        shutil.rmtree(OUT)
    cur = OUT / 'cursors'
    cur.mkdir(parents=True)
    for nombre, f in BASE.items():
        cuadros = []
        for n in TAMANOS:
            im, hot = f(n)
            cuadros.append((n, im, hot_en(hot, n), 0))
        escribe_xcursor(cur / nombre, cuadros)
    for nombre, f in ANIM.items():
        cuadros = []
        for n in TAMANOS:
            for fr in range(8):
                im, hot = f(fr)(n)
                cuadros.append((n, im, hot_en(hot, n), 90))
        escribe_xcursor(cur / nombre, cuadros)
    for base, nombres in ALIAS.items():
        for a in nombres.split():
            if a != base and not (cur / a).exists():
                os.symlink(base, cur / a)
    (OUT / 'index.theme').write_text('[Icon Theme]\nName=NeonGrid-cursors\nComment=Cursor pixel art cyberpunk para NeonGrid (borde cian, punta magenta)\n'
                                     'Inherits=breeze_cursors\n')
    return len(list(cur.iterdir()))


if __name__ == '__main__':
    print('entradas en cursors/:', construir())
