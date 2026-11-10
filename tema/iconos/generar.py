#!/usr/bin/env python3
"""NeonGrid - generador del tema de iconos `NeonGrid` (pixel art, rejilla de 32 px).

Herramienta de CONSTRUCCION (usa Pillow; en el paquete solo van los PNG/SVG resultantes).
Uso:  python3 generar.py          -> escribe paquete/neongrid/share/icons/NeonGrid/ y tema/iconos/vista-previa.png

Estilo: baldosas de app biseladas (borde de acento, luz arriba-izquierda, sombra dura de 1 px),
glifos con linea cian y detalle magenta, carpetas finas de 3 tonos violeta con linea de luz y
borde interior (version llena con hojas asomando). Todo lo no cubierto cae a breeze-dark.
Salida por icono: 32x32 PNG, 64x64 PNG (x2 exacto) y SVG escalable (un rect por tramo de pixeles).
"""
import os
import shutil
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[1]
sys.path.insert(0, str(RAIZ / 'tema'))
from paleta import PAL  # noqa: E402

OUT = RAIZ / 'paquete/neongrid/share/icons/NeonGrid'
S = 32

# ---------------------------------------------------------------- colores
def mixc(a, b, t):
    """t = fraccion de a (0..1) sobre b."""
    return tuple(int(round(a[i] * t + b[i] * (1 - t))) for i in range(3)) + (255,)

FONDO, PANEL, BOTON = PAL['fondo'], PAL['panel'], PAL['boton']
CY = PAL['cian'] + (255,)
MG = PAL['magenta'] + (255,)
GR = PAL['verde'] + (255,)
AM = PAL['ambar'] + (255,)
RD = PAL['rojo'] + (255,)
VIO = PAL['violeta']
VIOC = PAL['violeta_claro'] + (255,)
TEN = PAL['tenue'] + (255,)
TXT = PAL['texto'] + (255,)
CYD = mixc(PAL['cian'], FONDO, .55)
MGD = mixc(PAL['magenta'], FONDO, .55)
DIM = mixc(VIO, FONDO, .45)           # apagado / inactivo
SOMBRA = (5, 6, 16, 205)
# rampa violeta de 4 tonos para carpetas (+ borde)
V_RIM = mixc(VIO, FONDO, .14)
V_D = mixc(VIO, FONDO, .30)
V_M = mixc(VIO, FONDO, .50)
V_L = mixc(VIO, FONDO, .70)
V_X = mixc(VIO, FONDO, .20)           # sombra interior


class L:
    """Capa de 32x32 RGBA sin suavizado."""
    def __init__(s):
        s.im = Image.new('RGBA', (S, S), (0, 0, 0, 0))
        s.d = ImageDraw.Draw(s.im)

    def r(s, x, y, w, h, c):
        if w > 0 and h > 0:
            s.d.rectangle([x, y, x + w - 1, y + h - 1], fill=c)

    def ro(s, x, y, w, h, c):
        s.d.rectangle([x, y, x + w - 1, y + h - 1], outline=c)

    def p(s, x, y, c):
        s.d.point((x, y), fill=c)

    def ln(s, pts, c, w=1):
        s.d.line(pts, fill=c, width=w)

    def poly(s, pts, fill, outline=None):
        s.d.polygon(pts, fill=fill)
        if outline:
            s.d.line(list(pts) + [pts[0]], fill=outline, width=1)

    def ell(s, box, outline=None, fill=None, w=1):
        s.d.ellipse(box, fill=fill, outline=outline, width=w)

    def arc(s, box, a0, a1, c, w=1):
        s.d.arc(box, a0, a1, fill=c, width=w)


def comp(*capas, sombra=True):
    """Apila capas; cada una proyecta una sombra dura de 1 px (abajo-derecha)."""
    out = Image.new('RGBA', (S, S), (0, 0, 0, 0))
    for c in capas:
        if sombra:
            m = c.im.split()[3].point(lambda v: 255 if v else 0)
            m2 = Image.new('L', (S, S), 0)
            m2.paste(m, (1, 1))
            sh = Image.new('RGBA', (S, S), SOMBRA)
            sh.putalpha(m2.point(lambda v: SOMBRA[3] if v else 0))
            out.alpha_composite(sh)
        out.alpha_composite(c.im)
    return out


# ---------------------------------------------------------------- baldosa de aplicacion
def baldosa(acento):
    """Baldosa 31x31 biselada: borde de acento, luz arriba-izquierda, sombra abajo-derecha."""
    a = acento[:3]
    rim = mixc(a, FONDO, .30)
    luz = mixc(a, FONDO, .80)
    lum = mixc(a, FONDO, .60)
    somb = mixc(a, FONDO, .18)
    t = L()
    t.r(1, 0, 29, 31, rim)
    t.r(0, 1, 31, 29, rim)
    # relleno en 3 bandas (degradado discreto)
    t.r(2, 1, 27, 11, mixc(PAL['boton'], PAL['panel'], .75))
    t.r(1, 2, 29, 9, mixc(PAL['boton'], PAL['panel'], .75))
    t.r(1, 12, 29, 10, PAL['boton'] + (255,))
    t.r(1, 22, 29, 7, PAL['panel'] + (255,))
    t.r(2, 29, 27, 1, PAL['panel'] + (255,))
    # bisel: luz arriba y a la izquierda, sombra abajo y a la derecha
    t.r(2, 1, 27, 1, luz)
    t.r(1, 2, 1, 27, luz)
    t.r(2, 2, 6, 1, lum)
    t.p(2, 2, TXT)
    t.r(2, 29, 27, 1, somb)
    t.r(29, 2, 1, 27, somb)
    # esquinas muescadas
    for x, y in ((0, 0), (30, 0), (0, 30), (30, 30)):
        t.p(x, y, (0, 0, 0, 0))
    return t


