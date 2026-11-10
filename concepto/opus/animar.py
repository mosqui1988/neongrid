#!/usr/bin/env python3
"""NeonGrid · propuesta 'opus' animada: bucle sin saltos de 96 fotogramas a 8 fps (12 s).

Reutiliza generar-propuesta.py (no lo modifica: sustituye algunas funciones al importarlo) y
organiza la escena en CAPAS, que es como deberia montarse el tema real en QML:

  fondo estatico ........ ciudad + cielo + zepelin (cuerpo) + carteles fijos   (PNG por modo)
  ventanas .............. mascara de ids + color encendido + color apagado      (PNG id + 2 PNG)
  coches + estelas ...... sprites en carriles con perspectiva                    (dinamico)
  voladores ............. lanzaderas con neon inferior y halo escalonado         (dinamico)
  tren .................. convoyes sobre la via curva                            (dinamico)
  lluvia ................ gotas en bucle + salpicaduras en suelo mojado          (dinamico)
  carteles dinamicos .... reloj, CPU, NET, letrero del zepelin                   (dinamico)
  balizas/neones ........ pulsos y titileos sobre pixeles conocidos              (dinamico)

Oclusion: durante el render estatico se guarda un z-buffer (distancia del objeto que ocupa cada
pixel); los elementos dinamicos solo se pintan donde estan mas cerca que lo que ya hay.
Todos los colores pertenecen a la paleta cerrada de rampas de 4 tonos.

Uso:
  python animar.py noche [--calma]     -> animacion-noche.mp4
  python animar.py dia [--calma]       -> animacion-dia.mp4
  python animar.py ciclo [--calma]     -> animacion-ciclo.mp4 (192 fotogramas: amanecer-dia-atardecer-noche)
  python animar.py todo [--calma]
  python animar.py prueba              -> solo fotogramas 0,24,48,72,95,96 en el scratchpad
"""
import os, sys, math, random, json, time, shutil, importlib.util
if os.environ.get('PYTHONHASHSEED') != '0':          # semillas de edificios reproducibles
    os.environ['PYTHONHASHSEED'] = '0'; os.execv(sys.executable, [sys.executable] + sys.argv)
import multiprocessing as _mp
Pool = _mp.get_context("fork").Pool
from PIL import Image, ImageDraw, ImageMath, ImageChops

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location('gp', os.path.join(HERE, 'generar-propuesta.py'))
gp = importlib.util.module_from_spec(spec); spec.loader.exec_module(gp)
W, H, FOC = gp.W, gp.H, gp.FOC
P, L2W, depth, R, mix = gp.P, gp.L2W, gp.depth, gp.R, gp.mix
NF = 96
CALMA = 0.2 if '--calma' in sys.argv else 1.0
TMP = os.environ.get('NG_TMP') or os.path.join(__import__('tempfile').gettempdir(), 'neongrid-anim')

# =====================================================================================
# 1. RENDER ESTATICO CON Z-BUFFER, IDS DE VENTANA E IDS DE CARTEL
# =====================================================================================
CURD = [1e9]          # distancia del objeto que se esta dibujando
RMODE = ['N']         # N = ventanas en su estado inicial, A = todas encendidas, B = todas apagadas
WINS = []             # por ventana: (encendida_al_inicio, cerca)
SIGNMAP = {}          # cartel -> (sid, {dst: (i, j, es_fondo)})


def _new_canvases():
    S = gp.S
    S.img = Image.new('RGB', (W, H)); S.d = ImageDraw.Draw(S.img)
    S.E = Image.new('RGB', (W, H)); S.dE = ImageDraw.Draw(S.E)
    S.B = Image.new('RGB', (W, H)); S.dB = ImageDraw.Draw(S.B)
    S.G = Image.new('L', (W, H), 0); S.dG = ImageDraw.Draw(S.G)
    S.K = Image.new('L', (W, H), 0); S.dK = ImageDraw.Draw(S.K)
    S.Zb = Image.new('F', (W, H), 1e9); S.dZ = ImageDraw.Draw(S.Zb)
    S.ID = Image.new('I', (W, H), 0); S.dI = ImageDraw.Draw(S.ID)
    S.SID = Image.new('I', (W, H), 0); S.dS = ImageDraw.Draw(S.SID)


def _poly(pts, col, ground=False, crisp=False, emis=False, wid=0, draw=True):
    S = gp.S
    pts = [(round(x), round(y)) for x, y in pts]
    if draw:
        S.d.polygon(pts, fill=col)
        S.dG.polygon(pts, fill=255 if ground else 0)
        S.dZ.polygon(pts, fill=float(1e8 if ground else CURD[0]))
        S.dS.polygon(pts, fill=0)
        if crisp: S.dK.polygon(pts, fill=255)
        if emis: S.dE.polygon(pts, fill=col)
        if emis is True: S.dB.polygon(pts, fill=col)
    if not ground: S.dI.polygon(pts, fill=wid)


def _pix(x, y, col, emis=False, crisp=False, wid=0, draw=True):
    S = gp.S
    x, y = int(round(x)), int(round(y))
    if 0 <= x < W and 0 <= y < H:
        if draw:
            S.img.putpixel((x, y), col); S.G.putpixel((x, y), 0)
            S.Zb.putpixel((x, y), float(CURD[0])); S.SID.putpixel((x, y), 0)
            if emis: S.E.putpixel((x, y), col)
            if emis is True: S.B.putpixel((x, y), col)
            if crisp: S.K.putpixel((x, y), 255)
        S.ID.putpixel((x, y), wid)


def _win(on0, near):
    """registra una ventana y decide si se pinta encendida en el modo actual."""
    WINS.append((on0, near))
    wid = len(WINS)
    lit = {'N': on0, 'A': True, 'B': False}[RMODE[0]]
    return wid, lit


