#!/usr/bin/env python3
"""NeonGrid · construye las capas del fondo animado (paquete org.neongrid.wallpaper).

Reutiliza el metodo del concepto 'opus' (concepto/opus/generar-propuesta.py y animar.py, que NO se
modifican: se importan y se sustituyen funciones en memoria) y escribe, por relacion de pantalla:

  contents/capas/<rel>/vista-<modo>.png   escena estatica con las ventanas en su estado inicial
                                          (PNG indexado, <= 42 colores). Se usa como respaldo sin GPU,
                                          como relleno de bordes y como miniatura.
  contents/capas/<rel>/escena-<modo>.png  textura de DATOS (RGB) que lee el shader:
                                          R = indice de paleta base (0-41) + 64*anima + 128*parpadeo
                                          G = indice alternativo (ventana encendida/apagada) + 64*duracion(0-3)
                                          B = fase del encendido/apagado (0-255)
  contents/capas/<rel>/geo.png            R = distancia/30 (255 = cielo o suelo), G = banderas
                                          (1 suelo mojado, 2 LED, 4 cielo, 8 baliza, 16 baliza de la torre)
  contents/capas/<rel>/via.png            tren: R,G = abscisa s (16 bits), B = 128 + 64*via + parte(0-3)
  contents/capas/atlas.png                fila m = paleta del modo m (42 colores); filas 4-9 = sprites
  contents/capas/dron.png                 sprite del dron (7x4)
  contents/capas/layout.json              carteles, carriles, rutas, ventanas, balizas (contrato)
  contents/ui/layout.js                   lo mismo para QML (QML no puede leer ficheros con XHR)
  contents/shaders/*.qsb                  shaders compilados con qsb a partir de tema/fondo/shaders/

Modos: noche, dia (paletas del concepto), amanecer y atardecer (paletas calidas propias, cielo propio).
Relaciones: 16x10 (960x600, lienzo completo) y 16x9 (960x540, recorte anclado arriba).
21x9: tarea futura (ver LEEME del fondo); hoy se usa 16x9 con relleno.

Uso:  <python con Pillow> construir-capas.py [--modos noche,dia,...] [--rapido]
Solo depende de Pillow (herramienta de construccion; no se instala) y de qsb (Qt 6 Shader Tools).
"""
import os, sys
if os.environ.get('PYTHONHASHSEED') != '0':          # las semillas de los edificios dependen de hash()
    os.environ['PYTHONHASHSEED'] = '0'; os.execv(sys.executable, [sys.executable] + sys.argv)
import math, json, random, time, shutil, subprocess, importlib.util
import multiprocessing as _mp
from PIL import Image, ImageDraw, ImageChops

HERE = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.normpath(os.path.join(HERE, '..', '..'))
OPUS = os.path.join(RAIZ, 'concepto', 'opus')
PAQ = os.path.join(RAIZ, 'paquete', 'neongrid', 'share', 'plasma', 'wallpapers', 'org.neongrid.wallpaper')
CAPAS = os.path.join(PAQ, 'contents', 'capas')

spec = importlib.util.spec_from_file_location('an', os.path.join(OPUS, 'animar.py'))
an = importlib.util.module_from_spec(spec); spec.loader.exec_module(an)
gp = an.gp
W, H, FOC = gp.W, gp.H, gp.FOC
P, L2W, R, mix = gp.P, gp.L2W, gp.R, gp.mix

MODOS = ['noche', 'dia', 'amanecer', 'atardecer']
RELS = {'16x10': (0, 600), '16x9': (12, 540)}       # (desplazamiento vertical del recorte, alto)
ORDEN = ('ink', 'slate', 'mist', 'glass', 'cyan', 'mag', 'vio', 'amb', 'red', 'grn', 'wht')

