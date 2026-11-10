#!/usr/bin/env python3
"""Maqueta de ventanas NeonGrid: decoracion (activa/inactiva), terminal translucido, gestor de archivos y notificacion.
Solo dibuja una imagen para evaluar el estilo; no instala nada.
Uso: python maqueta.py [opacidad_terminal]   (por defecto 0.85)"""
import os, sys, math
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops
from paleta import PAL, contraste

HERE = os.path.dirname(os.path.abspath(__file__))
FONTS = os.path.join(HERE, 'fuentes', 'chakra-petch')
UI = lambda n, s=15: ImageFont.truetype(os.path.join(FONTS, f'ChakraPetch-{n}.ttf'), s)
MONO = ImageFont.truetype(os.path.expanduser('~/.local/share/fonts/pixelzen/DepartureMono-Regular.otf'), 15)
BG = os.path.join(HERE, '..', 'concepto', 'opus', 'propuesta-noche.png')
P = PAL
mix = lambda a, b, t: tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(3))
GLYPH = {
    'ok': ["......X", ".....XX", "X...XX.", "XX.XX..", ".XXX...", "..X...."],
    'up': ["...X...", "..XXX..", "..XXX..", ".XXXXX.", ".XXXXX.", "XXXXXXX"],
    'x': ["XX...XX", ".XX.XX.", "..XXX..", "..XXX..", ".XX.XX.", "XX...XX"],
}


def glyph(d, name, x, y, col, s=2):
    for j, row in enumerate(GLYPH[name]):
        for i, ch in enumerate(row):
            if ch == 'X': d.rectangle([x + i * s, y + j * s, x + i * s + s - 1, y + j * s + s - 1], fill=col)
    return 7 * s


def chamf(x0, y0, x1, y1, c=6):
    return [(x0 + c, y0), (x1 - c, y0), (x1, y0 + c), (x1, y1 - c), (x1 - c, y1), (x0 + c, y1), (x0, y1 - c), (x0, y0 + c)]