def tile(acento, glifo):
    g = L()
    glifo(g)
    return comp(baldosa(acento), g)


# ---------------------------------------------------------------- sync (compartido)
import math  # noqa: E402


def sync_arrows(g, cx, cy, r, w, c1, c2, punta=4):
    for (a0, a1, c) in ((200, 340, c1), (20, 160, c2)):
        g.arc((cx - r, cy - r, cx + r, cy + r), a0, a1, c, w)
        a = math.radians(a1)
        ex, ey = cx + r * math.cos(a), cy + r * math.sin(a)
        dx, dy = -math.sin(a), math.cos(a)
        rx, ry = math.cos(a), math.sin(a)
        tip = (round(ex + dx * punta), round(ey + dy * punta))
        b1 = (round(ex + rx * punta), round(ey + ry * punta))
        b2 = (round(ex - rx * punta), round(ey - ry * punta))
        g.poly([tip, b1, b2], c)


def cruz(g, x, y, n, c, w=2):
    g.ln([(x, y), (x + n, y + n)], c, w)
    g.ln([(x + n, y), (x, y + n)], c, w)


def check(g, pts, c, w=2):
    g.ln(pts, c, w)


# ---------------------------------------------------------------- glifos de baldosa
def gl_terminal(g):
    g.ln([(8, 10), (14, 16), (8, 22)], CY, 2)
    g.r(16, 21, 7, 2, MG)
    g.r(17, 11, 7, 1, CYD)


def gl_archivos(g):
    g.ro(7, 9, 7, 5, CY)
    g.ro(7, 12, 17, 11, CY)
    g.r(8, 13, 15, 1, MG)
    g.r(9, 16, 9, 1, CYD)
    g.r(9, 19, 6, 1, CYD)


def gl_navegador(g):
    g.ell((7, 7, 24, 24), outline=CY)
    g.ell((12, 7, 19, 24), outline=CY)
    g.ln([(7, 15), (24, 15)], CY)
    g.ln([(9, 11), (22, 11)], CYD)
    g.ln([(9, 19), (22, 19)], CYD)
    g.r(20, 9, 3, 3, MG)


def gl_editor(g):
    g.ln([(12, 10), (7, 15), (12, 20)], CY, 2)
    g.ln([(19, 10), (24, 15), (19, 20)], CY, 2)
    g.ln([(17, 8), (14, 23)], MG, 2)


def gl_ajustes(g):
    g.ell((9, 9, 22, 22), outline=CY, w=3)
    for (x, y, w, h) in ((14, 5, 3, 4), (14, 22, 3, 4), (5, 14, 4, 3), (22, 14, 4, 3),
                         (8, 8, 3, 3), (20, 8, 3, 3), (8, 20, 3, 3), (20, 20, 3, 3)):
        g.r(x, y, w, h, CY)
    g.r(14, 14, 3, 3, MG)


def gl_sync(g):
    sync_arrows(g, 15, 15, 8, 2, CY, MG, 4)


def gl_red(g):
    wifi(g, 15, 22, 3)
    g.r(14, 21, 3, 3, MG)


def gl_nota(g):
    g.r(10, 9, 11, 14, TEN)
    g.r(10, 9, 11, 1, TXT)
    for i, y in enumerate((12, 15, 18)):
        g.r(12, y, 7 - (i == 2) * 3, 1, CYD if i else MG)


# ---------------------------------------------------------------- glifos de estado
def wifi(g, cx, cy, n, dim=DIM, cl=CY, w=2):
    for i, r in enumerate((5, 10, 15)):
        g.arc((cx - r, cy - r, cx + r, cy + r), 225, 315, cl if i < n else dim, w)


def altavoz(g, nivel, mudo=False, cx=17):
    g.r(5, 13, 5, 7, CY)
    g.poly([(10, 13), (16, 8), (16, 25), (10, 20)], CY)
    g.r(5, 13, 5, 1, TXT)
    if mudo:
        cruz(g, 20, 12, 7, RD, 2)
        return
    for i, r in enumerate((4, 8, 12)):
        if i < nivel:
            g.arc((cx - r, 16 - r, cx + r, 16 + r), 310, 50, MG, 2)


def bateria(g, pct, carga=False, falta=False):
    col = GR if pct >= 40 else (AM if pct >= 20 else RD)
    g.ro(3, 9, 23, 14, DIM if falta else CY)
    g.r(26, 13, 3, 6, DIM if falta else CY)
    g.r(4, 10, 21, 12, FONDO + (255,))
    if not falta:
        ancho = round(19 * pct / 100)
        if ancho:
            g.r(5, 11, ancho, 10, col)
            g.r(5, 11, ancho, 1, mixc(col[:3], (255, 255, 255), .6))
    if pct < 20 and not falta:
        g.r(14, 12, 3, 5, RD[:3] + (255,))
        g.r(14, 18, 3, 2, RD)
        g.r(14, 12, 3, 5, TXT)
        g.r(14, 18, 3, 2, TXT)
    if falta:
        g.r(13, 12, 5, 3, TEN)
        g.r(15, 15, 2, 3, TEN)
        g.r(15, 19, 2, 2, TEN)
    if carga:
        g.poly([(17, 5), (11, 16), (15, 16), (14, 26), (21, 14), (17, 14), (19, 5)], MG)


