#!/usr/bin/env python3
"""Paleta de NeonGrid (fuente unica) y validador de contraste WCAG.
Uso:  python3 paleta.py            -> tabla de contraste
Importar:  from paleta import PAL, contraste
"""
PAL = {
    # superficies (de mas oscura a mas clara)
    'fondo':   (11, 14, 26),    # #0B0E1A
    'panel':   (18, 23, 43),    # #12172B
    'boton':   (21, 27, 52),
    'alterno': (15, 19, 37),
    # texto
    'texto':   (230, 241, 255), # #E6F1FF
    'tenue':   (172, 184, 216), # texto secundario
    # acentos (rampas de 4 tonos en la escena; aqui el tono "luz")
    'cian':    (0, 229, 255),   # principal
    'magenta': (255, 43, 214),  # atencion
    'verde':   (57, 255, 136),  # OK / prompt
    'ambar':   (255, 176, 32),  # aviso
    'rojo':    (255, 59, 92),   # error
    'violeta': (139, 92, 255),  # estructura / inactivo
    'violeta_claro': (192, 172, 255),
    # variantes CLARAS para escribir texto (los puros quedan para bordes y adornos)
    'magenta_t': (255, 124, 233),
    'rojo_t':    (255, 132, 150),
    'sel':     (0, 74, 100),    # fondo de seleccion
}


def _lin(c):
    c /= 255
    return c / 12.92 if c <= .03928 else ((c + .055) / 1.055) ** 2.4


def lum(rgb): r, g, b = (_lin(v) for v in rgb); return .2126 * r + .7152 * g + .0722 * b


def contraste(a, b):
    la, lb = lum(a), lum(b)
    if la < lb: la, lb = lb, la
    return (la + .05) / (lb + .05)


if __name__ == '__main__':
    fondos = ['fondo', 'panel', 'boton']
    textos = ['texto', 'tenue', 'cian', 'magenta_t', 'verde', 'ambar', 'rojo_t', 'violeta_claro']
    print(f"{'color':14}" + ''.join(f'{f:>9}' for f in fondos))
    mal = 0
    for t in textos:
        row = ''
        for f in fondos:
            c = contraste(PAL[t], PAL[f]); row += f'{c:8.1f}' + ('*' if c < 7 else ' '); mal += c < 7
        print(f'{t:14}{row}')
    print(f"\nseleccion: texto sobre sel = {contraste(PAL['texto'], PAL['sel']):.1f}")
    print('(* = menos de 7:1)  solo bordes/adornos, NO texto:', ', '.join(f"{k} {contraste(PAL[k], PAL['fondo']):.1f}" for k in ('magenta', 'rojo', 'violeta')))
    print('suspensos:', mal)