# ------------------------------------------------------------------ paletas calidas (propias, no un tinte)
RAMPS_A = dict(gp.RAMPS_N)   # amanecer: sombras lavanda, bruma rosa melocoton
RAMPS_A.update({
    'ink':   [(20, 16, 36), (32, 26, 54), (46, 38, 74), (62, 52, 96)],
    'slate': [(80, 66, 112), (102, 84, 134), (128, 102, 152), (158, 124, 170)],
    'mist':  [(188, 140, 172), (226, 162, 164), (250, 192, 162), (255, 224, 192)],
    'glass': [(30, 40, 72), (44, 60, 98), (66, 90, 128), (100, 128, 160)],
})
RAMPS_T = dict(gp.RAMPS_N)   # atardecer: sombras purpura, bruma naranja
RAMPS_T.update({
    'ink':   [(18, 10, 24), (30, 16, 38), (46, 24, 52), (64, 34, 66)],
    'slate': [(86, 40, 74), (112, 52, 84), (142, 66, 90), (178, 84, 92)],
    'mist':  [(212, 100, 82), (238, 132, 74), (252, 170, 92), (255, 212, 142)],
    'glass': [(36, 24, 54), (58, 36, 74), (86, 52, 94), (122, 72, 112)],
})
RAMPS = {'noche': gp.RAMPS_N, 'dia': gp.RAMPS_D, 'amanecer': RAMPS_A, 'atardecer': RAMPS_T}
gp.LITK.update({'amanecer': .5, 'atardecer': .72})
CALIDOS = {
    #            cielo arriba,     medio,           horizonte,        nube,            sombra nube,   bruma,           sol x
    'amanecer': ((40, 32, 70), (122, 98, 148), (248, 186, 160), (226, 162, 164), (46, 38, 74), (168, 128, 158), 300),
    'atardecer': ((28, 14, 34), (140, 62, 88), (252, 166, 90), (238, 132, 74), (46, 24, 52), (186, 98, 88), 600),
}
_haze_orig = gp.haze_col


def haze_col(Z, y=0):
    if gp.M.name in CALIDOS: return CALIDOS[gp.M.name][5]
    return _haze_orig(Z, y)


_sky_orig = gp.draw_sky


def draw_sky():
    if gp.M.name not in CALIDOS: return _sky_orig()
    top, mid, hor, cloud, dark, _, sunx = CALIDOS[gp.M.name]
    S, HY = gp.S, gp.HY
    for y in range(HY + 4):
        t = y / (HY + 3)
        c = mix(top, mid, t / .55) if t < .55 else mix(mid, hor, (t - .55) / .45)
        S.d.line([(0, y), (W, y)], fill=c)
    acc = Image.new('L', (W, HY + 4), 0)
    for k, (gw, gh, a) in enumerate(((10, 3, .5), (24, 6, .3), (60, 14, .2))):
        n = gp.vnoise(gw, gh, 70 + k).resize((W, HY + 4), Image.BICUBIC)
        acc = Image.blend(acc, n, a / (a + (0 if k == 0 else .6)) if k else 1.0)
    cl = acc.load(); px = S.img.load()
    for y in range(HY + 4):
        for x in range(W):
            n = cl[x, y] / 255; c = px[x, y]
            if n > .55: c = mix(c, cloud, min(1, (n - .55) * 2.2) * (.25 + .55 * y / HY))
            elif n < .4: c = mix(c, dark, (.4 - n) * 1.2)
            # sol bajo: resplandor centrado en sunx pegado al horizonte
            g = math.exp(-((x - sunx) / 170) ** 2) * math.exp(-((HY + 2 - y) / 46) ** 2)
            px[x, y] = mix(c, (255, 226, 190), min(1.0, g * .9))
    # (el disco del sol ya no se pinta aqui: lo dibuja el shader en su posicion real, ver escena.frag.in)


gp.haze_col = haze_col
gp.draw_sky = draw_sky

# ------------------------------------------------------------------ carteles: solo marco y pixeles fijos (el texto vivo lo pinta QML)
GEOM = {}            # nombre -> geometria del cartel montado (lo rellena el envoltorio de mount)
_mount_an = gp.mount


def _mount_reg(b, simg, t, ym, halo=None, face='front'):
    if face == 'front':
        a0, a1 = (b.u0, b.v0), (b.u0, b.v1)
    else:
        a0, a1 = ((b.u1, b.v0), (b.u0, b.v0)) if gp.VC < b.v0 else ((b.u0, b.v1), (b.u1, b.v1))
    pa, pb = P(*a0, ym), P(*a1, ym)
    cx = pa[0] + (pb[0] - pa[0]) * t; cy = pa[1] + (pb[1] - pa[1]) * t
    slope = (pb[1] - pa[1]) / (pb[0] - pa[0])
    w, h = simg.size
    nm = simg.info.get('name', '?')
    GEOM[nm] = dict(x=round(cx - w / 2), y=round(cy - h / 2), w=w, h=h, pendiente=round(slope, 5), dist=round(b.dist, 1))
    return _mount_an(b, simg, t, ym, halo, face)