def _draw_face(b, a, c, kind, rnd):
    """copia de gp.draw_face con consumo de azar fijo (igual en los 3 modos) y registro de ventanas."""
    R_, mix_, P_ = gp.R, gp.mix, gp.P
    mat = gp.MATS[b.mat]
    base = R_(*mat[kind])
    if kind == 'front' and b.mat == 'conc' and rnd.random() < .3: base = R_('slate', 0)
    ZA, ZC = gp.depth(*a), gp.depth(*c)
    Zm = (ZA + ZC) / 2
    hz = gp.haze_col(Zm)
    nb = 6 if b.h > 40 else 3
    xm = (P_(*a)[0] + P_(*c)[0]) / 2
    cm = gp.calm(xm)
    for i in range(nb):
        y0 = b.h * i / nb; y1 = b.h * (i + 1) / nb
        col = mix_(base, hz, gp.fogk(Zm, (y0 + y1) / 2))
        col = mix_(col, R_('ink', 0), (1 - cm) * .45)
        _poly(gp.face_pts(a, c, y0, y1 + .01), col)
    fa = gp.fogk(Zm, b.h * .6)
    flen = math.hypot(c[0] - a[0], c[1] - a[1])
    du, dv = (c[0] - a[0]) / flen, (c[1] - a[1]) / flen
    glass = b.mat == 'glass'
    fh = 3.8 if glass else 4.2
    cw = 3.2 if glass else 4.0
    ncol = max(1, int((flen - 2) / cw)); nfl = max(1, int((b.h - 3) / fh))
    pxm = FOC / Zm
    side = kind == 'side'
    litp = b.lit * (.55 if side else 1.0) * (.25 + .75 * cm) * gp.LITK[gp.M.name]
    wc1, wc2 = mat['win']
    tone = rnd.random()
    dom = [(R_('mist', 2), R_('mist', 3), R_('wht', 0)), (R_('cyan', 3), R_('mist', 3), R_('cyan', 2)),
           (R_('amb', 3), R_('amb', 2), R_('mist', 3)), (R_('mist', 1), R_('mist', 2), R_('mist', 3))][
        0 if tone < .4 else (1 if tone < .55 or wc1 == 'cyan' and tone < .8 else (2 if tone < .8 else 3))]
    def wcol(r2):
        if r2 < .5: return dom[0]
        if r2 < .8: return dom[1]
        if r2 < .93: return dom[2]
        return R_('amb', 3) if dom[0] != R_('amb', 3) else R_('mist', 3)
    lit_floor = [rnd.random() < litp * 1.4 for _ in range(nfl)]
    if pxm * fh < 1.6:
        step = max(1, int(1.6 / (pxm * cw)))
        for fl in range(0, nfl, max(1, int(1.6 / (pxm * fh)))):
            run0 = rnd.randint(0, ncol); run1 = run0 + rnd.randint(ncol // 3, ncol)
            for k in range(0, ncol, step):
                r = rnd.random(); rc = rnd.random()
                inrun = lit_floor[fl] and run0 <= k <= run1
                p = .85 if inrun else litp * .18
                if r < min(1.0, p * 1.5 + .02):          # candidata (puede encenderse en algun momento)
                    t = (k + .5) / ncol * flen
                    x, y = P_(a[0] + du * t, a[1] + dv * t, 2 + fl * fh + fh * .5)
                    col = mix_(wcol(rc), hz, fa * .7)
                    col = mix_(col, R_('ink', 1), (1 - cm) * .6)
                    wid, lit = _win(r < p, False)
                    _pix(x, y, col, emis='w', wid=wid, draw=lit)
        return
    if glass:
        for fl in range(nfl):
            y0 = 2 + fl * fh
            rg = rnd.random()
            k0 = rnd.randint(0, ncol // 3); k1 = ncol - rnd.randint(0, ncol // 3)
            rc = rnd.random()
            on0 = lit_floor[fl] or rg < litp * .5
            if on0 or rg < litp * 1.3 + .05:
                t0, t1 = k0 / ncol * flen, k1 / ncol * flen
                col = mix_(wcol(rc * .9), hz, fa * .6)
                col = mix_(col, R_('glass', 1), (1 - cm) * .7)
                q = [P_(a[0] + du * t0, a[1] + dv * t0, y0 + .6), P_(a[0] + du * t1, a[1] + dv * t1, y0 + .6),
                     P_(a[0] + du * t1, a[1] + dv * t1, y0 + fh - 1.1), P_(a[0] + du * t0, a[1] + dv * t0, y0 + fh - 1.1)]
                wid, lit = _win(on0, True)
                _poly(q, col, emis='w', wid=wid, draw=lit)
            if pxm * fh >= 3 and fl % 2 == 0:
                lc = mix_(R_('glass', 3), hz, fa); lc = mix_(lc, R_('glass', 0), 1 - cm)
                x0, y = P_(*a, y0); x1, y1 = P_(*c, y0)
                gp.S.d.line([(round(x0), round(y)), (round(x1), round(y1))], fill=lc)
        if pxm * cw * 3 >= 4:
            for k in range(0, ncol + 1, 3):
                t = k / ncol * flen
                x, y0 = P_(a[0] + du * t, a[1] + dv * t, 0); _, y1 = P_(a[0] + du * t, a[1] + dv * t, b.h)
                gp.S.d.line([(round(x), round(y1)), (round(x), round(y0))], fill=mix_(base, R_('ink', 0), .4))
        return
    gap_u = .9 if pxm * cw > 5 else .55
    for fl in range(nfl):
        y0 = 2 + fl * fh
        pf = litp * (1.25 if lit_floor[fl] else .45)
        for k in range(ncol):
            r = rnd.random(); rc = rnd.random()
            t0 = k * cw + gap_u + (flen - ncol * cw) / 2; t1 = t0 + cw - gap_u * 2
            q = [P_(a[0] + du * t0, a[1] + dv * t0, y0 + .7), P_(a[0] + du * t1, a[1] + dv * t1, y0 + .7),
                 P_(a[0] + du * t1, a[1] + dv * t1, y0 + fh - 1.2), P_(a[0] + du * t0, a[1] + dv * t0, y0 + fh - 1.2)]
            on0 = r < pf
            lcol = mix_(wcol(rc), hz, fa * .55); lcol = mix_(lcol, R_('ink', 1), (1 - cm) * .65)
            dcol = mix_(mix_(base, R_('ink', 0), .55), hz, fa) if pxm * cw > 3 else None
            if not on0 and dcol is None and r > pf * 2.2 + .03:
                continue                                    # nunca se enciende y no se ve: no se registra
            wid, lit = _win(on0, True)
            if lit: _poly(q, lcol, emis='w', wid=wid)
            elif dcol is not None: _poly(q, dcol, wid=wid)
            else: _poly(q, None, wid=wid, draw=False)


def _mount(b, simg, t, ym, halo=None, face='front'):
    """copia de gp.mount que ademas guarda el mapeo pixel a pixel (para repintar el cartel en vivo)
    y marca el cartel en el z-buffer (los voladores pasan por detras, nunca por encima)."""
    S = gp.S
    if face == 'front':
        a0, a1 = (b.u0, b.v0), (b.u0, b.v1)
    else:
        a0, a1 = ((b.u1, b.v0), (b.u0, b.v0)) if gp.VC < b.v0 else ((b.u0, b.v1), (b.u1, b.v1))
    pa, pb = P(*a0, ym), P(*a1, ym)
    cx = pa[0] + (pb[0] - pa[0]) * t; cy = pa[1] + (pb[1] - pa[1]) * t
    slope = (pb[1] - pa[1]) / (pb[0] - pa[0])
    w, h = simg.size
    x0 = round(cx - w / 2); y0 = round(cy - h / 2)
    spx = simg.load()
    bright = [[False] * h for _ in range(w)]
    for i in range(w):
        for j in range(h):
            r, g, b_, a = spx[i, j]
            bright[i][j] = bool(a) and r + g + b_ > 150
    inner = range(6, w - 6)
    rowfill = [sum(bright[i][j] for i in inner) for j in range(h)]
    bands = []; j = 0
    while j < h:
        if rowfill[j] == 0: bands.append((j, j, True)); j += 1; continue
        k = j
        while k + 1 < h and rowfill[k + 1] > 0: k += 1
        full = max(rowfill[j:k + 1]) > len(inner) * .8 and k - j < 2
        bands.append((j, k, full)); j = k + 1
    merged = []
    for bd in bands:
        if merged and not bd[2] and not merged[-1][2]:
            pj0, pj1, _ = merged[-1]
            if bd[0] - pj1 <= 3 and (rowfill[bd[0]] > 0 or bd[0] == bd[1]):
                merged[-1] = (pj0, bd[1], False); continue
        merged.append(bd)
    bands = merged
    ideal = [slope * (i - w / 2) for i in range(w)]
    band_dys = []
    for (j0, j1, free) in bands:
        cur = round(ideal[0]); dl = []
        for i in range(w):
            tgt = round(ideal[i])
            if tgt != cur:
                ok = free or i < 6 or i > w - 7 or not any(bright[i][jj] or bright[i - 1][jj] for jj in range(j0, j1 + 1))
                if ok or abs(tgt - cur) > 1: cur += 1 if tgt > cur else -1
            dl.append(cur)
        band_dys.append(dl)
    dys = [round(v) for v in ideal]
    gp.DETAIL_BOXES.append((simg.info.get('name', '?'), (x0 - 4, y0 + min(dys) - 4, x0 + w + 4, y0 + h + max(dys) + 4)))
    if halo:
        col, k = halo
        for r, a in ((7, .07 * k), (4, .12 * k), (2, .20 * k)):
            q = [(x0 - r, y0 - r + dys[0]), (x0 + w + r, y0 - r + dys[-1]), (x0 + w + r, y0 + h + r + dys[-1]), (x0 - r, y0 + h + r + dys[0])]
            lay = Image.new('L', (W, H), 0); ImageDraw.Draw(lay).polygon(q, fill=int(255 * a))
            S.img = Image.composite(ImageChops.add(S.img, Image.new('RGB', (W, H), col)), S.img, lay)
            S.E = Image.composite(ImageChops.add(S.E, Image.new('RGB', (W, H), col)), S.E, lay)
        S.d = ImageDraw.Draw(S.img); S.dE = ImageDraw.Draw(S.E)
    alpha = simg.getchannel('A')
    led = simg.info.get('led')
    back = simg.copy(); bd_ = ImageDraw.Draw(back)
    bd_.rectangle([5, 5, w - 6, h - 6], fill=R('ink', 0) + (255,))
    name = simg.info.get('name', '?')
    sid = len(SIGNMAP) + 1
    mp = {}
    apx = alpha.load()
    for i in range(w):
        S.img.paste(back.crop((i, 0, i + 1, h)), (x0 + i, y0 + dys[i]), alpha.crop((i, 0, i + 1, h)))
        for jj in range(h):
            if apx[i, jj]: mp[(x0 + i, y0 + jj + dys[i])] = (i, jj, True)
    for i in range(w):
        for (j0, j1, _), dl in zip(bands, band_dys):
            hh = j1 - j0 + 1
            col = simg.crop((i, j0, i + 1, j1 + 1)); am = alpha.crop((i, j0, i + 1, j1 + 1))
            pos = (x0 + i, y0 + j0 + dl[i])
            box = (pos[0], pos[1], pos[0] + 1, pos[1] + hh)
            S.img.paste(col, pos, am); S.E.paste(col, pos, am); S.B.paste(col, pos, am)
            S.K.paste(255, box, am); S.G.paste(0, box, am)
            for jj in range(j0, j1 + 1):
                if apx[i, jj]: mp[(pos[0], pos[1] + jj - j0)] = (i, jj, False)
            if led is not None:
                lm = led.crop((i, j0, i + 1, j1 + 1)); gp.LEDMASK.paste(lm, pos, lm)
    for (x, y) in mp:
        if 0 <= x < W and 0 <= y < H:
            S.SID.putpixel((x, y), sid); S.Zb.putpixel((x, y), 0.0); S.ID.putpixel((x, y), 0)
    SIGNMAP[name] = (sid, mp)
    S.d = ImageDraw.Draw(S.img); S.dE = ImageDraw.Draw(S.E); S.dK = ImageDraw.Draw(S.K); S.dG = ImageDraw.Draw(S.G); S.dB = ImageDraw.Draw(S.B)
    return (x0, y0, w, h)


# sustituciones en el modulo original (no se toca el fichero)
gp.new_canvases = _new_canvases
gp.poly = _poly
gp.pix = _pix
gp.draw_face = _draw_face
gp.mount = _mount
gp.streaks = lambda: None          # las estelas pasan a la capa dinamica
gp.draw_cars = lambda: None        # los coches tambien
gp.TRAIN = (-1, -1)                # y el tren
BUILDINGS = []


def build_static(mode, rmode):
    """render de una capa estatica: devuelve la imagen cuantizada (lienzo 960x600) y los buffers."""
    gp.M.name = mode; gp.M.R = gp.RAMPS_N if mode == 'noche' else gp.RAMPS_D
    gp.LEDMASK = Image.new('L', (W, H), 0); gp.DETAIL_BOXES.clear()
    RMODE[0] = rmode; WINS.clear(); SIGNMAP.clear(); BUILDINGS.clear()
    gp.new_canvases(); gp.CARS.clear(); gp.HEROES.clear(); gp.make_heroes()
    CURD[0] = 1e8
    gp.draw_sky(); gp.S.Zb.paste(1e9, (0, 0, W, gp.HY)); gp.draw_ground(); gp.draw_streets()
    gp.S.Zb.paste(1e9, (0, 0, W, gp.HY))
    gp.S.Zb.paste(1e8, (0, gp.HY, W, H))
    city = gp.make_city() + list(gp.HEROES.values())
    BUILDINGS.extend(city)
    objs = [(b.dist, 0, b) for b in city]
    objs += [(math.hypot(*L2W(l[1], l[2])), 2, l) for l in gp.lamps()]
    for i in range(len(gp.RAIL) - 1):
        (ua, va), (ub, vb) = gp.RAIL[i], gp.RAIL[i + 1]
        objs.append((math.hypot(*L2W((ua + ub) / 2, (va + vb) / 2)), 3, i))
    objs.append((math.hypot(*L2W(*gp.TOWER)), 4, None))
    objs.sort(key=lambda o: -o[0])
    for dist, k, o in objs:
        CURD[0] = dist
        if k == 0: gp.draw_building(o)
        elif k == 2: gp.draw_lamp(o[1], o[2])
        elif k == 3: gp.draw_rail_seg(o)
        else: gp.tower_halo(); gp.draw_tower()
    gp.reflections()
    CURD[0] = 0.0
    gp.draw_zeppelin(scroll=0)     # cuerpo y haz fijos; el letrero se repinta en vivo
    gp.bloom(1.0 if mode == 'noche' else .45)
    gp.calm_left()
    q, n = gp.quantize(gp.S.img, gp.S.K, amp=24)
    return q


def static_job(args):
    mode, rmode = args
    random.seed(0)
    q = build_static(mode, rmode)
    out = {'img': q}
    if rmode == 'N':
        S = gp.S
        out.update(Zb=S.Zb, ID=S.ID, SID=S.SID, G=S.G.copy(), K=S.K.copy(), LED=gp.LEDMASK.copy(),
                   WINS=list(WINS), SIGNMAP=dict(SIGNMAP),
                   blds=[(b.u0, b.v0, b.u1, b.v1, b.h, b.neon, b.dist, b.Z) for b in BUILDINGS])
    return mode, rmode, out


# =====================================================================================
# 2. PALETA CERRADA
# =====================================================================================
class Pal:
    cols = []; where = {}; cache = {}


def set_palette(mode):
    gp.M.name = mode; gp.M.R = gp.RAMPS_N if mode == 'noche' else gp.RAMPS_D
    Pal.cols = gp.palette_flat(); Pal.cache = {}; Pal.where = {}
    for k in ('ink', 'slate', 'mist', 'glass', 'cyan', 'mag', 'vio', 'amb', 'red', 'grn', 'wht'):
        for i, c in enumerate(gp.M.R[k]): Pal.where.setdefault(tuple(c), (k, i))


def near(c):
    c = tuple(int(v) for v in c[:3])
    r = Pal.cache.get(c)
    if r is None:
        r = min(Pal.cols, key=lambda p: (p[0] - c[0]) ** 2 * 2 + (p[1] - c[1]) ** 2 * 3 + (p[2] - c[2]) ** 2)
        Pal.cache[c] = r
    return r


def calmc(c, x):
    """oscurece como calm_left si cae en la zona de iconos."""
    if x >= 380: return near(c)
    a = (1 - max(0, x) / 380) ** 1.4 * .62
    return near(mix(c, R('ink', 0), a))


def fogc(c, Z, y=0.0, k=1.0):
    return mix(c, gp.haze_col(Z), gp.fogk(Z, y) * k)


def ramp_shift(c, d):
    k, i = Pal.where.get(tuple(c), (None, None))
    if k is None: return c
    rr = gp.M.R[k]
    return tuple(rr[max(0, min(len(rr) - 1, i + d))])


# =====================================================================================
# 3. CAPAS DINAMICAS
# =====================================================================================
class Dyn:
    """lienzo dinamico con su propio z: se compone contra el z-buffer estatico."""
    def __init__(s):
        s.img = Image.new('RGB', (W, H)); s.z = Image.new('F', (W, H), 1e9)
        s.d = ImageDraw.Draw(s.img); s.dz = ImageDraw.Draw(s.z)

    def poly(s, pts, col, z):
        pts = [(round(x), round(y)) for x, y in pts]
        s.d.polygon(pts, fill=col); s.dz.polygon(pts, fill=float(z))

    def line(s, a, b, col, z, w=1):
        a = (round(a[0]), round(a[1])); b = (round(b[0]), round(b[1]))
        s.d.line([a, b], fill=col, width=w); s.dz.line([a, b], fill=float(z), width=w)

    def pt(s, x, y, col, z):
        x, y = int(round(x)), int(round(y))
        if 0 <= x < W and 0 <= y < H:
            s.img.putpixel((x, y), col); s.z.putpixel((x, y), float(z))

    def compose(s, frame, zbuf):
        m = ImageMath.lambda_eval(lambda a: (a['d'] < a['z']) * 255, d=s.z, z=zbuf).convert('L')
        return Image.composite(s.img, frame, m)


# ---------------------------------------------------------------- coches
CAR_DIMS = {'car': (4.6, 2.0, 1.5), 'taxi': (4.6, 2.0, 1.5), 'bus': (12.0, 2.6, 3.4), 'truck': (9.0, 2.5, 3.2), 'moto': (2.0, .8, 1.2)}
BODIES = {'car': [(40, 46, 80), (70, 40, 90), (28, 60, 72), (90, 34, 60), (60, 62, 74)], 'taxi': [(200, 160, 40)],
          'bus': [(30, 90, 110)], 'truck': [(110, 104, 120)], 'moto': [(20, 20, 30)]}

# carril: (v, sentido, separacion m, desplazamiento por bucle m (en separaciones), patron de tipos)
LANES = [(-15.0, 1, 64.0, 2, ['car', 'truck']), (-10.0, 1, 52.0, 3, ['car', 'taxi', 'car']), (-5.0, 1, 76.0, 4, ['car', 'car', 'moto', 'taxi']),
         (5.0, -1, 70.0, 4, ['car', 'taxi', 'car', 'bus']), (10.0, -1, 50.0, 3, ['car', 'moto', 'car']), (15.0, -1, 84.0, 2, ['taxi', 'car'])]
U_MIN, U_SPAN = -120.0, 4400.0


def lane_cars(t):
    out = []
    for li, (v, dirn, gap, m, pat) in enumerate(LANES):
        n = int(round(U_SPAN / gap / m)) * m
        span = n * gap
        speed = m * gap / NF                      # en NF fotogramas cada coche ocupa el sitio del m-esimo siguiente
        rj = random.Random(li)
        jit = [rj.uniform(-gap * .3, gap * .3) for _ in range(m)]
        bodies = [rj.choice(BODIES[pat[k]]) for k in range(m)]
        for i in range(n):
            u = U_MIN + ((i * gap + jit[i % m] + dirn * speed * t) % span)
            out.append((u, v, dirn, pat[i % m], bodies[i % m]))
    return out


CROSS = []   # calles transversales: (u centro, carril, sentido)
for iu in range(0, 9):
    uc = iu * (gp.BLK_U + gp.ST_U) + gp.BLK_U + gp.ST_U / 2
    CROSS += [(uc - 3.0, 1), (uc + 3.0, -1)]
V_MIN, V_SPAN = -900.0, 2000.0


def cross_cars(t):
    out = []
    for ci, (u, dirn) in enumerate(CROSS):
        gap, m = 260.0, 2
        n = int(round(V_SPAN / gap / m)) * m; span = n * gap
        speed = m * gap / NF
        rj = random.Random(100 + ci)
        jit = [rj.uniform(-60, 60) for _ in range(m)]
        kinds = [rj.choice(['car', 'car', 'taxi', 'moto']) for _ in range(m)]
        for i in range(n):
            v = V_MIN + ((i * gap + jit[i % m] + dirn * speed * t) % span)
            if -gp.AVE - 4 < v < gp.AVE + 4: continue         # el cruce con la avenida lo ocupan los de la avenida
            out.append((u, v, dirn, kinds[i % m], BODIES[kinds[i % m]][0], 'x'))
    return out


def draw_car(dy, u, v, dirn, kind, body, night, along='u'):
    """coche en perspectiva. along='u' (avenida) o 'x' (calle transversal: se mueve en v)."""
    L, Wd, Hc = CAR_DIMS[kind]
    if along == 'u':
        Z = depth(u, v)
    else:
        Z = depth(u, v)
    if Z < 240 or Z > 6000: return 0
    dist = math.hypot(*L2W(u, v))
    s = FOC / Z
    x_scr = P(u, v)[0]
    if x_scr < -40 or x_scr > W + 40: return 0
    f = gp.fogk(Z, 0)
    if along == 'u':
        a0, a1 = (u, v - Wd / 2), (u, v + Wd / 2)          # cara hacia la camara
        bk = lambda d_: (u - d_ * 1, v)                      # punto 'detras' en direccion a la camara
        fwd = (1, 0)
        corners = [(u, v - Wd / 2), (u + L, v - Wd / 2), (u + L, v + Wd / 2), (u, v + Wd / 2)]
    else:
        corners = [(u - Wd / 2, v), (u + Wd / 2, v), (u + Wd / 2, v + L), (u - Wd / 2, v + L)]
        fwd = (0, 1)
    def cc(c, k=1.0): return calmc(fogc(c, Z, 1.0, k), x_scr)
    # carroceria (solo si se ve de mas de 3 px)
    if s * L >= 3:
        cb = cc(body); ct = cc(gp.mul(body, 1.5)); cs = cc(gp.mul(body, .6))
        if along == 'u':
            dy.poly([P(u, v - Wd / 2, 0), P(u, v + Wd / 2, 0), P(u, v + Wd / 2, Hc), P(u, v - Wd / 2, Hc)], cb, dist)
            side_v = v - Wd / 2 if gp.VC < v else v + Wd / 2
            dy.poly([P(u, side_v, 0), P(u + L, side_v, 0), P(u + L, side_v, Hc), P(u, side_v, Hc)], cs, dist)
        else:
            dy.poly([P(u - Wd / 2, v, 0), P(u + Wd / 2, v, 0), P(u + Wd / 2, v, Hc), P(u - Wd / 2, v, Hc)], cb, dist)
            dy.poly([P(u - Wd / 2, v, 0), P(u - Wd / 2, v + L, 0), P(u - Wd / 2, v + L, Hc), P(u - Wd / 2, v, Hc)], cs, dist)
        dy.poly([P(*corners[0], Hc), P(*corners[1], Hc), P(*corners[2], Hc), P(*corners[3], Hc)], ct, dist)
        if kind == 'bus' and s * L > 8:
            for k in range(1, 6):
                xx, yy = P(u + k * 1.9, v - Wd / 2 if gp.VC < v else v + Wd / 2, Hc * .7)
                dy.pt(xx, yy, cc(R('amb', 3), .5), dist - .1)
    # luces del lado de la camara y estela de larga exposicion detras del coche
    if along == 'u':
        toward = dirn < 0
        lights = [(u, v - Wd / 2 + .3), (u, v + Wd / 2 - .3)] if kind != 'moto' else [(u, v)]
        trail_dir = -1 if not toward else 1          # se aleja: la estela queda hacia la camara
        trail_from = u if not toward else u + L
    else:
        toward = dirn < 0
        lights = [(u - Wd / 2 + .2, v), (u + Wd / 2 - .2, v)] if kind != 'moto' else [(u, v)]
        trail_dir = -dirn; trail_from = v if dirn > 0 else v + L
    if night:
        lamp = R('red', 3) if not toward else (R('wht', 1) if kind != 'taxi' else R('amb', 3))
        ramp = [R('red', 2), R('red', 1), R('red', 0), R('ink', 3)] if not toward else [R('wht', 1), R('wht', 0), R('mist', 2), R('mist', 1)]
        tl = 60.0 if along == 'u' else 16.0
        n = 10
        for (lu, lv) in lights:
            for k in range(n):
                a_ = trail_from + trail_dir * tl * k / n; b_ = trail_from + trail_dir * tl * (k + 1) / n
                if along == 'u': pa, pb = P(a_, lv, .6), P(b_, lv, .6)
                else: pa, pb = P(lu, a_, .6), P(lu, b_, .6)
                col = cc(ramp[min(3, k * 4 // n)], .55)
                dy.line(pa, pb, col, dist + .05, w=1 if s < 2.2 else 2)
            xx, yy = P(lu, lv, .7) if along == 'u' else P(lu, lv if dirn < 0 else lv, .7)
            dy.pt(xx, yy, cc(lamp, .4), dist - .2)
            # reflejo en el asfalto mojado (estela vertical corta)
            for k in range(1, 1 + min(6, int(2 + s * 2.5))):
                if k % 2 == 0 or s < 1: dy.pt(xx, yy + k, cc(ramp[min(3, 1 + k // 2)], .6), dist + .1)
        if toward and s > .8:      # haz de los faros sobre el asfalto
            for k in range(1, 6):
                if along == 'u':
                    xx, yy = P(u - k * 1.8, v, 0)
                    dy.pt(xx, yy, cc(R('mist', 1) if k < 3 else R('slate', 2), .5), dist + .1)
    else:
        lamp = R('red', 1) if not toward else R('mist', 2)
        for (lu, lv) in lights:
            xx, yy = P(lu, lv, .7)
            dy.pt(xx, yy, cc(lamp, .6), dist - .2)
    return 1


# ---------------------------------------------------------------- tren
def rail_ext():
    r = list(gp.RAIL)
    (u0, v0), (u1, v1) = r[0], r[1]
    d = math.hypot(u1 - u0, v1 - v0); du, dv = (u0 - u1) / d, (v0 - v1) / d
    pre = [(u0 + du * k * 20, v0 + dv * k * 20) for k in range(20, 0, -1)]
    pts = pre + r
    cum = [0.0]
    for i in range(1, len(pts)): cum.append(cum[-1] + math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]))
    return pts, cum


RPTS, RCUM = rail_ext()
RLEN = RCUM[-1]


def rail_at(s):
    s = max(0.0, min(RLEN - 1e-6, s))
    lo, hi = 0, len(RCUM) - 1
    while hi - lo > 1:
        mid = (lo + hi) // 2
        if RCUM[mid] <= s: lo = mid
        else: hi = mid
    t = (s - RCUM[lo]) / (RCUM[hi] - RCUM[lo])
    (ua, va), (ub, vb) = RPTS[lo], RPTS[hi]
    nx, ny = -(vb - va), (ub - ua); nl = math.hypot(nx, ny)
    return ua + (ub - ua) * t, va + (vb - va) * t, nx / nl, ny / nl


TRAINS = [(-2.4, 1, 6), (2.4, -1, 4)]   # via (desplazamiento lateral), sentido, convoyes en la via
TRAIN_LEN = 120.0


def trains(t):
    out = []
    for ti, (o, dirn, k) in enumerate(TRAINS):
        sp = RLEN / k
        for j in range(k):
            s0 = (j * sp + ti * sp * .37 + dirn * (sp / NF) * t) % RLEN
            out.append((s0, o, dirn))
    return out


def draw_train(dy, s0, o, dirn, night):
    Y = 20.0; th = 4.6; tw = 3.4
    n = 15
    seg = TRAIN_LEN / n
    drawn = 0
    for k in range(n):
        sa = s0 + k * seg; sb = sa + seg * .92
        if sa < 0 or sb > RLEN: continue
        ua, va, nx, ny = rail_at(sa); ub, vb, _, _ = rail_at(sb)
        Zm = depth((ua + ub) / 2, (va + vb) / 2)
        if Zm < 250: continue
        dist = math.hypot(*L2W((ua + ub) / 2, (va + vb) / 2)) - 6
        xs = P(ua, va, Y)[0]
        if xs < -30 or xs > W + 30: continue
        drawn = 1
        def cc(c, kk=1.0): return calmc(fogc(c, Zm, 20, kk), xs)
        C0 = (ua + nx * (o - tw / 2), va + ny * (o - tw / 2)); C1 = (ua + nx * (o + tw / 2), va + ny * (o + tw / 2))
        D0 = (ub + nx * (o - tw / 2), vb + ny * (o - tw / 2)); D1 = (ub + nx * (o + tw / 2), vb + ny * (o + tw / 2))
        Ta, Tb = (C0, D0) if math.hypot(*L2W(*C0)) < math.hypot(*L2W(*C1)) else (C1, D1)
        dy.poly([P(*Ta, Y + .3), P(*Tb, Y + .3), P(*Tb, Y + th), P(*Ta, Y + th)], cc((150, 160, 186)), dist)
        dy.poly([P(*C0, Y + th), P(*D0, Y + th), P(*D1, Y + th), P(*C1, Y + th)], cc((190, 200, 220)), dist)
        if night or True:
            wc = R('cyan', 3) if k % 5 != 4 else R('amb', 3)
            if k % 5 != 2:
                qa = Ta; qb = (Ta[0] + (Tb[0] - Ta[0]) * .8, Ta[1] + (Tb[1] - Ta[1]) * .8)
                dy.poly([P(*qa, Y + 1.8), P(*qb, Y + 1.8), P(*qb, Y + 3.4), P(*qa, Y + 3.4)], cc(wc if night else R('mist', 2), .5), dist - .1)
        dy.line(P(*Ta, Y + 1.0), P(*Tb, Y + 1.0), cc(R('mag', 2), .5), dist - .1)
    # cabeza (faro) y estela de luz detras del convoy
    if drawn and night:
        head = s0 + TRAIN_LEN if dirn > 0 else s0
        u, v, nx, ny = rail_at(head)
        if 0 < head < RLEN:
            x, y = P(u + nx * o, v + ny * o, Y + 1.6); Zh = depth(u, v)
            dy.pt(x, y, calmc(fogc(R('wht', 1), Zh, 20, .4), x), math.hypot(*L2W(u, v)) - 7)
        tail = s0 if dirn > 0 else s0 + TRAIN_LEN
        for k in range(10):
            sa = tail - dirn * k * 7; sb = sa - dirn * 7
            if not (0 < sa < RLEN and 0 < sb < RLEN): break
            ua, va, nx, ny = rail_at(sa); ub, vb, _, _ = rail_at(sb)
            Zm = depth(ua, va); dist = math.hypot(*L2W(ua, va)) - 5
            col = [R('mag', 2), R('mag', 1), R('mag', 0), R('vio', 0)][min(3, k * 4 // 10)]
            pa, pb = P(ua + nx * o, va + ny * o, Y + 1.0), P(ub + nx * o, vb + ny * o, Y + 1.0)
            dy.line(pa, pb, calmc(fogc(col, Zm, 20, .5), pa[0]), dist)
    return drawn


# ---------------------------------------------------------------- coches voladores
FLY_M = ["...xxxx....", ".xxccxxxxx.", "xxxxxxxxxxx", ".nnnnnnnnn.", "..h.h.h.h..", "...h...h..."]
FLY_S = ["..xxx..", "xxcxxxx", ".nnnnn.", "..h.h.."]
FLY_T = ["xxx", "nnn"]
# trayectorias en coordenadas del mundo (u, v, altura): de A a B en un bucle; fase y neon
def _fp(x, Z, alt):
    u, v = gp.screen_to_local(x, Z); return (u, v, alt)


# trayectorias definidas en pantalla (x, distancia, altura): los extremos quedan fuera de cuadro,
# perdidos en la niebla o tapados por una torre, asi el salto del bucle nunca se ve
FLYERS = [
    (_fp(1100, 330, 170), _fp(720, 7000, 220), .00, 'cyan', 1),    # se aleja por encima de la via
    (_fp(560, 7000, 160), _fp(620, 230, 120), .45, 'mag', 1),      # viene hacia la camara
    (_fp(540, 250, 70), _fp(705, 7000, 90), .70, 'cyan', 1),       # sobre la avenida
    (_fp(700, 8000, 380), _fp(1150, 900, 420), .20, 'mag', 1),     # alto, por encima del horizonte
    (_fp(1050, 1200, 450), _fp(820, 9000, 360), .60, 'cyan', 1),
    (_fp(1000, 900, 120), _fp(560, 900, 120), .30, 'mag', 1),      # cruza y se esconde tras la torre SISTEMA
    (_fp(1000, 1150, 200), _fp(450, 1150, 200), .85, 'cyan', 1),   # cruza y se esconde tras la torre CPU
]


def flyers(t):
    out = []
    for fi, (A, B, ph, neon, k) in enumerate(FLYERS):
        fr = (t / NF * k + ph) % 1.0
        u = A[0] + (B[0] - A[0]) * fr; v = A[1] + (B[1] - A[1]) * fr; y = A[2] + (B[2] - A[2]) * fr
        x0, _ = P(A[0], A[1], A[2]); x1, _ = P(B[0], B[1], B[2])
        out.append((u, v, y, neon, 1 if x1 > x0 else -1, fi))
    return out


def draw_flyer(dy, u, v, y, neon, facing, fi, t, night):
    X, Z = L2W(u, v)
    if Z < 150: return 0
    x, yy = gp.proj(X, y, Z)
    if x < -20 or x > W + 20 or yy < 18 or yy > H + 10: return 0
    s = FOC / Z
    dist = math.hypot(X, Z)
    spr = FLY_M if s > .6 else (FLY_S if s > .2 else FLY_T)
    hgt = len(spr); wdt = len(spr[0])
    f = gp.fogk(Z, y) * .8
    nr = gp.M.R[neon]
    def cc(c, k=1.0): return calmc(mix(c, gp.haze_col(Z), f * k), x)
    pal = {'x': cc(R('slate', 2)), 'c': cc(R('cyan', 3), .5), 'n': cc(nr[2] if night else nr[1], .4), 'h': cc(nr[0], .7)}
    x0 = round(x) - wdt // 2; y0 = round(yy) - hgt // 2
    for j, row in enumerate(spr):
        for i, ch in enumerate(row):
            if ch == '.': continue
            if ch == 'h' and not night: continue
            ii = i if facing > 0 else wdt - 1 - i
            dy.pt(x0 + ii, y0 + j, pal[ch], dist)
    # contorno superior de luz (borde) y luces de posicion parpadeantes (1 Hz, fases distintas)
    on = ((t + fi * 3) // 4) % 2 == 0
    front = x0 + (wdt - 1 if facing > 0 else 0); rear = x0 + (0 if facing > 0 else wdt - 1)
    yl = y0 + (1 if hgt > 2 else 0)
    dy.pt(front, yl, cc(R('wht', 1), .4), dist - .1)
    dy.pt(rear, yl, cc(R('red', 2) if on else R('red', 0), .4), dist - .1)
    return 1


# ---------------------------------------------------------------- drones, baliza, lluvia
DRONES = [(548, 150, 'UPD 12', 'amb', None, 0), (806, 150, 'SRV 1', 'red', 'no', 1), (470, 104, 'SYNC', 'grn', 'ok', 2),
          (610, 70, None, None, None, 3), (720, 128, None, None, None, 4), (300, 160, None, None, None, 5),
          (830, 96, None, None, None, 6), (930, 150, None, None, None, 7)]
TAGS = {}


def draw_drones(fr, t):
    px = fr.load()
    for (cx, cy, lab, acc, ic, i) in DRONES:
        a = 2 * math.pi * (t / NF + i * .13)
        x = round(cx + 9 * math.sin(a)); y = round(cy + 4 * math.sin(2 * a))
        for j, row in enumerate(gp.DRONE):
            for k, ch in enumerate(row):
                if ch == 'x' and 0 <= x + k < W and 0 <= y + j < H:
                    px[x + k, y + j] = calmc(R('slate', 3) if j == 0 else R('ink', 3), x)
        on = ((t + i * 2) // 4) % 2 == 0
        px[x + 3, y + 3] = R('red', 2) if on else R('red', 0)
        if lab:
            key = (lab, gp.M.name)
            if key not in TAGS: TAGS[key] = gp.tag(lab, gp.rp(acc), ic)
            im = TAGS[key]
            for j in range(4, 8): px[x + 3, y + j] = R('slate', 1)
            tx = x + 3 - im.width // 2
            fr.paste(im, (tx, y + 8), im)


def beacon_pts(base, blds):
    pts = []
    u, v = gp.TOWER
    bx, _ = P(u, v, 0); _, sa = P(u, v, 520 + 60)
    pts.append((round(bx), round(sa) - 1, 0, 24))
    bp = base.load()
    for i, (u0, v0, u1, v1, h, neon, dist, Zb) in enumerate(blds):
        if h > 120 and FOC / Zb > .25:
            au, av = (u0 + u1) / 2, (v0 + v1) / 2
            xa, _ = P(au, av, h); _, yb = P(au, av, h + 14)
            x, y = int(round(xa)), int(round(yb - 1))
            if 0 <= x < W and 0 <= y < H and Pal.where.get(bp[x, y], ('', 0))[0] == 'red':
                pts.append((x, y, (i * 7) % 32, 32))
    return pts


def draw_beacons(fr, t, pts):
    px = fr.load()
    for (x, y, ph, per) in pts:
        k = (t + ph) % per
        lvl = 3 if k < 3 else (2 if k < 8 else 1)      # pulso lento: destello de 3 fotogramas y se apaga despacio
        px[x, y] = R('red', lvl)
        if lvl == 3:                                    # halo escalonado de 1 px
            for dx, dy_ in ((1, 0), (-1, 0), (0, -1), (0, 1)):
                if 0 <= x + dx < W and 0 <= y + dy_ < H: px[x + dx, y + dy_] = R('red', 1)


RAIN = []


def make_rain(n_far, n_near):
    rnd = random.Random(1); RAIN.clear()
    for _ in range(n_far): RAIN.append((rnd.randrange(W), rnd.uniform(0, H - 16), 1, 3))
    for _ in range(n_near): RAIN.append((rnd.randrange(W), rnd.uniform(0, H - 16), 2, 6))


def draw_rain(fr, t, ground, night):
    d = ImageDraw.Draw(fr)
    span = H - 16
    for (x, y0, k, ln) in RAIN:
        y = 16 + (y0 + k * span * t / NF) % span
        if k == 1:
            c = R('slate', 1) if y < gp.HY else R('slate', 2)
            if x < 380: c = R('slate', 0) if x < 200 else R('slate', 1)
            d.line([(x, y), (x, y + 2)], fill=c)
        else:
            c = R('slate', 3) if x >= 260 else R('slate', 1)
            d.line([(x, y), (x - 1, y + 5)], fill=c)
            d.point((x - 1, y + 5), fill=R('mist', 1) if x >= 260 else R('slate', 2))
    # salpicaduras: cada una dura 2 fotogramas en su fase
    rnd = random.Random(2); gpx = ground.load()
    for i in range(700 if night else 250):
        x, y = rnd.randrange(1, W - 1), rnd.randrange(gp.HY + 40, H - 1)
        ph = rnd.randrange(NF)
        if (t - ph) % NF < 2 and gpx[x, y] > 0:
            d.point((x - 1, y), fill=R('slate', 3)); d.point((x + 1, y), fill=R('slate', 3)); d.point((x, y - 1), fill=R('mist', 1))


# ---------------------------------------------------------------- carteles dinamicos
def periodic_series(n, seed, base, var):
    rnd = random.Random(seed)
    amps = [(rnd.uniform(0, var), rnd.randint(1, 9), rnd.uniform(0, 6.28)) for _ in range(6)]
    return [max(0, min(1, base + sum(a * math.sin(2 * math.pi * k * i / n + p) for a, k, p in amps) / 2)) for i in range(n)]


NET_DN = periodic_series(NF, 9, .45, .5)
NET_UP = periodic_series(NF, 5, .18, .2)


def s_reloj_t(t, hora, fecha):
    acc = gp.rp('cyan'); w, h = 100, 58
    im, d = gp.frame(w, h, acc)
    hh = hora if (t // 4) % 2 == 0 else hora.replace(':', ' ')          # dos puntos a 1 Hz
    gp.led_text(d, 8, 8, hh, acc)
    pos = (t * 28 // NF) % 28
    for k in range(28):
        d.point((10 + k * 3, 30), fill=acc[3] if k == pos else (acc[2] if k < pos else acc[0]))
    mg = gp.rp('mag')
    dia_, resto = fecha.split(' ', 1)
    gp.txt(d, 10, 34, dia_, mg[3]); gp.txt(d, 10 + 7 * 4, 34, resto, acc[3])
    for xx in range(6, w - 6, 2): d.point((xx, 44), fill=gp.rp('slate')[1])
    am = gp.rp('amb')
    gp.glyph(d, 'tri', 8, 47, am[2] if (t // 8) % 2 == 0 else am[1])
    x = gp.txt(d, 13, 47, '22:00', am[3], 'M'); gp.txt(d, x + 3, 47, 'COPIA DATOS', gp.rp('mist')[2], 'M'); gp.txt(d, w - 15, 47, '+2', acc[2], 'M')
    return im


def s_cpu_t(t):
    acc = gp.rp('mag'); w, h = 108, 50
    im, d = gp.frame(w, h, acc, 'CPU')
    base = [.62, .35, .91, .41, .23, .57, .74, .30]
    # cada nucleo cambia a saltos (cada 8 fotogramas = 1 s), con periodo que divide el bucle
    loads = []
    for k, b in enumerate(base):
        step = (t // 8)
        loads.append(max(.05, min(.98, b + .18 * math.sin(2 * math.pi * (step * (k % 3 + 1)) / 12 + k))))
    tot = int(round(sum(loads) / len(loads) * 100))
    s_ = f'{tot}%'
    gp.txt(d, w - 7 - gp.twidth(s_), 10, s_, acc[3]); gp.txt(d, 7, 11, '8 NUCLEOS 3.8GHZ', gp.rp('mist')[2], 'M')
    for k, l in enumerate(loads):
        cx = 11 + k * 12; cy = 25
        gp.ring(d, cx, cy, l, gp.load_ramp(l), gp.rp('ink')[3])
        d.point((cx, cy), fill=gp.load_ramp(l)[1])
        gp.txt(d, cx - 3, 33, str(int(l * 100)), gp.rp('mist')[3] if l < .85 else gp.rp('red')[3], 'M')
    hist = periodic_series(NF, 4, .47, .5)
    for k in range(48):
        v = hist[(k + t) % NF]
        hh = 1 + int(v * 5); c = gp.load_ramp(v)
        d.line([(6 + k * 2, 45), (6 + k * 2, 45 - hh + 1)], fill=c[0]); d.point((6 + k * 2, 45 - hh + 1), fill=c[2])
    return im


def s_net_t(t):
    acc = gp.rp('cyan'); w, h = 84, 46
    im, d = gp.frame(w, h, acc, 'NET')
    mg = gp.rp('mag')
    for k in range(4):
        d.rectangle([w - 18 + k * 3, 6 - k, w - 17 + k * 3, 6], fill=acc[2] if k < 3 else acc[0])
    gx, gy, gw, gh = 6, 29, w - 12, 12
    cur_dn = NET_DN[(t + gw - 1) % NF]; cur_up = NET_UP[(t + gw - 1) % NF]
    gp.glyph(d, 'dn', 7, 13, acc[3]); gp.txt(d, 14, 11, f'{cur_dn * 9.4:.1f}', acc[3]); gp.txt(d, 37, 13, 'MB/S', acc[2], 'M')
    gp.glyph(d, 'up', 7, 22, mg[3]); gp.txt(d, 14, 20, f'{cur_up * 1.8:.1f}', mg[3]); gp.txt(d, 37, 22, 'MB/S', mg[2], 'M')
    gp.txt(d, 58, 13, 'IP OK', gp.rp('grn')[2], 'M'); gp.txt(d, 58, 22, '12MS', gp.rp('mist')[2], 'M')
    for xx in range(gx, gx + gw, 4):
        for yy in range(gy, gy + gh, 4): d.point((xx, yy), fill=gp.rp('ink')[3])
    for k in range(gw):
        dn = NET_DN[(t + k) % NF]; up = NET_UP[(t + k) % NF]          # la grafica avanza 1 px por fotograma
        top = gy + gh - 1 - int(dn * (gh - 1))
        for yy in range(top + 1, gy + gh):
            d.point((gx + k, yy), fill=acc[0] if yy > top + 1 or (k + t) % 2 else acc[1])
        d.point((gx + k, top), fill=acc[2])
        d.point((gx + k, gy + gh - 1 - int(up * (gh - 1))), fill=mg[2])
    d.point((gx + gw - 1, gy + gh - 1 - int(cur_dn * (gh - 1))), fill=gp.rp('wht')[1])
    return im


def repaint_sign(fr, name, im, smap):
    sid, mp = smap[name]
    px = fr.load(); ip = im.load()
    for (x, y), (i, j, isback) in mp.items():
        if 0 <= x < W and 0 <= y < H:
            if isback and 5 <= i <= im.width - 6 and 5 <= j <= im.height - 6: c = R('ink', 0)
            else: c = ip[i, j]
            if len(c) == 4:
                if c[3] == 0: continue
                c = c[:3]
            px[x, y] = c


TIP = 'CONSEJO HAZ COMMIT A MENUDO  +  '      # 32 caracteres x 12 px = 384 px = 4 px/fotograma
SCR = (372 - 136 // 2 + 6, 58 - 22 // 2 - 1, 136, 22)


def draw_marquee(fr, t):
    sx0, sy0, sw, shh = SCR
    scr = Image.new('RGB', (sw, shh), R('ink', 0)); d = ImageDraw.Draw(scr)
    for y in range(4, shh - 4, 2):
        for x in range(3, sw - 3, 2): d.point((x, y), fill=R('ink', 2))
    strip = Image.new('RGBA', (len(TIP) * 12 * 3, 14), (0, 0, 0, 0)); sd = ImageDraw.Draw(strip)
    gp.led_text(sd, 0, 0, TIP * 3, gp.rp('amb'), pitch=2, dot=1, show_off=False)
    off = (4 * t) % (len(TIP) * 12)
    scr.paste(strip, (3 - off, 4), strip)
    d.rectangle([0, 0, 2, shh - 1], fill=R('ink', 0)); d.rectangle([sw - 3, 0, sw - 1, shh - 1], fill=R('ink', 0))
    fr.paste(scr.crop((1, 1, sw - 1, shh - 1)), (sx0 + 1, sy0 + 1))


# =====================================================================================
# 4. VENTANAS: horario de encendidos/apagados por ventana (periodico en el bucle)
# =====================================================================================
ALT = {'amb': ('mist', 'cyan'), 'mist': ('amb', 'cyan'), 'cyan': ('mist', 'amb'), 'wht': ('amb', 'cyan')}


def window_schedule(wins, calma, day=False):
    """devuelve {id: lista de 96 estados} solo para las ventanas que cambian.
    estado: (encendida, variante de color 0/1/2)."""
    rnd = random.Random(77)
    sched = {}
    p_tog_n = (.05 if not day else .025) * calma      # ventanas cercanas
    p_tog_f = (.02 if not day else .01) * calma       # puntos lejanos (si cambian muchos parece ruido)
    p_col = .025 * calma
    for wid0, (on0, nearw) in enumerate(wins):
        wid = wid0 + 1
        r = rnd.random(); r2 = rnd.random()
        a = rnd.randrange(NF); dur = rnd.randint(16, 64); flick = rnd.random() < .45
        alt = 1 + (rnd.random() < .5)
        if r < (p_tog_n if nearw else p_tog_f):
            st = []
            for t in range(NF):
                k = (t - a) % NF
                inside = k < dur
                on = (not on0) if inside else on0
                # parpadeo al encender (2 fotogramas encendida, 2 apagada = 2 Hz, nunca mas rapido)
                if flick:
                    turn_on_at = 0 if not on0 else dur        # momento en que pasa a encendida
                    kk = (k - turn_on_at) % NF
                    if kk in (2, 3) and on: on = False
                st.append((on, 0))
            sched[wid] = st
        elif r2 < p_col and on0:
            st = []
            for t in range(NF):
                k = (t - a) % NF
                st.append((True, alt if k < dur else 0))
            sched[wid] = st
    return sched


def window_pixels(ID, ids):
    data = ID.get_flattened_data() if hasattr(ID, 'get_flattened_data') else ID.getdata()
    want = set(ids); out = {}
    for idx, v in enumerate(data):
        if v in want:
            out.setdefault(v, []).append((idx % W, idx // W))
    return out


def recolor(c, variant):
    k, i = Pal.where.get(tuple(c), (None, None))
    if k is None or k not in ALT or variant == 0: return c
    nk = ALT[k][variant - 1]
    rr = gp.M.R[nk]
    return tuple(rr[min(len(rr) - 1, max(0, i if k != 'wht' else 3))])


# =====================================================================================
# 5. COMPOSICION DE UN FOTOGRAMA
# =====================================================================================
class G:   # estado global de la animacion (se hereda en los procesos con fork)
    pass


def led_grid_cached(big):
    if not hasattr(G, 'ledpat'):
        row0 = Image.new('L', (W * 2, 1)); row0.putdata([255 if x % 2 == 0 else 196 for x in range(W * 2)])
        row1 = Image.new('L', (W * 2, 1)); row1.putdata([196 if x % 2 == 0 else 150 for x in range(W * 2)])
        pat = Image.new('L', (W * 2, H * 2))
        for y in range(H * 2): pat.paste(row0 if y % 2 == 0 else row1, (0, y))
        G.ledpat = Image.merge('RGB', (pat, pat, pat))
        G.ledbig = G.LED.resize((W * 2, H * 2), Image.NEAREST)
    return Image.composite(ImageChops.multiply(big, G.ledpat), big, G.ledbig)


def compose(t, night=True, darkness=None, hour=None, tc=0):
    """devuelve (lienzo 960x600, imagen final 1920x1200, contadores de elementos)."""
    stats = {}
    if darkness is None:
        fr = G.base.copy()
    else:   # ciclo: fundido tramado entre el fondo de dia y el de noche (sin ventanas)
        m = G.thr.point(lambda v, d_=darkness: 255 if v < d_ * 255 else 0)
        fr = Image.composite(G.B_n, G.B_d, m)
        fr = warm_sky(fr, tc)
    px = fr.load()
    # --- ventanas
    if darkness is None:
        apx, bpx = G.A.load(), G.Bimg.load()
        nchg = 0
        for wid, st in G.sched.items():
            on, var = st[t % NF]
            on0 = G.wins[wid - 1][0]
            if on == on0 and var == 0: continue
            nchg += 1
            for (x, y) in G.wpix.get(wid, ()):
                c = apx[x, y] if on else bpx[x, y]
                if on and var: c = recolor(c, var)
                px[x, y] = c
        stats['ventanas_cambiadas'] = nchg
    else:
        apx = G.A.load()
        for wid, pl in G.wpix_all.items():
            on = G.wins[wid - 1][0] and G.tau[wid] < darkness
            st = G.sched.get(wid)
            if st and darkness > .99: on, var = st[t % NF]
            else: var = 0
            if on:
                for (x, y) in pl:
                    px[x, y] = recolor(apx[x, y], var) if var else apx[x, y]
    lit = night if darkness is None else darkness > .45
    # --- neones que titilan
    for (pl, ev) in G.neons:
        if ((t - ev) % NF) in (0, 1, 5):
            for (x, y, c) in pl: px[x, y] = ramp_shift(c, -2)
    # --- carteles dinamicos
    hora = hour or G.hora
    for nm, im in (('reloj', s_reloj_t(t, hora, G.fecha)), ('cpu', s_cpu_t(t)), ('net', s_net_t(t))):
        if nm in G.smap: repaint_sign(fr, nm, im, G.smap)
    draw_marquee(fr, t)
    # --- capa dinamica con oclusion: coches, tren, voladores
    dy = Dyn(); items = []
    for c in lane_cars(t): items.append((math.hypot(*L2W(c[0], c[1])), 'car', c))
    for c in cross_cars(t): items.append((math.hypot(*L2W(c[0], c[1])), 'xcar', c))
    for tr in trains(t): items.append((math.hypot(*L2W(*rail_at(tr[0])[:2])), 'train', tr))
    for fl in flyers(t): items.append((math.hypot(*L2W(fl[0], fl[1])), 'fly', fl))
    items.sort(key=lambda o: -o[0])
    cnt = {'coches': 0, 'trenes': 0, 'voladores': 0}
    for _, k, o in items:
        if k == 'car': cnt['coches'] += draw_car(dy, o[0], o[1], o[2], o[3], o[4], lit)
        elif k == 'xcar': cnt['coches'] += draw_car(dy, o[0], o[1], o[2], o[3], o[4], lit, along='x')
        elif k == 'train': cnt['trenes'] += draw_train(dy, o[0], o[1], o[2], lit)
        else: cnt['voladores'] += draw_flyer(dy, o[0], o[1], o[2], o[3], o[4], o[5], t, lit)
    fr = dy.compose(fr, G.Zb)
    stats.update(cnt)
    draw_beacons(fr, t, G.beacons)
    draw_drones(fr, t)
    draw_rain(fr, t, G.ground, lit)
    big = fr.resize((W * 2, H * 2), Image.NEAREST)
    big = led_grid_cached(big)
    gp.draw_bar(big, hora, G.fecha); gp.desktop_icons(big)
    return fr, big, stats


# ---------------------------------------------------------------- ciclo
def cycle_curve(t, n):
    """oscuridad 0..1 y hora para el ciclo acelerado (amanecer -> dia -> atardecer -> noche)."""
    f = t / n
    def sm(x): x = max(0.0, min(1.0, x)); return x * x * (3 - 2 * x)
    if f < .25: d = 1 - sm(f / .22)                 # amanecer
    elif f < .45: d = 0.0                            # dia
    elif f < .70: d = sm((f - .45) / .22)            # atardecer
    else: d = 1.0                                    # noche
    keys = [(0, 5.0), (.25, 8.5), (.45, 17.0), (.70, 21.5), (1.0, 29.0)]   # hora del reloj por tramos
    for (fa, ha), (fb, hb) in zip(keys, keys[1:]):
        if fa <= f <= fb: hour = (ha + (hb - ha) * (f - fa) / (fb - fa)) % 24; break
    hh, mm = int(hour), int((hour % 1) * 60)
    warm = max(0.0, 1 - abs(f - .12) / .12) + max(0.0, 1 - abs(f - .57) / .12)
    return d, f'{hh:02d}:{mm - mm % 5:02d}', min(1.0, warm)


def warm_sky(fr, tc):
    """resplandor calido de amanecer/atardecer en el cielo, tramado (sin colores nuevos)."""
    w = G.warm_t[tc]
    if w < .03: return fr
    m = ImageMath.lambda_eval(lambda a: (a['t'] < a['s'] * w * .9) * 255, t=G.thr, s=G.warm_str).convert('L')
    return Image.composite(G.warm_img, fr, m)


def prepare_warm():
    img = Image.new('RGB', (W, H)); s = Image.new('L', (W, H), 0)
    d = ImageDraw.Draw(img); ds = ImageDraw.Draw(s)
    sky = ImageMath.lambda_eval(lambda a: (a['z'] > 5e8) * 255, z=G.Zb).convert('L')
    sp = s.load()
    for y in range(gp.HY - 80, gp.HY + 4):
        k = (y - (gp.HY - 80)) / 84
        c = R('vio', 0) if k < .45 else (R('mag', 0) if k < .8 else R('amb', 0))
        d.line([(0, y), (W, y)], fill=c)
        for x in range(W):   # resplandor centrado detras de la torre, se apaga hacia los lados
            hx = math.exp(-((x - 700) / 330) ** 2)
            sp[x, y] = int(255 * min(1.0, k ** 1.3 * (.25 + .75 * hx)) * .8)
    G.warm_img = img; G.warm_str = ImageChops.multiply(s, sky)


# =====================================================================================
# 6. PREPARACION, EXPORTACION DE CAPAS Y VIDEO
# =====================================================================================
def frame_job(args):
    t, kind, outdir = args
    if kind == 'ciclo':
        d, hour, _ = cycle_curve(t, G.nf)
        G.hora = hour
        fr, big, st = compose(t % NF, darkness=d, hour=hour, tc=t)
    else:
        fr, big, st = compose(t % NF, night=(kind == 'noche'))
    big.save(os.path.join(outdir, f'f{t:03d}.png'), compress_level=1)
    if t in (0, 24, 48, 72, 95): fr.save(os.path.join(outdir, f'w{t:03d}.png'))
    return t, st


def prepare(mode, statics):
    set_palette(mode)
    N = statics[(mode, 'N')]; A = statics[(mode, 'A')]['img']; B = statics[(mode, 'B')]['img']
    G.base = N['img']; G.A = A; G.Bimg = B
    G.Zb = N['Zb']; G.ID = N['ID']; G.LED = N['LED']; G.ground = N['G']
    G.wins = N['WINS']
    sp = N['SID'].load(); G.smap = {}
    for nm, (sid, mp) in N['SIGNMAP'].items():   # solo los pixeles del cartel que siguen visibles
        G.smap[nm] = (sid, {k: v for k, v in mp.items() if 0 <= k[0] < W and 0 <= k[1] < H and sp[k] == sid})
    if hasattr(G, 'ledpat'): del G.ledpat
    G.sched = window_schedule(G.wins, CALMA, day=(mode == 'dia'))
    G.wpix = window_pixels(G.ID, list(G.sched.keys()))
    # neones: pixeles brillantes de las aristas de neon que se ven en el fondo
    bp = G.base.load(); kp = N['K'].load(); rnd = random.Random(5); G.neons = []
    for (u0, v0, u1, v1, h, neon, dist, Zb) in N['blds']:
        if not neon or FOC / Zb * h <= 20: continue
        corner = (u0, v0) if gp.VC < v0 else (u0, v1)
        xa, ya = P(*corner, 0); _, yb = P(*corner, h)
        x = int(round(xa)); pl = []
        for y in range(max(0, int(round(yb))), min(H, int(round(ya)) + 1)):
            if 0 <= x < W and kp[x, y] and Pal.where.get(bp[x, y], ('', 0))[0] in ('cyan', 'mag'): pl.append((x, y, bp[x, y]))
        if pl and rnd.random() < .5 * CALMA: G.neons.append((pl, rnd.randrange(NF)))
    G.beacons = beacon_pts(G.base, N['blds'])
    G.hora, G.fecha = ('21:37', 'MAR 10 NOV') if mode == 'noche' else ('13:05', 'MAR 10 NOV')
    make_rain(900 if mode == 'noche' else 450, 160 if mode == 'noche' else 50)


def export_layers(mode, statics, outroot):
    """exporta las capas estaticas como especificacion para el tema QML."""
    od = os.path.join(outroot, mode); os.makedirs(od, exist_ok=True)
    N = statics[(mode, 'N')]; A = statics[(mode, 'A')]['img']; B = statics[(mode, 'B')]['img']
    B.save(os.path.join(od, 'fondo-ventanas-apagadas.png'), optimize=True)
    diff = ImageChops.difference(A, B).convert('L').point(lambda v: 255 if v else 0)
    lit = A.convert('RGBA'); lit.putalpha(diff)
    lit.save(os.path.join(od, 'ventanas-encendidas.png'), optimize=True)
    # ids de ventana en RGB de 24 bits (lo que leeria un shader)
    data = list(N['ID'].get_flattened_data() if hasattr(N['ID'], 'get_flattened_data') else N['ID'].getdata())
    rgb = Image.new('RGB', (W, H)); rgb.putdata([((v >> 16) & 255, (v >> 8) & 255, v & 255) for v in data])
    rgb.save(os.path.join(od, 'ventanas-id.png'), optimize=True)
    zl = Image.new('L', (W, H)); zl.putdata([255 if v > 5e7 else int(min(254, v / 30)) for v in (N['Zb'].get_flattened_data() if hasattr(N['Zb'], 'get_flattened_data') else N['Zb'].getdata())])
    zl.save(os.path.join(od, 'profundidad-8bit.png'), optimize=True)
    N['LED'].save(os.path.join(od, 'mascara-led.png'), optimize=True)
    N['G'].save(os.path.join(od, 'mascara-suelo-mojado.png'), optimize=True)
    sizes = {f: os.path.getsize(os.path.join(od, f)) for f in sorted(os.listdir(od))}
    return sizes


def encode(frames_dir, out, n):
    os.system(f"ffmpeg -y -loglevel error -framerate 8 -i {frames_dir}/f%03d.png -frames:v {n} "
              f"-c:v libx264 -preset slow -crf 16 -pix_fmt yuv420p -movflags +faststart {out}")


def main():
    what = sys.argv[1] if len(sys.argv) > 1 else 'noche'
    kinds = ['noche', 'dia', 'ciclo'] if what == 'todo' else [what]
    t0 = time.time()
    need_modes = set()
    for k in kinds:
        if k in ('noche', 'prueba'): need_modes.add('noche')
        if k == 'dia': need_modes.add('dia')
        if k == 'ciclo': need_modes |= {'noche', 'dia'}
    jobs = [(m, r) for m in sorted(need_modes) for r in 'NAB']
    with Pool(min(len(jobs), os.cpu_count() or 4)) as pool:
        res = pool.map(static_job, jobs)
    statics = {(m, r): o for m, r, o in res}
    print(f'capas estaticas: {time.time() - t0:.1f} s', flush=True)
    report = {}
    for kind in kinds:
        t1 = time.time()
        mode = 'noche' if kind in ('noche', 'prueba', 'ciclo') else 'dia'
        prepare(mode, statics)
        if kind == 'ciclo':
            # fondos sin ventanas de los dos modos + umbral de tramado para el fundido
            G.B_n = statics[('noche', 'B')]['img']; G.B_d = statics[('dia', 'B')]['img']
            G.A = statics[('noche', 'A')]['img']
            rnd = random.Random(3)
            thr = Image.new('L', (W, H)); thr.putdata([int((gp.BAYER[y % 4][x % 4] + .5) * 16) for y in range(H) for x in range(W)])
            G.thr = thr
            G.nf = NF * 2
            G.wpix_all = window_pixels(G.ID, [i + 1 for i, w_ in enumerate(G.wins) if w_[0] or (i + 1) in G.sched])
            G.tau = {i + 1: rnd.random() * .9 + .05 for i in range(len(G.wins))}
            prepare_warm()
            G.warm_t = [cycle_curve(t, G.nf)[2] for t in range(G.nf)]
            set_palette('noche')
            n = G.nf
        else:
            n = NF
        outdir = os.path.join(TMP, kind); shutil.rmtree(outdir, ignore_errors=True); os.makedirs(outdir)
        ts = list(range(n)) if kind != 'prueba' else [0, 24, 48, 72, 95, 96]
        with Pool(os.cpu_count() or 4) as pool:
            sts = pool.map(frame_job, [(t, kind if kind != 'prueba' else 'noche', outdir) for t in ts])
        dt = time.time() - t1
        if kind != 'prueba':
            out = os.path.join(HERE, f'animacion-{kind}.mp4')
            encode(outdir, out, n)
        avg = {k: round(sum(s[k] for _, s in sts) / len(sts), 1) for k in sts[0][1]}
        report[kind] = dict(fotogramas=n, segundos=round(dt, 1), media_en_pantalla=avg,
                            ventanas_registradas=len(G.wins), ventanas_animadas=len(G.sched),
                            pixeles_ventana_animados=sum(len(v) for v in G.wpix.values()))
        if kind in ('noche', 'dia'):
            report[kind]['capas_png_bytes'] = export_layers(mode, statics, os.path.join(HERE, 'capas'))
        print(kind, json.dumps(report[kind], ensure_ascii=False), flush=True)
    if what != 'prueba':
        with open(os.path.join(HERE, 'capas', f'informe-{what}.json'), 'w') as fh:
            json.dump(report, fh, ensure_ascii=False, indent=1)
    print(f'total {time.time() - t0:.1f} s')


if __name__ == '__main__':
    main()