def escudo(g, color, relleno):
    pts = [(6, 6), (16, 3), (26, 6), (26, 15), (21, 23), (16, 27), (11, 23), (6, 15)]
    g.poly(pts, relleno, color)
    g.poly([(7, 7), (16, 4), (25, 7), (25, 15), (20, 22), (16, 26), (12, 22), (7, 15)], None, color)


def gl_vpn(g, estado):
    if estado == 'on':
        escudo(g, CY, mixc(PAL['cian'], FONDO, .22))
        check(g, [(11, 15), (15, 19), (22, 10)], GR, 3)
    elif estado == 'off':
        escudo(g, DIM, mixc(VIO, FONDO, .18))
        cruz(g, 11, 10, 9, RD, 3)
    else:
        escudo(g, AM, mixc(PAL['ambar'], FONDO, .18))
        for x in (10, 15, 20):
            g.r(x, 15, 3, 3, AM)


def gl_red_cable(g, estado):
    g.ro(7, 6, 18, 13, CY if estado != 'off' else DIM)
    for x in (10, 13, 16, 19, 22):
        g.r(x, 7, 1, 4, MG if estado != 'off' else DIM)
    g.r(14, 19, 4, 3, CY if estado != 'off' else DIM)
    g.r(15, 22, 2, 6, CY if estado != 'off' else DIM)
    if estado == 'off':
        cruz(g, 19, 17, 8, RD, 2)


def gl_apagar(g):
    g.arc((7, 8, 25, 26), 305, 235, CY, 3)
    g.r(15, 3, 3, 13, MG)


def gl_reiniciar(g):
    g.arc((7, 7, 25, 25), 300, 220, CY, 3)
    g.poly([(16, 3), (16, 11), (22, 7)], MG)


def gl_bloqueo(g):
    g.ro(9, 14, 14, 12, CY)
    g.r(10, 15, 12, 10, mixc(PAL['cian'], FONDO, .2))
    g.arc((11, 4, 21, 20), 180, 360, CY, 2)
    g.r(15, 18, 3, 4, MG)


def gl_salir(g):
    g.ro(5, 5, 11, 22, CY)
    g.ln([(12, 16), (27, 16)], MG, 2)
    g.poly([(27, 16), (21, 11), (21, 21)], MG)


# ---------------------------------------------------------------- carpetas
def poly_tab(c, pts):
    c.poly(pts, V_RIM)


def carpeta(emblema=None, lleno=False):
    back = L()
    # silueta trasera: cuerpo + pestana biselada
    back.r(2, 8, 27, 19, V_RIM)
    back.poly([(3, 5), (12, 5), (15, 8), (15, 9), (3, 9)], V_RIM)
    back.r(3, 6, 9, 3, V_M)
    back.r(4, 6, 7, 1, V_L)
    back.p(12, 7, V_M)
    back.p(13, 8, V_M)
    back.r(3, 9, 25, 16, V_D)
    back.r(15, 9, 12, 1, V_L)             # luz del borde trasero
    back.r(3, 6, 1, 3, V_L)               # luz izquierda de la pestana
    back.p(3, 6, VIOC)
    capas = [back]
    if lleno:
        h = L()
        h.r(7, 3, 14, 10, mixc(PAL['tenue'], FONDO, .85))
        h.r(7, 3, 14, 1, TXT)
        h.r(7, 3, 1, 10, TXT)
        h.r(9, 6, 8, 1, CYD)
        h.r(9, 8, 11, 1, MGD)
        h.r(14, 6, 14, 7, mixc(PAL['cian'], FONDO, .55))
        h.r(14, 6, 14, 1, CY)
        h.r(14, 6, 1, 7, CY)
        h.r(16, 9, 9, 1, mixc(PAL['cian'], FONDO, .25))
        h.p(7, 3, (0, 0, 0, 0))
        capas.append(h)
    f = L()
    f.r(2, 11, 27, 16, V_RIM)
    f.r(3, 12, 25, 14, V_M)
    f.r(3, 12, 25, 1, VIOC)               # linea de luz superior
    f.r(3, 13, 25, 3, V_L)
    f.r(3, 22, 25, 4, V_D)
    f.r(3, 13, 1, 12, V_L)                # borde interior izquierdo (luz)
    f.r(27, 13, 1, 13, V_X)               # borde interior derecho (sombra)
    f.r(3, 25, 25, 1, V_X)
    for x, y in ((2, 11), (28, 11), (2, 26), (28, 26)):
        f.p(x, y, (0, 0, 0, 0))
    capas.append(f)
    if emblema:
        g = L()
        emblema(g)
        capas.append(g)
    return comp(*capas)


def em_docs(g):
    g.r(11, 15, 10, 1, CY)
    g.r(11, 18, 10, 1, CYD)
    g.r(11, 21, 6, 1, MG)


def em_descargas(g):
    g.r(15, 14, 2, 5, CY)
    g.poly([(11, 18), (20, 18), (15, 23), (16, 23)], CY)
    g.r(13, 19, 6, 1, MG)
    g.r(10, 24, 12, 1, CYD)


def em_imagenes(g):
    g.poly([(10, 24), (14, 17), (17, 21), (19, 19), (22, 24)], None, CY)
    g.r(19, 15, 3, 2, MG)


def em_musica(g):
    g.r(17, 15, 2, 8, CY)
    g.ell((12, 21, 17, 24), fill=CY)
    g.ln([(19, 15), (22, 17)], MG, 2)


def em_videos(g):
    g.ro(10, 14, 12, 10, CY)
    g.poly([(14, 16), (14, 22), (19, 19)], MG)