gp.mount = _mount_reg
rp, frame, glyph = gp.rp, gp.frame, gp.glyph
RELOJ_X = [0, 18, 36, 45, 63]      # desplazamiento de cada caracter LED de "HH:MM" (paso 3, punto 2)


def v_reloj():
    acc = rp('cyan'); w, h = 100, 58
    im, d = frame(w, h, acc)
    off = rp('ink')[2]
    for ci, dx in enumerate(RELOJ_X):          # todos los LED apagados; QML enciende los que tocan
        cols = (1, 3) if ci == 2 else (0, 5)
        for j in range(7):
            for i in range(*cols):
                d.point((8 + dx + (i - cols[0]) * 3, 8 + j * 3), fill=off)
    for k in range(28): d.point((10 + k * 3, 30), fill=acc[0])
    for xx in range(6, w - 6, 2): d.point((xx, 44), fill=rp('slate')[1])
    return im


def v_cpu():
    acc = rp('mag'); w, h = 108, 50
    im, d = frame(w, h, acc, 'CPU')
    for k in range(8):                          # ranuras de las barras por nucleo
        x = 8 + k * 12; d.rectangle([x, 20, x + 7, 35], fill=rp('ink')[2])
    d.line([(6, 45), (101, 45)], fill=rp('ink')[3])
    return im


def v_net():
    acc = rp('cyan'); w, h = 84, 46
    im, d = frame(w, h, acc, 'NET')
    gx, gy, gw, gh = 6, 29, w - 12, 12
    for xx in range(gx, gx + gw, 4):
        for yy in range(gy, gy + gh, 4): d.point((xx, yy), fill=rp('ink')[3])
    return im


def v_ram():
    acc = rp('vio'); w, h = 92, 50
    im, d = frame(w, h, acc, 'SYS')
    for y in (10, 23, 36):
        for k in range(26): d.rectangle([7 + k * 3, y + 8, 8 + k * 3, y + 9], fill=rp('ink')[3])
    return im


