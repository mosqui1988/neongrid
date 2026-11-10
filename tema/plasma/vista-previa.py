#!/usr/bin/env python3
"""Captura estatica del tema de Plasma NeonGrid: renderiza los SVG reales (rsvg-convert --export-id) y los monta
con el troceado en 9 de FrameSvg. Necesita Pillow. Uso: python3 vista-previa.py"""
import io, os, subprocess, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'aurorae'))
from PIL import Image, ImageDraw, ImageFont
from pixelsvg import P, mix as _mix
mix = lambda a, b, t: tuple(int(v) for v in _mix(a, b, t))

QUI = os.path.dirname(os.path.abspath(__file__))
TEMA = os.path.join(QUI, '..', '..', 'paquete', 'neongrid', 'share', 'plasma', 'desktoptheme', 'NeonGrid')
FUENTES = os.path.join(QUI, '..', 'tipografias', 'chakra-petch')
MONO = os.path.expanduser('~/.local/share/fonts/pixelzen/DepartureMono-Regular.otf')
UI = lambda n, s=13: ImageFont.truetype(os.path.join(FUENTES, f'ChakraPetch-{n}.ttf'), s)
cache = {}


def elem(fichero, id_, w=None, h=None):
    k = (fichero, id_, w, h)
    if k not in cache:
        cmd = ['rsvg-convert', '-i', id_]
        if w: cmd += ['-w', str(w), '-h', str(h)]
        out = subprocess.run(cmd + [os.path.join(TEMA, fichero)], capture_output=True, check=True).stdout
        cache[k] = Image.open(io.BytesIO(out)).convert('RGBA')
    return cache[k]


def tiled(im, dst, x, y, w, h, tile=True):
    p = dst
    if not tile:
        dst.alpha_composite(im.resize((w, h), Image.NEAREST), (x, y)); return
    for yy in range(y, y + h, im.height):
        for xx in range(x, x + w, im.width):
            t = im.crop((0, 0, min(im.width, x + w - xx), min(im.height, y + h - yy)))
            dst.alpha_composite(t, (xx, yy))


def marco(dst, fichero, pre, x, y, w, h, tile=True, bordes='tblr'):
    """Troceado en 9 de FrameSvg. `bordes` = bordes activados (en una barra superior solo 'b')."""
    g = lambda n: elem(fichero, pre + n)
    c = g('center')
    tl = g('topleft') if 'tl' in bordes or ('t' in bordes and 'l' in bordes) else None
    l = r = t = b = 0
    if 't' in bordes: t = g('top').height
    if 'b' in bordes: b = g('bottom').height
    if 'l' in bordes: l = g('left').width
    if 'r' in bordes: r = g('right').width
    tiled(c, dst, x + l, y + t, w - l - r, h - t - b, tile)
    if t: tiled(g('top'), dst, x + l, y, w - l - r, t)
    if b: tiled(g('bottom'), dst, x + l, y + h - b, w - l - r, b)
    if l: tiled(g('left'), dst, x, y + t, l, h - t - b)
    if r: tiled(g('right'), dst, x + w - r, y + t, r, h - t - b)
    if t and l: dst.alpha_composite(g('topleft'), (x, y))
    if t and r: dst.alpha_composite(g('topright'), (x + w - r, y))
    if b and l: dst.alpha_composite(g('bottomleft'), (x, y + h - b))
    if b and r: dst.alpha_composite(g('bottomright'), (x + w - r, y + h - b))


