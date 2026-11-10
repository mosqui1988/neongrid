#!/usr/bin/env python3
"""Captura estatica de la decoracion Aurorae: renderiza los SVG reales con rsvg-convert y monta ventanas
con el mismo troceado en 9 que usa Aurorae. Necesita Pillow (solo herramienta de construccion).
Uso: python3 vista-previa.py"""
import io, json, os, subprocess, sys
from PIL import Image, ImageDraw, ImageFont
from pixelsvg import P, AQUI, mix

TEMA = os.path.join(AQUI, '..', '..', 'paquete', 'neongrid', 'share', 'aurorae', 'themes', 'NeonGrid')
FUENTES = os.path.join(AQUI, '..', 'tipografias', 'chakra-petch')
pos = json.load(open(os.path.join(AQUI, '_layout.json')))


def render(svg, esc=1):
    out = subprocess.run(['rsvg-convert', '-z', str(esc), svg], capture_output=True, check=True).stdout
    return Image.open(io.BytesIO(out)).convert('RGBA')


deco = render(os.path.join(TEMA, 'decoration.svg'))
H = {'top': 28, 'left': 4}


def pieza(pref, n):
    # alto de cada pieza segun el generador: top* = 28, bottom* = 4, resto = 4
    w = 4 if n in ('topleft', 'topright', 'left', 'right', 'bottomleft', 'bottomright', 'center', 'top', 'bottom') else 4
    h = 28 if n.startswith('top') else 4
    y = pos[pref + n]
    return deco.crop((0, y, w, y + h))


def ventana(w, h, activo, titulo, fondo_cliente):
    pref = 'decoration-' if activo else 'decoration-inactive-'
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0))

    def pega(n, x, y, ww, hh):
        p = pieza(pref, n)
        for yy in range(y, y + hh, p.height):
            for xx in range(x, x + ww, p.width):
                im.alpha_composite(p, (xx, yy))
    pega('topleft', 0, 0, 4, 28); pega('top', 4, 0, w - 8, 28); pega('topright', w - 4, 0, 4, 28)
    pega('left', 0, 28, 4, h - 32); pega('center', 4, 28, w - 8, h - 32); pega('right', w - 4, 28, 4, h - 32)
    pega('bottomleft', 0, h - 4, 4, 4); pega('bottom', 4, h - 4, w - 8, 4); pega('bottomright', w - 4, h - 4, 4, 4)
    d = ImageDraw.Draw(im)
    d.rectangle([4, 28, w - 5, h - 5], fill=fondo_cliente)           # el cliente lo pinta la aplicacion
    f = ImageFont.truetype(os.path.join(FUENTES, 'ChakraPetch-SemiBold.ttf'), 15)
    d.text((4 + 8, 2 + 3), titulo, font=f, fill=P['texto'] if activo else P['tenue'])
    # botones: minimizar, maximizar, cerrar (de derecha a izquierda, ancho 20, hueco 4, margen 8)
    sufijo = 'active' if activo else 'inactive'
    x = w - 4 - 8 - 20
    for n in ('close', 'maximize', 'minimize'):
        b = render(os.path.join(TEMA, n + '.svg'))
        # cada estado mide 20 de alto, en orden active, hover, pressed, inactive...
        idx = ['active', 'hover', 'pressed', 'inactive', 'deactivated', 'hover-inactive', 'pressed-inactive'].index(sufijo)
        im.alpha_composite(b.crop((0, idx * 20, 20, idx * 20 + 20)), (x, 2 + 2))
        x -= 24
    return im


def fondo(w, h):
    bg = Image.new('RGBA', (w, h), (6, 8, 18, 255)); d = ImageDraw.Draw(bg)
    for i in range(0, w, 16): d.line([(i, 0), (i, h)], fill=(18, 24, 48, 255))
    for j in range(0, h, 16): d.line([(0, j), (w, j)], fill=(18, 24, 48, 255))
    d.rectangle([w // 2 - 30, 0, w // 2 + 150, h], fill=(150, 20, 120, 255))      # franja magenta para ver la translucidez
    return bg


def main():
    ESC = 3
    bg = fondo(640, 340)
    a = ventana(360, 220, True, 'Konsole  -  neongrid', P['fondo']); bg.alpha_composite(a, (20, 20))
    i = ventana(300, 190, False, 'Dolphin  -  Proyectos', P['panel']); bg.alpha_composite(i, (300, 120))
    # hoja de botones (x4 vertical) para el segundo panel
    names = ['close', 'maximize', 'restore', 'minimize', 'keepabove', 'keepbelow', 'alldesktops', 'shade', 'help']
    est = ['active', 'hover', 'pressed', 'inactive', 'deactivated', 'hover-inactive']
    hoja = Image.new('RGBA', (len(names) * 24 + 4, len(est) * 24 + 4), P['fondo'] + (255,))
    for c, n in enumerate(names):
        b = render(os.path.join(TEMA, n + '.svg'))
        for r in range(len(est)):
            hoja.alpha_composite(b.crop((0, r * 20, 20, r * 20 + 20)), (4 + c * 24, 4 + r * 24))
    big = bg.resize((bg.width * 2, bg.height * 2), Image.NEAREST)
    hb = hoja.resize((hoja.width * 3, hoja.height * 3), Image.NEAREST)
    out = Image.new('RGBA', (big.width, big.height + hb.height + 30), P['fondo'] + (255,))
    out.paste(big, (0, 0)); out.paste(hb, (0, big.height + 20))
    d = ImageDraw.Draw(out); f = ImageFont.truetype(os.path.join(FUENTES, 'ChakraPetch-Medium.ttf'), 13)
    d.text((6, big.height + 3), 'botones (columnas) x estados: activo, hover, pulsado, inactiva, desactivado, hover-inactiva', font=f, fill=P['tenue'])
    out.convert('RGB').save(os.path.join(AQUI, 'vista-previa.png'))
    print('vista-previa.png', out.size)


if __name__ == '__main__':
    main()