def em_proyectos(g):
    g.ln([(13, 15), (10, 19), (13, 23)], CY)
    g.ln([(18, 15), (21, 19), (18, 23)], CY)
    g.ln([(17, 14), (14, 24)], MG)


def em_casa(g):
    g.poly([(15, 14), (22, 19), (9, 19)], None, CY)
    g.ro(11, 19, 9, 5, CY)
    g.r(15, 21, 2, 3, MG)


def papelera(llena=False):
    capas = []
    if llena:
        p = L()
        p.r(9, 1, 8, 9, mixc(PAL['tenue'], FONDO, .85))
        p.r(9, 1, 8, 1, TXT)
        p.r(11, 4, 5, 1, CYD)
        p.r(15, 3, 9, 8, mixc(PAL['magenta'], FONDO, .5))
        p.r(15, 3, 9, 1, MG)
        p.r(17, 6, 5, 1, MG)
        capas.append(p)
    b = L()
    b.poly([(7, 9), (24, 9), (22, 28), (9, 28)], V_RIM)
    b.poly([(8, 10), (23, 10), (21, 27), (10, 27)], V_M)
    b.r(9, 10, 14, 1, V_L)
    b.ln([(8, 10), (10, 26)], V_L)
    b.ln([(23, 10), (21, 26)], V_X)
    for x in (13, 16, 19):
        b.r(x, 13, 1, 11, V_D)
        b.r(x, 13, 1, 1, V_L)
    lid = L()
    lid.r(5, 6, 21, 4, V_RIM)
    lid.r(6, 7, 19, 2, V_L)
    lid.r(6, 7, 19, 1, VIOC)
    lid.r(12, 4, 7, 2, V_RIM)
    lid.r(13, 4, 5, 1, V_L)
    capas += [b, lid]
    if llena:
        e = L()
        e.r(14, 12, 3, 1, MG)
    return comp(*capas)


# ---------------------------------------------------------------- tipos MIME
FUENTE3 = {
    'P': ['XXX', 'X.X', 'XXX', 'X..', 'X..'],
    'D': ['XX.', 'X.X', 'X.X', 'X.X', 'XX.'],
    'F': ['XXX', 'X..', 'XX.', 'X..', 'X..'],
    'Z': ['XXX', '..X', '.X.', 'X..', 'XXX'],
    'I': ['XXX', '.X.', '.X.', '.X.', 'XXX'],
    'T': ['XXX', '.X.', '.X.', '.X.', '.X.'],
    'A': ['.X.', 'X.X', 'XXX', 'X.X', 'X.X'],
    'R': ['XX.', 'X.X', 'XX.', 'X.X', 'X.X'],
    'S': ['XXX', 'X..', 'XXX', '..X', 'XXX'],
    'H': ['X.X', 'X.X', 'XXX', 'X.X', 'X.X'],
    'M': ['X.X', 'XXX', 'XXX', 'X.X', 'X.X'],
    'L': ['X..', 'X..', 'X..', 'X..', 'XXX'],
    '?': ['XX.', '..X', '.X.', '...', '.X.'],
}


def texto3(g, x, y, s, c):
    for i, ch in enumerate(s):
        for j, fila in enumerate(FUENTE3[ch]):
            for k, v in enumerate(fila):
                if v == 'X':
                    g.p(x + i * 4 + k, y + j, c)


def pagina(acento, badge):
    a = acento[:3]
    rim = mixc(a, FONDO, .38)
    luz = mixc(a, FONDO, .85)
    somb = mixc(a, FONDO, .22)
    p = L()
    pts = [(6, 2), (18, 2), (25, 9), (25, 29), (6, 29)]
    p.poly(pts, rim)
    p.r(7, 3, 11, 26, mixc(PAL['boton'], PAL['panel'], .8))
    p.r(7, 9, 18, 20, mixc(PAL['boton'], PAL['panel'], .8))
    p.r(7, 20, 18, 9, PAL['panel'] + (255,))
    p.poly([(18, 3), (24, 9), (18, 9)], mixc(a, FONDO, .5))
    p.ln([(18, 2), (18, 9), (25, 9)], rim)
    p.r(7, 3, 1, 26, luz)                 # luz izquierda
    p.r(7, 3, 11, 1, luz)                 # luz superior
    p.r(8, 28, 17, 1, somb)               # sombra inferior
    p.r(24, 10, 1, 19, somb)
    p.p(18, 2, (0, 0, 0, 0))
    g = L()
    badge(g)
    return comp(p, g)


def b_texto(g):
    for i, (y, w, c) in enumerate(((13, 11, CY), (16, 11, CYD), (19, 11, CYD), (22, 6, MG))):
        g.r(10, y, w, 1, c)


def b_imagen(g):
    g.poly([(9, 25), (13, 18), (16, 22), (18, 20), (22, 25)], None, CY)
    g.r(18, 13, 3, 3, MG)


def b_audio(g):
    g.r(16, 14, 2, 9, CY)
    g.ell((11, 21, 16, 25), fill=CY)
    g.ln([(18, 14), (21, 17)], MG, 2)


def b_video(g):
    g.ro(9, 13, 13, 11, CY)
    g.poly([(13, 15), (13, 22), (18, 18)], MG)
    for y in (14, 17, 20, 23):
        g.p(9, y, MG)
        g.p(21, y, MG)


def b_pdf(g):
    texto3(g, 9, 17, 'PDF', RD[:3] + (255,))
    g.r(9, 14, 13, 1, MGD)