def v_vpn():
    w, h = 66, 40
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    ink = rp('ink')
    d.polygon(gp.chamf(0, 0, w - 1, h - 1, 2), fill=ink[0])
    for yy in range(2, h - 2, 2):
        for xx in range(2 + (yy // 2) % 2, w - 2, 2): d.point((xx, yy), fill=ink[1])
    d.line([(2, 0), (w - 3, 0)], fill=rp('slate')[2]); d.line([(2, h - 1), (w - 3, h - 1)], fill=ink[2])
    return im


def v_git():
    acc = rp('amb'); w, h = 72, 42
    im, d = frame(w, h, acc, 'GIT')
    c1, c2 = acc[1], rp('mag')[1]
    for y in range(11, 37): d.point((10, y), fill=c1)
    for (x, y) in ((11, 30), (12, 29), (13, 28), (13, 27), (13, 26), (13, 25), (13, 24), (13, 23), (12, 22), (11, 21)):
        d.point((x, y), fill=c2)
    for y in (13, 20, 30, 35):
        d.rectangle([9, y - 1, 11, y + 1], fill=acc[2]); d.point((10, y), fill=rp('ink')[0])
    return im


def v_bat():
    acc = rp('mag'); w, h = 64, 40
    im, d = frame(w, h, acc, 'PWR')
    sl = rp('slate')
    d.rectangle([7, 11, 27, 19], outline=sl[2]); d.rectangle([28, 13, 29, 17], fill=sl[2])
    th = [".x.", "x.x", "x.x", "x.x", "xxx", "xxx", "xxx", "xxx", ".x."]
    for j, row in enumerate(th):
        for i, ch in enumerate(row):
            if ch == 'x': d.point((9 + i, 24 + j), fill=rp('red')[1] if j >= 3 else rp('mist')[1])
    gp.txt(d, 47, 27, 'CPU', rp('mist')[1], 'M')
    return im


gp.SIGNS.update({'reloj': v_reloj, 'cpu': v_cpu, 'net': v_net, 'ram': v_ram, 'vpn': v_vpn, 'git': v_git, 'bat': v_bat})
gp.TIPS = ' '                     # la pantalla del zepelin queda vacia (rejilla de LED apagados)



# ------------------------------------------------------------------ zepelin como sprite (para que flote)
# build_static llama a gp.draw_zeppelin sobre la escena. Aqui se envuelve: se pinta, se extrae el casco como sprite
# RGBA (pixeles cuya mascara K cambia, cuantizados a la paleta del modo) y se restaura la escena SIN zepelin.
ZSPR = {}
_zep_orig = gp.draw_zeppelin


def draw_zeppelin_sprite(*a, **k):
    S = gp.S
    antes = {n: getattr(S, n).copy() for n in ('img', 'E', 'B', 'K', 'G')}
    led0 = gp.LEDMASK.copy()
    _zep_orig(*a, **k)
    mask = ImageChops.difference(S.K, antes['K']).point(lambda v: 255 if v else 0)
    q, _ = gp.quantize(S.img, mask, amp=24)
    spr = q.convert('RGBA'); spr.putalpha(mask)
    bb = mask.getbbox()
    ZSPR[gp.M.name] = (spr.crop(bb), bb)
    for n, im in antes.items():
        setattr(S, n, im); setattr(S, 'd' + ('' if n == 'img' else n), ImageDraw.Draw(im))
    gp.LEDMASK.paste(led0)


gp.draw_zeppelin = draw_zeppelin_sprite


def haz_zepelin():
    """haz de busqueda nocturno del zepelin como capa translucida (mismos poligonos que draw_zeppelin)."""
    cx, cy, rx, ry = 372, 58, 104, 23
    bx, by = cx + 6, cy + ry - 3 + 9
    capa = Image.new('L', (W, H), 0)
    for pts, a in (([(bx - 2, by), (bx + 2, by), (bx + 60, by + 150), (bx + 6, by + 158)], 34),
                   ([(bx - 1, by), (bx + 1, by), (bx + 40, by + 152), (bx + 18, by + 156)], 30)):
        l = Image.new('L', (W, H), 0); ImageDraw.Draw(l).polygon(pts, fill=a)
        capa = ImageChops.screen(capa, l)
    im = Image.new('RGBA', (W, H), (90, 150, 170, 0)); im.putalpha(capa)
    bb = capa.getbbox()
    return im.crop(bb), bb


# ------------------------------------------------------------------ render estatico (en procesos)
def static_job(args):
    mode, rmode = args
    random.seed(0)
    gp.RAMPS_D = RAMPS[mode]                   # build_static usa RAMPS_D para todo lo que no es noche
    q = an.build_static(mode, rmode)
    out = {'img': q, 'geom': dict(GEOM), 'sigbox': [(n, b) for n, b in gp.DETAIL_BOXES]}
    if rmode == 'N':
        S = gp.S
        out.update(Zb=S.Zb, ID=S.ID, G=S.G.copy(), LED=gp.LEDMASK.copy(), WINS=list(an.WINS),
                   blds=[(b.u0, b.v0, b.u1, b.v1, b.h, b.neon, b.dist, b.Z) for b in an.BUILDINGS])
    if rmode == 'N': out['zspr'] = ZSPR.get(mode)
    return mode, rmode, out


def palette(mode):
    return [tuple(c) for k in ORDEN for c in RAMPS[mode][k]]


# ------------------------------------------------------------------ horario de ventanas (se codifica por pixel)
def window_events(wins, mode):
    """por ventana que cambia: (fase 0-255, codigo de duracion 0-3, parpadeo al encender)."""
    rnd = random.Random(77)
    day = mode == 'dia'
    p_n = .16 if not day else .07          # bucle de 96 s (768 fotogramas a 8 fps)
    p_f = .05 if not day else .025
    ev = {}
    for i, (on0, nearw) in enumerate(wins):
        r = rnd.random(); a = rnd.randrange(256); dc = rnd.randrange(4); fl = rnd.random() < .45
        if r < (p_n if nearw else p_f):
            ev[i + 1] = (a, dc, fl and not on0)
    return ev


def encode_scene(st, mode):
    """devuelve (vista P, escena RGB) a 960x600."""
    pal = palette(mode); idx = {c: i for i, c in enumerate(pal)}
    N, A, B = st[(mode, 'N')], st[(mode, 'A')]['img'], st[(mode, 'B')]['img']
    base = N['img']
    ev = window_events(N['WINS'], mode)
    wins = N['WINS']
    bpx, apx, offpx = base.load(), A.load(), B.load()
    ids = N['ID'].load()
    R_ = Image.new('L', (W, H)); G_ = Image.new('L', (W, H)); B_ = Image.new('L', (W, H))
    r, g, b = R_.load(), G_.load(), B_.load()
    miss = 0
    for y in range(H):
        for x in range(W):
            c = bpx[x, y]
            i0 = idx.get(c)
            if i0 is None: i0 = 0; miss += 1
            rv, gv, bv = i0, 0, 0
            wid = ids[x, y]
            if wid and wid in ev:
                a, dc, fl = ev[wid]
                on0 = wins[wid - 1][0]
                alt = offpx[x, y] if on0 else apx[x, y]
                ia = idx.get(alt, i0)
                if ia != i0:
                    rv = i0 + 64 + (128 if fl else 0); gv = ia + 64 * dc; bv = a
            r[x, y] = rv; g[x, y] = gv; b[x, y] = bv
    assert miss == 0, f'{mode}: {miss} pixeles fuera de paleta'
    vista = Image.frombytes('P', (W, H), R_.point(lambda v: v & 63).tobytes())
    vista.putpalette([v for c in pal for v in c])
    return vista, Image.merge('RGB', (R_, G_, B_)), len(ev)


# ------------------------------------------------------------------ geometria comun: profundidad, banderas, balizas, via del tren
def encode_geo(N, mode='noche'):
    an.set_palette(mode)
    Zb = N['Zb'].load(); Gm = N['G'].load(); Lm = N['LED'].load()
    beac = an.beacon_pts(N['img'], N['blds'])
    R_ = Image.new('L', (W, H)); G_ = Image.new('L', (W, H))
    r, g = R_.load(), G_.load()
    for y in range(H):
        for x in range(W):
            z = Zb[x, y]
            r[x, y] = 255 if z > 5e7 else int(min(254, z / 30))
            f = (1 if Gm[x, y] else 0) | (2 if Lm[x, y] else 0) | (4 if z > 5e8 else 0)
            g[x, y] = f
    for i, (x, y, ph, per) in enumerate(beac):
        if 0 <= x < W and 0 <= y < H: g[x, y] = g[x, y] | (16 if i == 0 else 8)
    return Image.merge('RGB', (R_, G_, Image.new('L', (W, H), 0))), beac


def encode_rail(N):
    """recorre las dos vias y pinta, de lejos a cerca, la seccion del tren; guarda s y la parte."""
    Zb = N['Zb'].load()
    Y, th, tw = 20.0, 4.6, 3.4
    segs = []
    ds = .5
    for ti, (o, dirn, k) in enumerate(an.TRAINS):
        s = 0.0
        while s < an.RLEN - ds:
            ua, va, nx, ny = an.rail_at(s); ub, vb, _, _ = an.rail_at(s + ds)
            Zm = gp.depth((ua + ub) / 2, (va + vb) / 2)
            if Zm >= 250:
                dist = math.hypot(*L2W((ua + ub) / 2, (va + vb) / 2)) - 6
                segs.append((dist, ti, s + ds / 2, ua, va, ub, vb, nx, ny, o))
            s += ds
    segs.sort(key=lambda q: -q[0])
    SI = Image.new('I', (W, H), 0); PT = Image.new('L', (W, H), 0); DZ = Image.new('F', (W, H), 1e9)
    dS, dP, dZ = ImageDraw.Draw(SI), ImageDraw.Draw(PT), ImageDraw.Draw(DZ)

    def poly(pts, s16, meta, dist):
        pts = [(round(x), round(y)) for x, y in pts]
        dS.polygon(pts, fill=s16); dP.polygon(pts, fill=meta); dZ.polygon(pts, fill=float(dist))

    for dist, ti, s, ua, va, ub, vb, nx, ny, o in segs:
        s16 = int(round(s / an.RLEN * 65535))
        m = 128 + 64 * ti
        C0 = (ua + nx * (o - tw / 2), va + ny * (o - tw / 2)); C1 = (ua + nx * (o + tw / 2), va + ny * (o + tw / 2))
        D0 = (ub + nx * (o - tw / 2), vb + ny * (o - tw / 2)); D1 = (ub + nx * (o + tw / 2), vb + ny * (o + tw / 2))
        Ta, Tb = (C0, D0) if math.hypot(*L2W(*C0)) < math.hypot(*L2W(*C1)) else (C1, D1)
        poly([P(*Ta, Y + .3), P(*Tb, Y + .3), P(*Tb, Y + th), P(*Ta, Y + th)], s16, m + 0, dist)
        poly([P(*C0, Y + th), P(*D0, Y + th), P(*D1, Y + th), P(*C1, Y + th)], s16, m + 1, dist)
        poly([P(*Ta, Y + 1.8), P(*Tb, Y + 1.8), P(*Tb, Y + 3.4), P(*Ta, Y + 3.4)], s16, m + 2, dist - .1)
        a, b = P(*Ta, Y + 1.0), P(*Tb, Y + 1.0)
        dS.line([(round(a[0]), round(a[1])), (round(b[0]), round(b[1]))], fill=s16)
        dP.line([(round(a[0]), round(a[1])), (round(b[0]), round(b[1]))], fill=m + 3)
        dZ.line([(round(a[0]), round(a[1])), (round(b[0]), round(b[1]))], fill=float(dist - .1))
    sp, pp, zp = SI.load(), PT.load(), DZ.load()
    R_ = Image.new('L', (W, H)); G_ = Image.new('L', (W, H)); B_ = Image.new('L', (W, H))
    r, g, b = R_.load(), G_.load(), B_.load()
    n = 0
    for y in range(H):
        for x in range(W):
            if pp[x, y] and zp[x, y] < Zb[x, y]:
                v = sp[x, y]; r[x, y] = v >> 8; g[x, y] = v & 255; b[x, y] = pp[x, y]; n += 1
    return Image.merge('RGB', (R_, G_, B_)), n


# ------------------------------------------------------------------ atlas: paletas + sprites
def build_atlas():
    at = Image.new('RGB', (64, 16), (0, 0, 0)); px = at.load()
    for m, mode in enumerate(MODOS):
        for i, c in enumerate(palette(mode)): px[i, m] = c
    codes = {'.': 0, 'x': 1, 'c': 2, 'n': 3, 'h': 4}
    for (spr, x0) in ((an.FLY_M, 0), (an.FLY_S, 12), (an.FLY_T, 20)):
        for j, row in enumerate(spr):
            for i, ch in enumerate(row): px[x0 + i, 4 + j] = (codes[ch] * 50, 0, 0)
    return at


def build_drone():
    im = Image.new('RGBA', (7, 4), (0, 0, 0, 0)); px = im.load()
    for j, row in enumerate(gp.DRONE):
        for i, ch in enumerate(row):
            if ch == 'x': px[i, j] = R('slate', 3) + (255,) if j == 0 else R('ink', 3) + (255,)
    return im


def save_png(im, path):
    im.save(path, optimize=True)
    return os.path.getsize(path)


def ncolors(path):
    im = Image.open(path)
    return len(im.convert('RGB').getcolors(1 << 20))


# ------------------------------------------------------------------ shaders (plantilla + constantes del concepto)
def build_shaders(meta):
    src = os.path.join(HERE, 'shaders'); dst = os.path.join(PAQ, 'contents', 'shaders')
    os.makedirs(dst, exist_ok=True)
    qsb = shutil.which('qsb') or '/usr/lib/qt6/bin/qsb'
    consts = {
        'CX': gp.CX, 'HY': gp.HY, 'FOC': gp.FOC, 'CAMH': gp.CAMH, 'SA': gp.SA, 'CA': gp.CA, 'Z0': gp.Z0, 'X0': gp.X0,
        'RLEN': an.RLEN, 'NF': an.NF, 'U_MIN': an.U_MIN, 'U_SPAN': an.U_SPAN, 'V_MIN': an.V_MIN, 'V_SPAN': an.V_SPAN,
        'AVE': gp.AVE, 'BLK_U': gp.BLK_U, 'ST_U': gp.ST_U, 'TRAIN_LEN': an.TRAIN_LEN,
    }
    fly = []
    for i, (A, B, ph, neon, k) in enumerate(an.FLYERS):
        fly.append(f'    flyer(acc, cp, vec3({A[0]:.3f}, {A[1]:.3f}, {A[2]:.1f}), vec3({B[0]:.3f}, {B[1]:.3f}, {B[2]:.1f}), {ph:.2f}, {16.0 if neon == "cyan" else 20.0:.1f}, {float(i):.1f});')
    lanes = []
    for li, (v, dirn, gap, m, pat) in enumerate(an.LANES):
        n = int(round(an.U_SPAN / gap / m)) * m
        lanes.append(f'    laneCars(acc, g0, g1, {v:.1f}, {float(dirn):.1f}, {gap:.1f}, {float(m):.1f}, {n * gap:.1f}, {float(li):.1f});')
    cross = []
    for ci, (u, dirn) in enumerate(an.CROSS):
        cross.append(f'    crossCars(acc, g0, g1, {u:.2f}, {float(dirn):.1f}, {float(ci):.1f});')
    out = {}
    for fn in sorted(os.listdir(src)):
        if not fn.endswith(('.frag.in', '.frag', '.vert')): continue
        txt = open(os.path.join(src, fn)).read()
        for k, v in consts.items(): txt = txt.replace('@' + k + '@', repr(float(v)))
        txt = txt.replace('@FLYERS@', '\n'.join(fly)).replace('@LANES@', '\n'.join(lanes)).replace('@CROSS@', '\n'.join(cross))
        name = fn[:-3] if fn.endswith('.in') else fn
        gen = os.path.join(meta['tmp'], name); open(gen, 'w').write(txt)
        o = os.path.join(dst, name + '.qsb')
        r = subprocess.run([qsb, '--glsl', '300es,120,150,330', '-o', o, gen], capture_output=True, text=True)
        if r.returncode:
            print(r.stdout, r.stderr); raise SystemExit(f'qsb fallo con {fn}')
        out[name] = os.path.getsize(o)
    return out


# ------------------------------------------------------------------ principal
def main():
    t0 = time.time()
    modos = MODOS
    for a in sys.argv[1:]:
        if a.startswith('--modos='): modos = a.split('=', 1)[1].split(',')
    tmp = os.environ.get('NG_TMP') or os.path.join(os.environ.get('TMPDIR', '/tmp'), 'neongrid-capas')
    os.makedirs(tmp, exist_ok=True)
    if '--solo-shaders' in sys.argv:
        print(json.dumps(build_shaders({'tmp': tmp}))); return
    jobs = [(m, r) for m in modos for r in 'NAB']
    with _mp.get_context('fork').Pool(min(len(jobs), os.cpu_count() or 4)) as pool:
        res = pool.map(static_job, jobs)
    st = {(m, r): o for m, r, o in res}
    print(f'capas estaticas ({len(jobs)}): {time.time() - t0:.1f} s', flush=True)
    os.makedirs(CAPAS, exist_ok=True)
    geom = st[(modos[0], 'N')]['geom']
    base_mode = 'noche' if 'noche' in modos else modos[0]
    geo, beac = encode_geo(st[(base_mode, 'N')], base_mode)
    via, nvia = encode_rail(st[(base_mode, 'N')])
    informe = {'modos': {}, 'relaciones': {}}
    enc = {}
    for m in modos:
        vista, esc, nev = encode_scene(st, m)
        enc[m] = (vista, esc)
        informe['modos'][m] = {'ventanas': len(st[(m, 'N')]['WINS']), 'ventanas_animadas': nev}
    for rel, (oy, hh) in RELS.items():
        od = os.path.join(CAPAS, rel); os.makedirs(od, exist_ok=True)
        box = (0, oy, W, oy + hh)
        tam = {}
        tam['geo.png'] = save_png(geo.crop(box), os.path.join(od, 'geo.png'))
        tam['via.png'] = save_png(via.crop(box), os.path.join(od, 'via.png'))
        for m in modos:
            vista, esc = enc[m]
            tam[f'vista-{m}.png'] = save_png(vista.crop(box), os.path.join(od, f'vista-{m}.png'))
            tam[f'escena-{m}.png'] = save_png(esc.crop(box), os.path.join(od, f'escena-{m}.png'))
        colores = {m: ncolors(os.path.join(od, f'vista-{m}.png')) for m in modos}
        porm = {m: tam[f'vista-{m}.png'] + tam[f'escena-{m}.png'] + tam['geo.png'] + tam['via.png'] for m in modos}
        informe['relaciones'][rel] = {'tam': [W, hh], 'oy': oy, 'bytes': tam, 'bytes_por_modo': porm, 'colores_vista': colores}
    save_png(build_atlas(), os.path.join(CAPAS, 'atlas.png'))
    save_png(build_drone(), os.path.join(CAPAS, 'dron.png'))
    zbb = None
    for m in modos:      # sprites del zepelin (uno por modo, misma geometria) y su haz nocturno
        spr, bb = st[(m, 'N')]['zspr']
        assert zbb is None or zbb == bb, f'zepelin: caja distinta en {m}: {bb} != {zbb}'
        zbb = bb; save_png(spr, os.path.join(CAPAS, f'zepelin-{m}.png'))
    haz, hbb = haz_zepelin(); save_png(haz, os.path.join(CAPAS, 'zepelin-haz.png'))
    ztx, zty, ztw, zth = an.SCR
    for m in modos:      # mascara de la matriz LED del zepelin: deja ver 1 de cada 2x2 pixeles
        ink0 = palette(m)[0]
        rj = Image.new('RGBA', (ztw - 6, zth - 8), ink0 + (255,)); px = rj.load()
        for y in range(0, zth - 8, 2):
            for x in range(0, ztw - 6, 2): px[x, y] = (0, 0, 0, 0)
        save_png(rj, os.path.join(CAPAS, f'rejilla-led-{m}.png'))
    # ---- layout (contrato) ------------------------------------------------------------------
    carteles = {}
    for nm, g in geom.items():
        carteles[nm] = g
    ztx, zty, ztw, zth = an.SCR
    lay = {
        'version': 1,
        'lienzo': [W, H], 'pixel': 2,
        'relaciones': {rel: {'tam': [W, hh], 'oy': oy, 'carpeta': f'capas/{rel}'} for rel, (oy, hh) in RELS.items()},
        'modos': modos,
        'paletas': {m: ['#%02x%02x%02x' % c for c in palette(m)] for m in modos},
        'camara': {'CX': gp.CX, 'HY': gp.HY, 'FOC': gp.FOC, 'CAMH': gp.CAMH, 'ANG_grados': 20, 'Z0': gp.Z0, 'X0': gp.X0},
        'carteles': carteles,
        'reloj_led': {'x': 8, 'y': 8, 'paso': 3, 'punto': 2, 'desplazamientos': RELOJ_X},
        'zepelin_pantalla': {'x': ztx + 3, 'y': zty + 4, 'w': ztw - 6, 'h': zth - 8},
        'zepelin_sprite': {'x': zbb[0], 'y': zbb[1], 'w': zbb[2] - zbb[0], 'h': zbb[3] - zbb[1]},
        'zepelin_haz': {'x': hbb[0], 'y': hbb[1], 'w': hbb[2] - hbb[0], 'h': hbb[3] - hbb[1]},
        'drones': [{'x': cx, 'y': cy, 'dato': ['actualizaciones', 'servicios', 'sync', None, None, None, None, None][i], 'fase': i}
                   for i, (cx, cy, lab, acc, ic, _) in enumerate(an.DRONES)],
        'carriles': [{'v': v, 'sentido': d, 'separacion': g, 'patron': m, 'tipos': p} for (v, d, g, m, p) in an.LANES],
        'calles_transversales': [{'u': u, 'sentido': d} for (u, d) in an.CROSS],
        'tren': {'longitud_via': an.RLEN, 'vias': [{'desplazamiento': o, 'sentido': d, 'convoyes': k} for (o, d, k) in an.TRAINS],
                 'largo_convoy': an.TRAIN_LEN, 'pixeles_via': nvia},
        'voladores': [{'desde': A, 'hasta': B, 'fase': ph, 'neon': n} for (A, B, ph, n, k) in an.FLYERS],
        'balizas': [{'x': x, 'y': y, 'fase': ph, 'periodo': per, 'torre': i == 0} for i, (x, y, ph, per) in enumerate(beac)],
        'ventanas': informe['modos'],
        'bucle_fotogramas': 768, 'fps': 8,
    }
    with open(os.path.join(CAPAS, 'layout.json'), 'w') as fh:
        json.dump(lay, fh, ensure_ascii=False, indent=1)
    with open(os.path.join(PAQ, 'contents', 'ui', 'layout.js'), 'w') as fh:
        fh.write('// Generado por tema/fondo/construir-capas.py: no editar a mano.\n.pragma library\nvar L = ')
        json.dump({k: lay[k] for k in ('lienzo', 'relaciones', 'modos', 'paletas', 'carteles', 'reloj_led', 'zepelin_pantalla', 'zepelin_sprite', 'zepelin_haz', 'drones', 'camara')}, fh, ensure_ascii=False)
        fh.write(';\n')
    informe['shaders'] = build_shaders({'tmp': tmp})
    informe['segundos'] = round(time.time() - t0, 1)
    with open(os.path.join(HERE, 'informe-capas.json'), 'w') as fh:
        json.dump(informe, fh, ensure_ascii=False, indent=1)
    print(json.dumps(informe, ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main()
