#!/usr/bin/env python3
"""NeonGrid - lector/validador independiente de ficheros Xcursor + hoja de vista previa.
Uso: python3 verificar.py [carpeta_tema]   (por defecto paquete/neongrid/share/icons/NeonGrid-cursors)
Valida: magica 'Xcur', cabecera de 16 bytes, version, tabla de contenidos, cada chunk (cabecera 36, tipo, subtipo
= tamano nominal, anchura/altura, hotspot dentro de la imagen, pixeles completos) y que cada enlace resuelva."""
import struct
import sys
from pathlib import Path

from PIL import Image, ImageDraw

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[1]
TEMA = Path(sys.argv[1]) if len(sys.argv) > 1 else RAIZ / 'paquete/neongrid/share/icons/NeonGrid-cursors'


def leer(ruta):
    b = Path(ruta).read_bytes()
    assert b[:4] == b'Xcur', 'magica incorrecta'
    cab, ver, n = struct.unpack_from('<III', b, 4)
    assert cab == 16, 'cabecera != 16'
    assert ver == 0x10000, 'version inesperada'
    assert len(b) >= 16 + 12 * n
    imgs = []
    for i in range(n):
        tipo, sub, pos = struct.unpack_from('<III', b, 16 + 12 * i)
        assert tipo == 0xfffd0002, 'tipo de chunk no soportado'
        hdr, t2, s2, v, w, h, xh, yh, dl = struct.unpack_from('<IIIIIIIII', b, pos)
        assert hdr == 36 and t2 == tipo and s2 == sub and v == 1, 'cabecera de chunk invalida'
        assert 0 < w <= 0x7fff and 0 < h <= 0x7fff and xh < w and yh < h, 'dimensiones/hotspot invalidos'
        assert pos + 36 + 4 * w * h <= len(b), 'pixeles truncados'
        px = struct.unpack_from('<%dI' % (w * h), b, pos + 36)
        im = Image.new('RGBA', (w, h))
        datos = []
        for p in px:
            a = p >> 24
            if a == 0:
                datos.append((0, 0, 0, 0))
            else:
                datos.append((min(255, ((p >> 16) & 255) * 255 // a), min(255, ((p >> 8) & 255) * 255 // a), min(255, (p & 255) * 255 // a), a))
        im.putdata(datos)
        imgs.append((sub, im, (xh, yh), dl))
    assert pos + 36 + 4 * w * h == len(b), 'bytes sobrantes'
    return imgs


def main():
    cur = TEMA / 'cursors'
    reales = sorted(p for p in cur.iterdir() if not p.is_symlink())
    enlaces = sorted(p for p in cur.iterdir() if p.is_symlink())
    for e in enlaces:
        assert e.resolve().exists() and e.resolve().parent == cur.resolve(), f'enlace roto: {e.name}'
    todo = {}
    for p in reales:
        im = leer(p)
        tam = sorted({s for s, *_ in im})
        todo[p.name] = im
        print(f'OK {p.name:14} tamanos {tam}  cuadros {len(im)}')
    print(f'ficheros Xcursor validos: {len(reales)} | enlaces simbolicos validos: {len(enlaces)} | index.theme: {(TEMA / "index.theme").exists()}')
    # --- vista previa
    nombres = list(todo)
    ancho = 8
    cel = 150
    filas = (len(nombres) + ancho - 1) // ancho
    img = Image.new('RGB', (ancho * cel, filas * 2 * 100 + 140), (11, 14, 26))
    d = ImageDraw.Draw(img)
    for i, nom in enumerate(nombres):
        x0 = (i % ancho) * cel + 10
        y0 = (i // ancho) * 200 + 6
        d.rectangle([x0 - 4, y0, x0 + cel - 12, y0 + 92], fill=(11, 14, 26))
        d.rectangle([x0 - 4, y0 + 96, x0 + cel - 12, y0 + 188], fill=(214, 224, 238))
        frs = [c for c in todo[nom] if c[0] == 48]
        sel = frs[0]
        for (yy, bg) in ((y0 + 4, None), (y0 + 100, None)):
            w, h = sel[1].size
            img.paste(sel[1], (x0 + 4, yy), sel[1])
            hx, hy = sel[2]
            d.rectangle([x0 + 4 + hx - 1, yy + hy - 1, x0 + 4 + hx + 1, yy + hy + 1], outline=(255, 255, 0))
            # tamano 24 al lado
            s24 = [c for c in todo[nom] if c[0] == 24][0]
            img.paste(s24[1], (x0 + 70, yy), s24[1])
        d.text((x0, y0 + 74), nom + (f' x{len(frs)}' if len(frs) > 1 else ''), fill=(172, 184, 216))
    # tira de animacion
    y = filas * 200 + 10
    for k, nom in enumerate(('wait', 'progress')):
        frs = [c for c in todo[nom] if c[0] == 48]
        for j, c in enumerate(frs):
            img.paste(c[1], (10 + j * 56 + k * 0, y + k * 56), c[1])
        d.text((10 + 8 * 56 + 8, y + k * 56 + 20), nom, fill=(172, 184, 216))
    img.crop((0, 0, img.width, y + 120)).save(AQUI / 'vista-previa.png')
    print('vista previa:', AQUI / 'vista-previa.png')


if __name__ == '__main__':
    main()