def b_zip(g):
    for i in range(6):
        g.r(14 + (i % 2) * 2, 11 + i * 2, 2, 1, AM)
    g.ro(14, 23, 5, 4, AM)
    g.p(16, 24, MG)


AMD = mixc(PAL['ambar'], FONDO, .5)


def b_codigo(g):
    g.ln([(12, 15), (9, 19), (12, 23)], CY)
    g.ln([(19, 15), (22, 19), (19, 23)], CY)
    g.ln([(17, 14), (14, 24)], MG)


def b_shell(g):
    g.ln([(9, 15), (14, 19), (9, 23)], GR, 2)
    g.r(16, 22, 6, 2, MG)


def b_json(g):
    g.ln([(13, 14), (11, 15), (11, 18), (9, 19), (11, 20), (11, 23), (13, 24)], CY)
    g.ln([(18, 14), (20, 15), (20, 18), (22, 19), (20, 20), (20, 23), (18, 24)], CY)
    g.r(15, 19, 2, 2, MG)


def b_html(g):
    g.ln([(12, 15), (9, 19), (12, 23)], MG)
    g.ln([(19, 15), (22, 19), (19, 23)], MG)
    g.ln([(17, 14), (14, 24)], CY)


def b_desc(g):
    texto3(g, 13, 16, '?', TEN)
    g.r(14, 24, 3, 1, MG)


def b_tar(g):
    g.ro(10, 13, 11, 11, AM)
    g.r(10, 16, 11, 1, AM)
    g.r(14, 18, 3, 1, MG)


def b_markdown(g):
    texto3(g, 9, 15, 'M', CY)
    g.ln([(18, 15), (18, 20)], MG, 2)
    g.ln([(15, 18), (18, 21), (21, 18)], MG)


# ---------------------------------------------------------------- registro
ICONOS = {}      # nombre -> (contexto, imagen)
ALIAS = []       # (alias, contexto, nombre)
ORDEN = []       # (grupo, nombre) para la hoja de contacto


def reg(grupo, ctx, nombre, im, alias=()):
    ICONOS[nombre] = (ctx, im)
    ORDEN.append((grupo, nombre))
    for a in alias:
        ALIAS.append((a, ctx, nombre))