def escena(w, h):
    bg = Image.new('RGBA', (w, h), (8, 10, 22, 255)); d = ImageDraw.Draw(bg)
    for i in range(0, w, 24):
        d.rectangle([i, h - 60 - (i * 37 % 90), i + 18, h], fill=(14, 18, 38, 255))
    for i in range(0, w, 24):
        for j in range(h - 150, h, 12):
            if (i * 7 + j * 3) % 5 == 0: d.rectangle([i + 4, j, i + 7, j + 3], fill=(255, 176, 32, 255) if (i + j) % 3 else (0, 229, 255, 255))
    d.rectangle([w // 2 - 20, 40, w // 2 + 70, h], fill=(110, 16, 96, 255))
    return bg


def texto(d, xy, s, f, col, anc='l'):
    x, y = xy
    if anc == 'm': x -= d.textlength(s, font=f) / 2
    d.text((x, y), s, font=f, fill=col)


def main():
    W, H = 960, 560
    im = escena(W, H); d = ImageDraw.Draw(im)
    # ---- barra superior (solo borde inferior activo)
    marco(im, 'widgets/panel-background.svg', '', 0, 0, W, 32, True, 'b')
    nu = elem('icons/nucleo-22.svg', 'nucleo'); im.alpha_composite(nu, (8, 5))
    x = 44
    d.line([(x - 6, 8), (x - 6, 22)], fill=mix(P['violeta'], P['fondo'], .4))
    for i in range(4):
        pr = 'active-center' if i == 1 else ('hover-center' if i == 3 else 'normal-center')
        im.alpha_composite(elem('widgets/pager.svg', pr, 18, 18), (x + i * 24, 7))
    x += 4 * 24 + 6
    d.line([(x - 6, 8), (x - 6, 22)], fill=mix(P['violeta'], P['fondo'], .4))
    cols = [(0, 229, 255), (192, 172, 255), (255, 124, 233), (57, 255, 136), (255, 176, 32)]
    for i, (est, col) in enumerate((('focus', cols[0]), ('normal', cols[1]), ('attention', cols[2]), ('minimized', cols[3]), ('hover', cols[4]))):
        xx = x + i * 34
        marco(im, 'widgets/tasks.svg', f'north-{est}-', xx, 0, 32, 32, True, 'tblr')
        d.rectangle([xx + 6, 7, xx + 25, 24], outline=col, width=2)
        d.rectangle([xx + 10, 11, xx + 21, 20], fill=mix(col, P['fondo'], .55))
    f = ImageFont.truetype(MONO, 14)
    texto(d, (W // 2, 8), '21:37  ·  MAR 10 NOV', f, P['texto'], 'm')
    # bandeja: escudo VPN, sync, volumen, red, bateria (rallitas), apagado
    xb = W - 210
    d.polygon([(xb, 9), (xb + 14, 9), (xb + 14, 17), (xb + 7, 24), (xb, 17)], fill=P['verde'])
    d.arc([xb + 24, 8, xb + 38, 22], 40, 300, fill=P['cian'], width=2); d.polygon([(xb + 36, 6), (xb + 42, 12), (xb + 33, 12)], fill=P['cian'])
    d.polygon([(xb + 50, 13), (xb + 54, 13), (xb + 60, 8), (xb + 60, 24), (xb + 54, 19), (xb + 50, 19)], fill=P['cian'])
    d.arc([xb + 62, 11, xb + 70, 19], -50, 50, fill=P['cian'], width=2)
    for k in range(4): d.rectangle([xb + 82 + k * 4, 22 - k * 4, xb + 84 + k * 4, 24], fill=P['cian'])
    d.text((xb + 98, 8), '78%', font=UI('Medium', 13), fill=P['texto'])
    im.alpha_composite(elem('icons/battery.svg', '22-22-Fill80', 22, 22).copy(), (xb + 134, 5))
    im.alpha_composite(elem('icons/battery.svg', '22-22-Battery', 22, 22), (xb + 134, 5))
    d.ellipse([xb + 166, 9, xb + 180, 23], outline=P['magenta'], width=2); d.line([(xb + 173, 6), (xb + 173, 14)], fill=P['magenta'], width=2)
    # ---- popup (dialogs/background) con contenido
    px, py, pw, ph = 40, 70, 360, 250
    marco(im, 'dialogs/background.svg', '', px, py, pw, ph, True)
    d = ImageDraw.Draw(im)
    texto(d, (px + 22, py + 18), 'Red  ·  ajustes de ejemplo', UI('SemiBold', 16), P['texto'])
    # lista con seleccion
    for i, (nom, st) in enumerate((('Elemento normal', 'normal'), ('Elemento con el cursor encima', 'hover'), ('Elemento seleccionado', 'selected'))):
        yy = py + 52 + i * 32
        marco(im, 'widgets/viewitem.svg', f'{st}-', px + 16, yy, pw - 32, 28, True)
        d = ImageDraw.Draw(im); texto(d, (px + 28, yy + 5), nom, UI('Medium', 14), P['texto'])
    # campo de texto, botones
    marco(im, 'widgets/lineedit.svg', 'focus-', px + 16, py + 156, 190, 30, True)
    d = ImageDraw.Draw(im); texto(d, (px + 26, py + 162), '> buscar', UI('Regular', 14), P['texto'])
    for i, st in enumerate(('normal', 'hover', 'pressed')):
        marco(im, 'widgets/button.svg', f'{st}-', px + 16 + i * 74, py + 198, 68, 30, True)
        d = ImageDraw.Draw(im); texto(d, (px + 50 + i * 74, py + 204), ('Vale', 'Hover', 'Pulsa')[i], UI('Medium', 13), P['texto'], 'm')
    # slider + progreso
    sx, sy = px + 250, py + 164
    marco(im, 'widgets/slider.svg', 'groove-', sx, sy + 5, 100, 6, True)
    marco(im, 'widgets/slider.svg', 'groove-highlight-', sx, sy + 5, 58, 6, True)
    im.alpha_composite(elem('widgets/slider.svg', 'horizontal-slider-handle'), (sx + 52, sy))
    marco(im, 'widgets/bar_meter_horizontal.svg', 'bar-inactive-', sx, sy + 40, 100, 10, True)
    marco(im, 'widgets/bar_meter_horizontal.svg', 'bar-active-', sx, sy + 40, 64, 10, True)
    # ---- tooltip
    tx, ty = 440, 70
    marco(im, 'widgets/tooltip.svg', '', tx, ty, 230, 58, True)
    d = ImageDraw.Draw(im); texto(d, (tx + 14, ty + 8), 'Konsole', UI('SemiBold', 14), P['texto']); texto(d, (tx + 14, ty + 30), 'neongrid  ·  1 ventana', UI('Regular', 12), P['tenue'])
    # pestanas + scrollbar
    for i, (nom, act) in enumerate((('General', 1), ('Red', 0), ('Audio', 0))):
        if act: marco(im, 'widgets/tabbar.svg', 'north-active-tab-', tx + i * 78, ty + 150, 74, 30, True)
        d = ImageDraw.Draw(im); texto(d, (tx + 37 + i * 78, ty + 156), nom, UI('Medium', 13), P['texto'] if act else P['tenue'], 'm')
    marco(im, 'widgets/scrollbar.svg', 'background-vertical-', tx + 250, ty + 4, 12, 170, True)
    marco(im, 'widgets/scrollbar.svg', 'slider-', tx + 250, ty + 30, 12, 60, True)
    marco(im, 'widgets/scrollbar.svg', 'mouseover-slider-', tx + 280, ty + 30, 12, 60, True)
    # leyenda
    d = ImageDraw.Draw(im)
    texto(d, (440, 270), 'tareas (de izq. a der.): foco = subrayado cian + relleno, normal = sin marco,', UI('Regular', 12), P['tenue'])
    texto(d, (440, 288), 'atencion = magenta discontinuo, minimizada = punteado violeta, hover = relleno claro', UI('Regular', 12), P['tenue'])
    out = im.resize((W * 2, H * 2), Image.NEAREST).convert('RGB')
    out.save(os.path.join(QUI, 'vista-previa.png'))
    # acercamiento x4 de la barra
    print('ok', out.size)


if __name__ == '__main__':
    main()
