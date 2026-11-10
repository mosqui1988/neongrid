#!/usr/bin/env python3
"""Utilidades comunes (solo stdlib) para generar SVG de pixeles de NeonGrid.
Un "lienzo" es una lista de filas; cada celda es None (transparente) o (hex, alfa).
Todo se emite como rectangulos alineados a la rejilla, con shape-rendering=crispEdges."""
import os, sys

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(AQUI, '..'))
from paleta import PAL  # noqa: E402

P = PAL


def hx(rgb):
    return '#%02x%02x%02x' % tuple(int(round(v)) for v in rgb)


def mix(a, b, t):
    """Mezcla de dos tuplas RGB (t=0 -> a, t=1 -> b)."""
    return tuple(a[i] + (b[i] - a[i]) * t for i in range(3))


def lienzo(w, h):
    return [[None] * w for _ in range(h)]


def rect(c, x, y, w, h, col, a=1.0):
    for j in range(y, y + h):
        for i in range(x, x + w):
            if 0 <= j < len(c) and 0 <= i < len(c[0]):
                c[j][i] = (hx(col) if not isinstance(col, str) else col, a)


def mascara(c, filas, x0, y0, col, a=1.0, u=1):
    """Pinta una mascara de texto ('X' = pixel) con celdas de u x u."""
    for j, fila in enumerate(filas):
        for i, ch in enumerate(fila):
            if ch not in '. ':
                rect(c, x0 + i * u, y0 + j * u, u, u, col, a)


def rects_svg(c, dx=0, dy=0):
    """Une tramos horizontales iguales y los apila en vertical si se repiten."""
    h = len(c)
    w = len(c[0]) if h else 0
    abiertos = {}   # (x, w, color, alfa) -> y inicial
    salida = []
    for y in range(h + 1):
        fila = {}
        if y < h:
            x = 0
            while x < w:
                v = c[y][x]
                if v is None:
                    x += 1
                    continue
                x2 = x
                while x2 < w and c[y][x2] == v:
                    x2 += 1
                fila[(x, x2 - x, v[0], v[1])] = 1
                x = x2
        for k in list(abiertos):
            if k not in fila:
                x, ww, col, a = k
                y0 = abiertos.pop(k)
                salida.append(f'<rect x="{x + dx}" y="{y0 + dy}" width="{ww}" height="{y - y0}" fill="{col}"'
                              + ('' if a >= 0.999 else f' fill-opacity="{a:.3g}"') + '/>')
        for k in fila:
            abiertos.setdefault(k, y)
    return salida


def grupo(id_, c, y0=0, x0=0, caja=True):
    """<g id> con una caja transparente del tamano del lienzo (define el bbox del elemento)."""
    h, w = len(c), len(c[0])
    s = [f'<g id="{id_}" transform="translate({x0},{y0})">']
    if caja:
        s.append(f'<rect width="{w}" height="{h}" fill="#000" fill-opacity="0"/>')
    s += rects_svg(c)
    s.append('</g>')
    return '\n'.join(s)


def svg(ancho, alto, cuerpo, extra=''):
    return (f'<?xml version="1.0" encoding="UTF-8"?>\n<svg xmlns="http://www.w3.org/2000/svg" width="{ancho}" '
            f'height="{alto}" viewBox="0 0 {ancho} {alto}" shape-rendering="crispEdges">\n{extra}{cuerpo}\n</svg>\n')


def apilar(grupos, ancho, sep=1):
    """grupos: lista de (id, lienzo). Devuelve (svg, {id: y0})."""
    y, partes, pos = 0, [], {}
    for id_, c in grupos:
        partes.append(grupo(id_, c, y))
        pos[id_] = y
        y += len(c) + sep
    return svg(ancho, max(1, y - sep), '\n'.join(partes)), pos


def anillo(x, y, w, h, c):
    """Profundidad (0 = borde exterior) del pixel (x,y) en un rectangulo w x h con esquinas
    biseladas a 45 grados de tamano c. None = fuera (transparente)."""
    dx, dy = min(x, w - 1 - x), min(y, h - 1 - y)
    r = min(dx, dy)
    if c and dx < c and dy < c:
        s = dx + dy - (c - 1)
        if s < 0:
            return None
        r = min(r, int(s * 0.7071))
    return r


def marco9(m, medio, fn):
    """Corta en 9 trozos un marco virtual. m=(izq,arr,der,aba) margenes; medio=(ancho,alto) del centro;
    fn(x,y,W,H) -> (hex,alfa) | None. Devuelve {nombre: lienzo}."""
    l, t, r, b = m
    mw, mh = medio
    W, H = l + mw + r, t + mh + b
    full = [[fn(x, y, W, H) for x in range(W)] for y in range(H)]
    xs = {'left': (0, l), 'mid': (l, l + mw), 'right': (l + mw, W)}
    ys = {'top': (0, t), 'mid': (t, t + mh), 'bottom': (t + mh, H)}

    def corte(cx, cy):
        (x0, x1), (y0, y1) = xs[cx], ys[cy]
        return [row[x0:x1] for row in full[y0:y1]]
    out = {}
    for ny, cy in (('top', 'top'), ('', 'mid'), ('bottom', 'bottom')):
        for nx, cx in (('left', 'left'), ('', 'mid'), ('right', 'right')):
            nombre = (ny + nx) or 'center'
            if (cy != 'mid' and ys[cy][1] - ys[cy][0] == 0) or (cx != 'mid' and xs[cx][1] - xs[cx][0] == 0):
                continue
            out[nombre] = corte(cx, cy)
    return out


def pistas(pre, m, ancho):
    """Elementos hint-*-margin (rectangulos de 1 px; su dimension fija el margen)."""
    l, t, r, b = m
    out = []
    for n, (w, h) in (('top', (1, t)), ('bottom', (1, b)), ('left', (l, 1)), ('right', (r, 1))):
        if w and h:
            out.append((f'{pre}hint-{n}-margin', [[('#ff00ff', 0.0)] * w for _ in range(h)]))
    return out


def con_prefijo(pre, trozos):
    return [(pre + n, c) for n, c in trozos.items()]