def construir():
    # --- carpetas (places)
    reg('carpetas', 'places', 'folder', carpeta(), ('inode-directory', 'folder-visiting', 'folder-closed', 'folder-blue'))
    reg('carpetas', 'places', 'folder-full', carpeta(lleno=True), ('folder-open', 'folder-drag-accept', 'folder-open-full'))
    reg('carpetas', 'places', 'folder-documents', carpeta(em_docs), ('folder-text',))
    reg('carpetas', 'places', 'folder-download', carpeta(em_descargas), ('folder-downloads',))
    reg('carpetas', 'places', 'folder-pictures', carpeta(em_imagenes), ('folder-image',))
    reg('carpetas', 'places', 'folder-music', carpeta(em_musica), ('folder-sound',))
    reg('carpetas', 'places', 'folder-videos', carpeta(em_videos), ('folder-video',))
    reg('carpetas', 'places', 'folder-development', carpeta(em_proyectos), ('folder-projects', 'folder-code', 'folder-git', 'folder-script'))
    reg('carpetas', 'places', 'user-home', carpeta(em_casa), ('folder-home', 'go-home-large'))
    reg('carpetas', 'places', 'user-trash', papelera(False), ('trash-empty', 'edittrash', 'user-trash-empty'))
    reg('carpetas', 'places', 'user-trash-full', papelera(True), ('trash-full', 'trashcan_full'))

    # --- aplicaciones (baldosas)
    reg('apps', 'apps', 'utilities-terminal', tile(GR, gl_terminal),
        ('org.kde.konsole', 'konsole', 'Alacritty', 'alacritty', 'terminal', 'xterm', 'foot', 'kitty', 'org.wezfurlong.wezterm'))
    reg('apps', 'apps', 'system-file-manager', tile(CY, gl_archivos),
        ('org.kde.dolphin', 'dolphin', 'file-manager', 'org.gnome.Nautilus', 'thunar'))
    reg('apps', 'apps', 'internet-web-browser', tile(CY, gl_navegador),
        ('org.mozilla.firefox', 'firefox', 'chromium', 'google-chrome', 'brave-browser', 'org.chromium.Chromium', 'web-browser', 'falkon', 'org.kde.falkon'))
    reg('apps', 'apps', 'accessories-text-editor', tile(MG, gl_editor),
        ('org.kde.kate', 'kate', 'code', 'visual-studio-code', 'com.visualstudio.code', 'code-oss', 'org.kde.kwrite', 'kwrite', 'nvim', 'vim', 'gvim'))
    reg('apps', 'apps', 'preferences-system', tile(VIOC, gl_ajustes),
        ('org.kde.systemsettings', 'systemsettings', 'preferences-desktop', 'preferences-other', 'applications-system', 'configure'))
    reg('apps', 'apps', 'syncthing', tile(GR, gl_sync), ('org.syncthing.syncthing', 'syncthing-gtk', 'syncthingtray'))
    reg('apps', 'apps', 'preferences-system-network', tile(CY, gl_red),
        ('preferences-network', 'org.kde.plasma.networkmanagement', 'nm-device-wireless'))
    reg('apps', 'apps', 'org.kde.kate-notes', tile(AM, gl_nota), ('knotes', 'org.kde.knotes', 'accessories-notes'))

    # --- estado: red
    for niv, n in (('0', 0), ('20', 1), ('40', 1), ('60', 2), ('80', 2), ('100', 3)):
        im = comp(_l(lambda g, n=n: wifi(g, 16, 25, n) or g.r(15, 24, 3, 3, MG if n else DIM)))
        al = [f'network-wireless-connected-{int(niv):02d}' if niv != '0' else 'network-wireless-connected-00',
              f'network-wireless-{niv}-symbolic']
        if niv == '100':
            al += ['network-wireless', 'network-wireless-signal-excellent', 'network-wireless-activated']
        if niv == '20':
            al += ['network-wireless-signal-weak', 'network-wireless-connected-25']
        if niv == '40':
            al += ['network-wireless-signal-low', 'network-wireless-connected-50']
        if niv == '60':
            al += ['network-wireless-signal-ok', 'network-wireless-connected-60', 'network-wireless-connected-75']
        if niv == '80':
            al += ['network-wireless-signal-good', 'network-wireless-connected-80']
        if niv == '0':
            al += ['network-wireless-signal-none']
        reg('estado', 'status', f'network-wireless-{niv}', im, al)

    def wifi_x(g):
        wifi(g, 15, 25, 0)
        g.r(14, 24, 3, 3, DIM)
        cruz(g, 20, 4, 8, RD, 3)
    reg('estado', 'status', 'network-wireless-disconnected', comp(_l(wifi_x)),
        ('network-wireless-off', 'network-wireless-offline', 'network-wireless-available', 'network-wireless-disconnected-symbolic'))

    def wifi_lim(g):
        wifi(g, 15, 25, 2)
        g.r(14, 24, 3, 3, MG)
        g.poly([(24, 3), (29, 12), (19, 12)], AM)
        g.r(24, 6, 1, 3, FONDO + (255,))
        g.r(24, 10, 1, 1, FONDO + (255,))
    reg('estado', 'status', 'network-wireless-60-limited', comp(_l(wifi_lim)),
        ('network-wireless-80-limited', 'network-wireless-100-limited', 'network-wireless-40-limited', 'network-wireless-20-limited', 'network-wireless-0-limited'))
    reg('estado', 'status', 'network-wired', comp(_l(lambda g: gl_red_cable(g, 'on'))),
        ('network-wired-activated', 'network-wired-symbolic', 'network-connect', 'network-wired-available'))
    reg('estado', 'status', 'network-wired-disconnected', comp(_l(lambda g: gl_red_cable(g, 'off'))),
        ('network-wired-unavailable', 'network-wired-disconnected-symbolic'))

    def off_net(g):
        wifi(g, 15, 25, 0)
        cruz(g, 19, 6, 9, RD, 3)
    reg('estado', 'status', 'network-offline', comp(_l(off_net)), ('network-disconnect', 'network-offline-symbolic', 'network-error'))
    reg('estado', 'status', 'network-vpn', comp(_l(lambda g: gl_vpn(g, 'on'))), ('network-vpn-symbolic', 'network-vpn-connected', 'security-high'))
    reg('estado', 'status', 'network-vpn-disconnected', comp(_l(lambda g: gl_vpn(g, 'off'))), ('network-vpn-error', 'network-vpn-disconnected-symbolic'))
    reg('estado', 'status', 'network-vpn-acquiring', comp(_l(lambda g: gl_vpn(g, 'acq'))), ('network-vpn-connecting',))

    # --- estado: volumen
    for nom, niv in (('high', 3), ('medium', 2), ('low', 1)):
        reg('estado', 'status', f'audio-volume-{nom}', comp(_l(lambda g, niv=niv: altavoz(g, niv))), (f'audio-volume-{nom}-symbolic',))
    reg('estado', 'status', 'audio-volume-muted', comp(_l(lambda g: altavoz(g, 0, True))), ('audio-volume-muted-symbolic', 'audio-volume-off'))

    # --- estado: bateria
    for pct in range(0, 101, 10):
        al = [f'battery-{pct:03d}-symbolic']
        if pct == 0:
            al += ['battery-empty', 'battery-caution']
        if pct == 20:
            al += ['battery-low']
        if pct == 60:
            al += ['battery-good']
        if pct == 100:
            al += ['battery-full', 'battery']
        reg('estado', 'status', f'battery-{pct:03d}', comp(_l(lambda g, p=pct: bateria(g, p))), al)
        al = [f'battery-{pct:03d}-charging-symbolic']
        if pct == 0:
            al += ['battery-empty-charging', 'battery-caution-charging']
        if pct == 20:
            al += ['battery-low-charging']
        if pct == 60:
            al += ['battery-good-charging']
        if pct == 100:
            al += ['battery-full-charging', 'battery-charging', 'battery-full-charged']
        reg('estado', 'status', f'battery-{pct:03d}-charging', comp(_l(lambda g, p=pct: bateria(g, p, True))), al)
    reg('estado', 'status', 'battery-missing', comp(_l(lambda g: bateria(g, 0, False, True))), ('battery-missing-symbolic',))

    # --- estado: sincronizacion
    def sync_ok(g):
        sync_arrows(g, 16, 16, 11, 2, DIM, DIM, 4)
        check(g, [(11, 16), (15, 20), (22, 11)], GR, 3)

    def sync_err(g):
        sync_arrows(g, 16, 16, 11, 2, DIM, DIM, 4)
        cruz(g, 11, 11, 9, RD, 3)
    reg('estado', 'status', 'state-sync', comp(_l(lambda g: sync_arrows(g, 16, 16, 11, 2, CY, MG, 5))),
        ('view-refresh', 'emblem-synchronizing', 'sync-synchronizing', 'state-syncing', 'emblem-synchronizing-symbolic', 'view-refresh-symbolic', 'folder-sync'))
    reg('estado', 'status', 'sync-synchronized', comp(_l(sync_ok)), ('state-ok-sync', 'emblem-synchronized'))
    reg('estado', 'status', 'sync-error', comp(_l(sync_err)), ('state-error-sync', 'emblem-synchronizing-error', 'sync-offline'))

    # --- acciones del sistema
    reg('acciones', 'actions', 'system-shutdown', comp(_l(gl_apagar)), ('system-shutdown-symbolic', 'system-shutdown-panel', 'application-exit'))
    reg('acciones', 'actions', 'system-reboot', comp(_l(gl_reiniciar)), ('system-restart', 'system-reboot-symbolic', 'view-restore-reboot'))
    reg('acciones', 'actions', 'system-lock-screen', comp(_l(gl_bloqueo)), ('system-lock-screen-symbolic', 'lock'))
    reg('acciones', 'actions', 'system-log-out', comp(_l(gl_salir)), ('system-log-out-symbolic', 'system-logout', 'application-exit-symbolic'))

    # --- tipos MIME
    reg('mime', 'mimetypes', 'text-x-generic', pagina(CY, b_texto),
        ('text-plain', 'application-x-zerosize', 'text-x-log', 'text-x-readme', 'text-x-generic-template'))
    reg('mime', 'mimetypes', 'text-markdown', pagina(CY, b_markdown), ('text-x-markdown', 'text-x-markdown-symbolic'))
    reg('mime', 'mimetypes', 'image-x-generic', pagina(MG, b_imagen),
        ('image-png', 'image-jpeg', 'image-gif', 'image-webp', 'image-svg+xml', 'image-bmp', 'image-tiff', 'image-x-xcf', 'image-avif'))
    reg('mime', 'mimetypes', 'audio-x-generic', pagina(VIOC, b_audio),
        ('audio-mpeg', 'audio-flac', 'audio-ogg', 'audio-x-wav', 'audio-x-vorbis+ogg', 'audio-mp4', 'audio-x-flac', 'audio-aac'))
    reg('mime', 'mimetypes', 'video-x-generic', pagina(AM, b_video),
        ('video-mp4', 'video-x-matroska', 'video-webm', 'video-mpeg', 'video-quicktime', 'video-x-msvideo', 'video-ogg'))
    reg('mime', 'mimetypes', 'application-pdf', pagina(RD, b_pdf), ('application-x-pdf', 'application-postscript'))
    reg('mime', 'mimetypes', 'application-zip', pagina(AM, b_zip),
        ('application-x-zip', 'application-x-zip-compressed', 'package-x-generic', 'application-x-7z-compressed', 'application-vnd.rar',
         'application-x-rar', 'application-x-archive', 'application-x-compressed', 'application-x-cpio'))
    reg('mime', 'mimetypes', 'application-x-compressed-tar', pagina(AM, b_tar),
        ('application-gzip', 'application-x-tar', 'application-x-bzip', 'application-x-xz', 'application-x-bzip-compressed-tar', 'application-x-xz-compressed-tar',
         'application-zstd', 'application-x-zstd-compressed-tar', 'application-x-gzip'))
    reg('mime', 'mimetypes', 'text-x-script', pagina(GR, b_codigo),
        ('text-x-python', 'text-x-csrc', 'text-x-chdr', 'text-x-c++src', 'text-x-c++hdr', 'text-x-java', 'text-x-rust', 'text-x-go', 'text-x-javascript',
         'application-javascript', 'text-x-typescript', 'text-css', 'text-x-lua', 'text-x-sql', 'text-x-makefile', 'text-x-cmake', 'text-x-perl',
         'application-x-php', 'text-x-php', 'text-x-ruby', 'text-x-source', 'text-x-qml', 'text-x-patch', 'text-x-diff', 'text-x-toml', 'application-toml',
         'application-x-yaml', 'text-yaml', 'text-x-ini', 'text-xml', 'application-xml', 'text-x-csv', 'text-csv'))
    reg('mime', 'mimetypes', 'application-x-shellscript', pagina(GR, b_shell), ('text-x-shellscript', 'application-x-executable-script', 'application-x-executable'))
    reg('mime', 'mimetypes', 'application-json', pagina(CY, b_json), ('text-x-json', 'application-x-json'))
    reg('mime', 'mimetypes', 'text-html', pagina(MG, b_html), ('application-xhtml+xml', 'text-x-html'))
    reg('mime', 'mimetypes', 'application-octet-stream', pagina(VIOC, b_desc), ('unknown', 'application-x-generic', 'application-x-object', 'application-x-sharedlib'))