def halo(img, pts, col, k=1.0):
    """Halo de neon en 3 escalones (sin difuminado): 3 contornos engordados con alfa decreciente."""
    lay = Image.new('RGBA', img.size, (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    for rad, al in ((8, 26), (5, 48), (2, 90)):
        for a in range(16):
            dx = round(math.cos(a * math.pi / 8) * rad); dy = round(math.sin(a * math.pi / 8) * rad)
            d.polygon([(x + dx, y + dy) for x, y in pts], fill=col + (int(al * k),))
    img.alpha_composite(lay)


def window(img, x, y, w, h, title, active=True, opacity=1.0, blur=0, body=None):
    """Dibuja una ventana. body(img, x0, y0, x1, y1) pinta el contenido. Devuelve la imagen."""
    pts = chamf(x, y, x + w, y + h, 8)
    # sombra dura desplazada (2 px finales = 1 px logico)
    sh = Image.new('RGBA', img.size, (0, 0, 0, 0)); ImageDraw.Draw(sh).polygon([(px + 4, py + 4) for px, py in pts], fill=(0, 0, 0, 150)); img.alpha_composite(sh)
    if active: halo(img, pts, P['cian'], .9)
    # fondo translucido: el escritorio de detras, con desenfoque opcional (efecto "blur" de KWin)
    back = img.crop((x, y, x + w + 1, y + h + 1)).convert('RGB')
    if blur: back = back.filter(ImageFilter.GaussianBlur(blur))
    panel = P['fondo'] if active else P['panel']
    fill = Image.blend(back, Image.new('RGB', back.size, panel), opacity)
    mask = Image.new('L', (w + 1, h + 1), 0); ImageDraw.Draw(mask).polygon([(px - x, py - y) for px, py in pts], fill=255)
    img.paste(fill.convert('RGBA'), (x, y), mask)
    d = ImageDraw.Draw(img)
    # barra de titulo 28 px: tira ligeramente mas clara, lineas de escaneo ~5 %
    tb = Image.new('RGBA', (w + 1, 28), (0, 0, 0, 0)); td = ImageDraw.Draw(tb)
    base = mix(P['panel'], P['cian'], .10) if active else mix(P['panel'], P['violeta'], .06)
    td.rectangle([0, 0, w, 27], fill=base + (int(255 * max(.55, opacity)),))
    for yy in range(0, 28, 4): td.line([(0, yy), (w, yy)], fill=(0, 0, 0, 22))
    tmask = Image.new('L', (w + 1, 28), 0); ImageDraw.Draw(tmask).polygon([(px - x, py - y) for px, py in pts if py - y <= 40] + [(w, 28), (0, 28)], fill=255)
    img.paste(tb, (x, y), ImageChops.multiply(tb.split()[3], tmask)); d = ImageDraw.Draw(img)
    line = P['cian'] if active else mix(P['violeta'], P['fondo'], .45)
    d.line([(x, y + 28), (x + w, y + 28)], fill=mix(line, P['fondo'], .5))
    # titulo en la tipografia de interfaz y botones con forma propia: — □ ✕
    d.text((x + 16, y + 5), title, font=UI('SemiBold', 15), fill=P['texto'] if active else P['tenue'])
    bc = P['cian'] if active else P['tenue']
    bx = x + w - 30
    d.line([(bx - 4, y + 18), (bx + 4, y + 18)], fill=bc, width=2)                         # cerrar → x
    d.line([(bx - 4, y + 10), (bx + 4, y + 18)], fill=P['magenta_t'] if active else bc, width=2); d.line([(bx + 4, y + 10), (bx - 4, y + 18)], fill=P['magenta_t'] if active else bc, width=2)
    d.rectangle([bx - 38, y + 8, bx - 28, y + 18], outline=bc, width=2)                    # maximizar
    d.line([(bx - 70, y + 17), (bx - 60, y + 17)], fill=bc, width=2)                       # minimizar
    # borde de 2 px y "corchetes" en las esquinas
    d.line(pts + [pts[0]], fill=line, width=2)
    for (cx, cy, sx, sy) in ((x, y, 1, 1), (x + w, y, -1, 1), (x, y + h, 1, -1), (x + w, y + h, -1, -1)):
        d.line([(cx + sx * 14, cy), (cx + sx * 4, cy)], fill=mix(line, (255, 255, 255), .55 if active else .1), width=2)
        d.line([(cx, cy + sy * 14), (cx, cy + sy * 4)], fill=mix(line, (255, 255, 255), .55 if active else .1), width=2)
    if body: body(img, x + 2, y + 30, x + w - 2, y + h - 2)
    return img


# ---------------- contenidos ----------------
def terminal_body(img, x0, y0, x1, y1):
    d = ImageDraw.Draw(img); d.fontmode = "1"; X = x0 + 14; Y = y0 + 10; LH = 22; cw = MONO.getlength('M')
    def t(x, y, s, c): d.text((x, y), s, font=MONO, fill=c); return x + MONO.getlength(s)
    def prompt(y, cmd=''):
        x = t(X, y, 'λ ', P['verde']); x = t(x, y, '~/Proyectos/neongrid ', P['cian']); x = t(x, y, 'main ', P['magenta_t'])
        if cmd: t(x, y, cmd, P['texto'])
    prompt(Y, 'neongrid --estado'); Y += LH
    x = t(X, Y, ' CPU ', P['tenue']);
    for i in range(8): d.rectangle([x + i * 12, Y + 3, x + i * 12 + 8, Y + 13], fill=P['cian'] if i < 4 else mix(P['panel'], P['cian'], .25))
    t(x + 104, Y, '47%', P['texto']); t(x + 160, Y, 'GPU 41%  58°C', P['texto']); Y += LH
    x = t(X, Y, ' RAM ', P['tenue']); t(x, Y, '10.2/16 GB', P['texto']); x2 = x + 190; x2 += glyph(d, 'ok', x2, Y + 3, P['verde']) + 6; x2 = t(x2, Y, 'VPN activa', P['verde'])
    x2 += 20; x2 += glyph(d, 'ok', x2, Y + 3, P['verde']) + 6; t(x2, Y, 'SYNC', P['verde']); Y += LH
    x = X + 5 + glyph(d, 'up', X + 5, Y + 3, P['ambar']) + 6; t(x, Y, '12 actualizaciones', P['ambar']); x2 = x + 230
    x2 += glyph(d, 'x', x2, Y + 3, P['rojo_t']) + 6; t(x2, Y, '1 servicio caido', P['rojo_t']); Y += LH * 2 - 6
    prompt(Y, 'ls'); Y += LH
    x = X
    for n, c in (('concepto/', P['cian']), ('tema/', P['cian']), ('DISEÑO.md', P['texto']), ('PROMPT.md', P['texto']), ('generar.py', P['verde'])):
        x = t(x, Y, n + '  ', c)
    Y += LH * 2 - 6
    prompt(Y, 'git status -sb'); Y += LH
    t(X, Y, '## main...origin/main [adelantado 1]', P['tenue']); Y += LH
    t(X, Y, ' M', P['ambar']); t(X + 3 * cw, Y, 'tema/paleta.py', P['texto']); Y += LH
    t(X, Y, '??', P['rojo_t']); t(X + 3 * cw, Y, 'tema/maqueta.py', P['texto']); Y += LH * 2 - 6
    prompt(Y); d.rectangle([X + cw * 40, Y + 1, X + cw * 40 + 9, Y + 17], fill=P['verde'])  # cursor bloque


def fm_body(img, x0, y0, x1, y1):
    d = ImageDraw.Draw(img); f = UI('Medium', 14); fs = UI('Regular', 13)
    d.rectangle([x0, y0, x0 + 170, y1], fill=P['panel'])
    d.line([(x0 + 170, y0), (x0 + 170, y1)], fill=mix(P['violeta'], P['fondo'], .5))
    d.text((x0 + 14, y0 + 12), 'LUGARES', font=fs, fill=P['tenue'])
    for i, (n, sel) in enumerate((('Inicio', 0), ('Proyectos', 1), ('Documentos', 0), ('Descargas', 0), ('Imágenes', 0), ('Papelera', 0))):
        yy = y0 + 40 + i * 34
        if sel: d.polygon(chamf(x0 + 6, yy - 4, x0 + 164, yy + 26, 4), fill=P['sel'], outline=P['cian'])
        d.rectangle([x0 + 16, yy + 6, x0 + 26, yy + 16], outline=P['cian'] if sel else P['violeta'], width=2)
        d.text((x0 + 38, yy), n, font=f, fill=P['texto'] if sel else P['tenue'])
    # ruta y rejilla de carpetas
    d.text((x0 + 190, y0 + 12), 'Proyectos  /  neongrid', font=f, fill=P['cian'])
    d.line([(x0 + 180, y0 + 40), (x1 - 8, y0 + 40)], fill=mix(P['violeta'], P['fondo'], .5))
    names = ['concepto', 'tema', 'frames', 'fuentes', 'colores', 'maqueta']
    for n, nm in enumerate(names):
        c, r = divmod(n, 3); fx = x0 + 200 + c * 150; fy = y0 + 60 + r * 118
        if n == 1: d.polygon(chamf(fx - 14, fy - 8, fx + 94, fy + 92, 6), fill=P['sel'], outline=P['cian'])
        d.polygon([(fx, fy + 6), (fx + 24, fy + 6), (fx + 30, fy + 12), (fx + 38, fy + 12), (fx + 38, fy + 18), (fx, fy + 18)], fill=(120, 84, 200))
        d.polygon([(fx, fy + 16), (fx + 76, fy + 16), (fx + 76, fy + 62), (fx, fy + 62)], fill=(84, 56, 150))
        d.rectangle([fx, fy + 16, fx + 76, fy + 18], fill=(170, 130, 255)); d.rectangle([fx, fy + 56, fx + 76, fy + 62], fill=(52, 34, 98))
        d.rectangle([fx + 3, fy + 21, fx + 73, fy + 59], outline=(110, 76, 190))
        w = d.textlength(nm, font=fs); d.text((fx + 38 - w / 2, fy + 70), nm, font=fs, fill=P['texto'] if n == 1 else P['tenue'])


def notificacion(img, x, y, w, h):
    pts = chamf(x, y, x + w, y + h, 8)
    sh = Image.new('RGBA', img.size, (0, 0, 0, 0)); ImageDraw.Draw(sh).polygon([(px + 4, py + 4) for px, py in pts], fill=(0, 0, 0, 150)); img.alpha_composite(sh)
    halo(img, pts, P['ambar'], .7)
    d = ImageDraw.Draw(img); d.polygon(pts, fill=P['fondo'], outline=P['ambar'])
    d.rectangle([x + 2, y + 10, x + 10, y + h - 10], fill=P['ambar'])        # franja lateral por gravedad
    glyph(d, 'up', x + 26, y + 22, P['ambar'], 3)
    d.text((x + 62, y + 14), 'Actualizaciones pendientes', font=UI('SemiBold', 16), fill=P['texto'])
    d.text((x + 62, y + 42), '12 paquetes · 1 servicio caído', font=UI('Regular', 14), fill=P['tenue'])
    d.text((x + w - 70, y + 14), 'ahora', font=UI('Regular', 12), fill=P['tenue'])


def main():
    op = float(sys.argv[1]) if len(sys.argv) > 1 else 0.85
    img = Image.open(BG).convert('RGBA')
    window(img, 1120, 520, 700, 470, 'Dolphin — Proyectos', active=False, opacity=.97, body=fm_body)
    window(img, 520, 330, 800, 470, 'Konsole — neongrid', active=True, opacity=op, blur=5, body=terminal_body)
    notificacion(img, 1440, 64, 420, 92)
    img.convert('RGB').save(os.path.join(HERE, 'maqueta', 'ventanas.png'))
    # comparativa de opacidad del terminal sobre la zona mas cargada de la ciudad
    base = Image.open(BG).convert('RGBA').crop((500, 180, 1700, 780))
    strip = Image.new('RGBA', (1920, 700), (6, 7, 16, 255)); lab = ImageDraw.Draw(strip)
    for i, o in enumerate((1.0, .85, .70)):
        panel = base.crop((0, 0, 600, 600)) if False else Image.open(BG).convert('RGBA').crop((560 + i * 80, 340, 1160 + i * 80, 940))
        panel2 = Image.new('RGBA', (640, 600), (0, 0, 0, 255)); panel2.paste(panel, (20, 0))
        window(panel2, 30, 90, 580, 330, f'Konsole — opacidad {int(o * 100)} %', active=True, opacity=o, blur=5 if o < 1 else 0,
               body=lambda im, a, b, c, dd: terminal_body(im, a, b, c, dd))
        strip.paste(panel2.convert('RGB'), (i * 640, 40))
        lab.text((i * 640 + 24, 8), f'{int(o * 100)} %' + ('  (opaco)' if o == 1 else '  (con desenfoque de KWin)'), font=UI('SemiBold', 18), fill=P['cian'])
    strip.convert('RGB').save(os.path.join(HERE, 'maqueta', 'opacidades.png'))
    print('ok')


if __name__ == '__main__':
    main()