def _l(fn):
    g = L()
    fn(g)
    return g


# ---------------------------------------------------------------- escritura
def svg_de(im):
    filas = []
    px = im.load()
    for y in range(S):
        x = 0
        while x < S:
            c = px[x, y]
            if c[3] == 0:
                x += 1
                continue
            x0 = x
            while x < S and px[x, y] == c:
                x += 1
            op = '' if c[3] == 255 else f' fill-opacity="{c[3] / 255:.2f}"'
            filas.append(f'<rect x="{x0}" y="{y}" width="{x - x0}" height="1" fill="#{c[0]:02x}{c[1]:02x}{c[2]:02x}"{op}/>')
    return ('<svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 32 32" shape-rendering="crispEdges">'
            + ''.join(filas) + '</svg>\n')


CONTEXTOS = {'apps': 'Applications', 'places': 'Places', 'mimetypes': 'MimeTypes', 'status': 'Status', 'actions': 'Actions'}


def escribir():
    if OUT.exists():
        shutil.rmtree(OUT)
    todo = {n: (c, im) for n, (c, im) in ICONOS.items()}
    for a, c, n in ALIAS:
        if a not in todo:
            todo[a] = (c, ICONOS[n][1])
    for nombre, (ctx, im) in todo.items():
        for tam in (32, 64):
            d = OUT / f'{tam}x{tam}' / ctx
            d.mkdir(parents=True, exist_ok=True)
            (im if tam == 32 else im.resize((64, 64), Image.NEAREST)).save(d / f'{nombre}.png', optimize=True)
        d = OUT / 'scalable' / ctx
        d.mkdir(parents=True, exist_ok=True)
        (d / f'{nombre}.svg').write_text(svg_de(im))
    dirs = []
    for base in ('32x32', '64x64', 'scalable'):
        for ctx in CONTEXTOS:
            dirs.append(f'{base}/{ctx}')
    idx = ['[Icon Theme]', 'Name=NeonGrid', 'Comment=Iconos pixel art cyberpunk (rejilla de 32 px) para NeonGrid',
           'Inherits=breeze-dark,hicolor', 'DisplayDepth=32', 'Example=folder', 'Directories=' + ','.join(dirs), '']
    for d in dirs:
        base, ctx = d.split('/')
        idx.append(f'[{d}]')
        if base == 'scalable':
            idx += ['Size=32', 'MinSize=16', 'MaxSize=512', 'Type=Scalable']
        else:
            t = int(base.split('x')[0])
            idx += [f'Size={t}', 'Type=Fixed']
        idx += [f'Context={CONTEXTOS[ctx]}', '']
    (OUT / 'index.theme').write_text('\n'.join(idx))
    return len(todo)


# ---------------------------------------------------------------- hoja de contacto
def hoja():
    fuente = None
    for ruta in (os.path.expanduser('~/.local/share/fonts/pixelzen/DepartureMono-Regular.otf'),
                 str(RAIZ / 'paquete/neongrid/share/fonts/neongrid/DepartureMono-Regular.otf')):
        if os.path.exists(ruta):
            fuente = ImageFont.truetype(ruta, 11)
            break
    fuente = fuente or ImageFont.load_default()
    cols, cw, ch = 9, 110, 104
    grupos = {}
    for g, n in ORDEN:
        grupos.setdefault(g, []).append(n)
    # fila extra: carpetas a 32 px con texto (como en una lista de Dolphin)
    alto = 40
    for g, ns in grupos.items():
        alto += 26 + ((len(ns) + cols - 1) // cols) * ch
    alto += 260
    W = cols * cw + 20
    img = Image.new('RGB', (W, alto), FONDO)
    d = ImageDraw.Draw(img)
    y = 10
    for g, ns in grupos.items():
        d.text((12, y), g.upper(), font=fuente, fill=CY[:3])
        y += 22
        for i, n in enumerate(ns):
            x = 10 + (i % cols) * cw
            yy = y + (i // cols) * ch
            im = ICONOS[n][1].resize((64, 64), Image.NEAREST)
            img.paste(im, (x + (cw - 64) // 2, yy), im)
            t = n if len(n) <= 15 else n[:14] + '~'
            tw = d.textlength(t, font=fuente)
            d.text((x + (cw - tw) // 2, yy + 70), t, font=fuente, fill=TEN[:3])
        y += ((len(ns) + cols - 1) // cols) * ch + 4
    # escritorio / lista: carpetas con texto a 32 y 64 px sobre fondo claro-oscuro
    d.text((12, y), 'CARPETAS CON TEXTO (32 px reales, x1) Y ESCRITORIO (64 px)', font=fuente, fill=CY[:3])
    y += 22
    nombres = ['folder', 'folder-full', 'folder-documents', 'folder-download', 'folder-pictures', 'folder-music', 'folder-videos',
               'folder-development', 'user-home', 'user-trash', 'user-trash-full']
    paneles = [PAL['panel'], PAL['fondo'], (30, 36, 64)]
    for k, bg in enumerate(paneles):
        d.rectangle([10, y, W - 10, y + 40], fill=bg)
        x = 18
        for n in nombres[:8]:
            im = ICONOS[n][1]
            img.paste(im, (x, y + 4), im)
            d.text((x + 34, y + 14), n.replace('folder-', '').replace('folder', 'carpeta')[:6], font=fuente, fill=PAL['texto'])
            x += 120
        y += 46
    # fondo de escritorio: iconos grandes + etiquetas con sombra
    d.rectangle([10, y + 4, W - 10, y + 120], fill=mixc(PAL['violeta'], PAL['fondo'], .12)[:3])
    x = 30
    for n in nombres[:6] + nombres[9:]:
        im = ICONOS[n][1].resize((64, 64), Image.NEAREST)
        img.paste(im, (x, y + 12), im)
        t = n.replace('folder-', '').replace('user-', '')[:9]
        tw = d.textlength(t, font=fuente)
        d.text((x + 32 - tw / 2 + 1, y + 85), t, font=fuente, fill=(0, 0, 0))
        d.text((x + 32 - tw / 2, y + 84), t, font=fuente, fill=PAL['texto'])
        x += 110
    return img


def main():
    construir()
    n = escribir()
    img = hoja()
    img.save(AQUI / 'vista-previa.png')
    print('iconos unicos:', len(ICONOS), '| nombres totales (con alias):', n, '| hoja:', img.size)


if __name__ == '__main__':
    main()
