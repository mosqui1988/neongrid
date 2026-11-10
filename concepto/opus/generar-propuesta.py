#!/usr/bin/env python3
"""NeonGrid · propuesta 'opus': ciudad en perspectiva real (2 puntos de fuga, camara alta).

Lienzo de trabajo 960x600 (1 px logico = 2x2 px en pantalla 1920x1200).
Todo se pinta en RGB y al final se cuantiza a una paleta fija de rampas de 4 tonos;
la niebla y los degradados pasan por un tramado ordenado Bayer 4x4 (sin difuminados).
Los carteles se dibujan pixel a pixel a tamano nativo y se pegan con cizallado por columnas.

Uso:  python generar-propuesta.py [noche|dia|detalle|todo]
Solo depende de Pillow.
"""
import math, random, os, sys
from PIL import Image, ImageDraw, ImageFont, ImageChops, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
# Fuentes para RECONSTRUIR el fondo (el paquete ya trae las capas hechas): Departure Mono, Micro 5 y DotGothic16 (todas OFL).
# Pon su carpeta en NG_FUENTES (ver README, seccion «Reconstruir»).
FONTDIR = os.path.expanduser(os.environ.get('NG_FUENTES', '~/.local/share/fonts/neongrid-build')).rstrip('/') + '/'
FD = ImageFont.truetype(FONTDIR + 'DepartureMono-Regular.otf', 11)   # 5x7, avance 7
FM = ImageFont.truetype(FONTDIR + 'Micro5-Regular.ttf', 10)           # 3/4x5 condensada
FB14 = ImageFont.truetype(FONTDIR + 'DepartureMono-Regular.otf', 14)  # UI a 1x (barra)

W, H = 960, 600
CX, HY, FOC, CAMH = 480, 108, 720.0, 290.0
ANG = math.radians(20)
SA, CA = math.sin(ANG), math.cos(ANG)
Z0 = 420.0
VCAM = 110.0                    # la camara vuela a la derecha de la avenida, mirando hacia ella
X0 = (Z0 * math.sin(ANG) - VCAM) / math.cos(ANG)

# ------------------------------------------------------------------ paleta
RAMPS_N = {
    'ink':   [(5, 6, 14), (10, 12, 26), (16, 20, 40), (24, 30, 56)],
    'slate': [(32, 40, 68), (44, 56, 88), (60, 76, 110), (84, 104, 140)],
    'mist':  [(70, 88, 116), (102, 122, 150), (138, 158, 184), (182, 198, 216)],
    'glass': [(8, 30, 44), (14, 52, 70), (24, 84, 104), (44, 130, 150)],
    'cyan':  [(0, 104, 136), (0, 168, 208), (0, 229, 255), (170, 248, 255)],
    'mag':   [(88, 14, 80), (170, 28, 150), (255, 43, 214), (255, 160, 236)],
    'vio':   [(36, 22, 70), (70, 44, 130), (139, 92, 255), (196, 176, 255)],
    'amb':   [(96, 40, 12), (190, 92, 22), (255, 166, 40), (255, 222, 150)],
    'red':   [(80, 10, 26), (160, 20, 46), (255, 59, 92), (255, 150, 160)],
    'grn':   [(8, 60, 36), (18, 140, 76), (57, 255, 136), (180, 255, 206)],
    'wht':   [(214, 222, 236), (246, 248, 255)],
}
RAMPS_D = dict(RAMPS_N)
RAMPS_D.update({
    'ink':   [(14, 18, 30), (22, 28, 44), (32, 40, 60), (44, 54, 78)],
    'slate': [(54, 64, 88), (68, 80, 106), (84, 98, 124), (104, 120, 146)],
    'mist':  [(92, 106, 128), (112, 126, 148), (134, 148, 168), (160, 172, 190)],
    'glass': [(20, 44, 58), (30, 64, 80), (44, 90, 106), (70, 124, 138)],
})


LITK = {'noche': 1.0, 'dia': .38}


class M:  # modo actual
    name = 'noche'; R = RAMPS_N


def R(n, i): return M.R[n][i]


def mix(a, b, t): return tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(3))
def mul(c, k): return tuple(max(0, min(255, int(v * k))) for v in c)
def clamp(v, a, b): return max(a, min(b, v))


# ------------------------------------------------------------------ camara
def L2W(u, v): return X0 + u * SA + v * CA, Z0 + u * CA - v * SA
def proj(X, Y, Z): return (CX + FOC * X / Z, HY - FOC * (Y - CAMH) / Z)
def P(u, v, y=0.0):
    X, Z = L2W(u, v); return proj(X, y, Z)
def depth(u, v): return L2W(u, v)[1]


UC = (0 - X0) * SA + (0 - Z0) * CA
VC = (0 - X0) * CA - (0 - Z0) * SA


def fogk(Z, y=0.0):
    """niebla por distancia + bruma baja (capas como en la referencia)."""
    f = 1 - math.exp(-max(0.0, Z - 380) / (3300 if M.name == 'noche' else 2600))
    low = math.exp(-max(0.0, y) / 70.0) * min(1.0, Z / 2200) * .38
    return clamp(f * .92 + low, 0, .96)


# ------------------------------------------------------------------ lienzos
class S:
    img = None; d = None; E = None; dE = None; G = None; dG = None; K = None; dK = None


def new_canvases():
    S.img = Image.new('RGB', (W, H)); S.d = ImageDraw.Draw(S.img)
    S.E = Image.new('RGB', (W, H)); S.dE = ImageDraw.Draw(S.E)     # emisivo (para reflejos)
    S.B = Image.new('RGB', (W, H)); S.dB = ImageDraw.Draw(S.B)     # fuentes de halo (neon, carteles, faros)
    S.G = Image.new('L', (W, H), 0); S.dG = ImageDraw.Draw(S.G)     # mascara calle mojada
    S.K = Image.new('L', (W, H), 0); S.dK = ImageDraw.Draw(S.K)     # zonas nitidas (sin tramado)


def poly(pts, col, ground=False, crisp=False, emis=False):
    pts = [(round(x), round(y)) for x, y in pts]
    S.d.polygon(pts, fill=col)
    S.dG.polygon(pts, fill=255 if ground else 0)
    if crisp: S.dK.polygon(pts, fill=255)
    if emis: S.dE.polygon(pts, fill=col)
    if emis is True: S.dB.polygon(pts, fill=col)


def pix(x, y, col, emis=False, crisp=False):
    x, y = int(round(x)), int(round(y))
    if 0 <= x < W and 0 <= y < H:
        S.img.putpixel((x, y), col); S.G.putpixel((x, y), 0)
        if emis: S.E.putpixel((x, y), col)
        if emis is True: S.B.putpixel((x, y), col)
        if crisp: S.K.putpixel((x, y), 255)


# ------------------------------------------------------------------ cielo
def vnoise(gw, gh, seed):
    rnd = random.Random(seed)
    im = Image.new('L', (gw, gh))
    im.putdata([rnd.randint(0, 255) for _ in range(gw * gh)])
    return im


def draw_sky():
    night = M.name == 'noche'
    top, mid, hor = ((4, 5, 13), (16, 20, 38), (46, 50, 84)) if night else ((30, 36, 52), (52, 62, 84), (98, 110, 132))
    for y in range(HY + 4):
        t = y / (HY + 3)
        c = mix(top, mid, t / .6) if t < .6 else mix(mid, hor, (t - .6) / .4)
        S.d.line([(0, y), (W, y)], fill=c)
    # nubes: ruido por octavas, bandas horizontales (estiradas como un cielo de tormenta)
    acc = Image.new('L', (W, HY + 4), 0)
    for k, (gw, gh, a) in enumerate(((10, 3, .5), (24, 6, .3), (60, 14, .2))):
        n = vnoise(gw, gh, 70 + k).resize((W, HY + 4), Image.BICUBIC)
        acc = Image.blend(acc, n, a / (a + (0 if k == 0 else .6)) if k else 1.0)
    cl = acc.load(); px = S.img.load()
    cloud = (40, 46, 74) if night else (120, 130, 150)
    dark = (8, 9, 20) if night else (40, 48, 66)
    for y in range(HY + 4):
        for x in range(W):
            n = cl[x, y] / 255
            c = px[x, y]
            if n > .55: c = mix(c, cloud, min(1, (n - .55) * 2.2) * (.35 + .65 * y / HY))
            elif n < .4: c = mix(c, dark, (.4 - n) * 1.5)
            px[x, y] = c
    # resplandor de la ciudad bajo las nubes (magenta/cian)
    if night:
        for y in range(HY - 56, HY + 4):
            t = ((y - (HY - 56)) / 60) ** 1.6
            for x in range(0, W, 1):
                g = math.exp(-((x - 640) / 300) ** 2) * .55 + math.exp(-((x - 880) / 160) ** 2) * .30 + .12
                px[x, y] = mix(px[x, y], mix((40, 104, 136), (112, 44, 120), clamp((x - 560) / 400, 0, 1)), g * t * .8)


# ------------------------------------------------------------------ ciudad
MATS = {
    'conc':  dict(front=('slate', 1), side=('ink', 3), roof=('slate', 0), win=('wht', 'amb')),
    'dark':  dict(front=('ink', 3), side=('ink', 2), roof=('ink', 3), win=('wht', 'cyan')),
    'glass': dict(front=('glass', 1), side=('glass', 0), roof=('glass', 1), win=('cyan', 'wht')),
    'plum':  dict(front=('vio', 0), side=('ink', 2), roof=('ink', 3), win=('wht', 'amb')),
}


def haze_col(Z, y=0):
    if M.name == 'noche':
        return mix((40, 54, 82), (66, 62, 104), clamp((Z - 2500) / 4000, 0, 1) * .5)
    return (118, 132, 152)


class Bld:
    def __init__(s, u0, v0, u1, v1, h, mat, seed, lit=.5, hero=None, sign=None, neon=None):
        s.u0, s.v0, s.u1, s.v1, s.h, s.mat, s.seed = u0, v0, u1, v1, h, mat, seed
        s.lit = lit; s.hero = hero; s.sign = sign; s.neon = neon
        uc, vc = (u0 + u1) / 2, (v0 + v1) / 2
        s.dist = math.hypot(*(a - b for a, b in zip(L2W(uc, vc), (0, 0))))
        s.Z = depth(u0, (v0 + v1) / 2)

    def key(s): return -s.dist


def face_pts(a, b, y0, y1):
    """a,b = (u,v) extremos horizontales; devuelve quad en pantalla abajo-izq, abajo-der, arriba-der, arriba-izq."""
    return [P(*a, y0), P(*b, y0), P(*b, y1), P(*a, y1)]


def calm(x):
    """factor de calma para la zona de iconos (izquierda)."""
    return clamp((x - 150) / 260, 0, 1)


def draw_face(b, a, c, kind, rnd):
    """kind: 'front' (mira a camara) o 'side'."""
    mat = MATS[b.mat]
    base = R(*mat[kind])
    if kind == 'front' and b.mat == 'conc' and rnd.random() < .3: base = R('slate', 0)
    ZA, ZC = depth(*a), depth(*c)
    Zm = (ZA + ZC) / 2
    hz = haze_col(Zm)
    # cuerpo en bandas horizontales con niebla creciente hacia abajo
    nb = 6 if b.h > 40 else 3
    xm = (P(*a)[0] + P(*c)[0]) / 2
    cm = calm(xm)
    for i in range(nb):
        y0 = b.h * i / nb; y1 = b.h * (i + 1) / nb
        f = fogk(Zm, (y0 + y1) / 2)
        col = mix(base, hz, f)
        col = mix(col, R('ink', 0), (1 - cm) * .45)
        poly(face_pts(a, c, y0, y1 + .01), col)
    fa = fogk(Zm, b.h * .6)
    # ventanas
    flen = math.hypot(c[0] - a[0], c[1] - a[1])
    du, dv = (c[0] - a[0]) / flen, (c[1] - a[1]) / flen
    glass = b.mat == 'glass'
    fh = 3.8 if glass else 4.2
    cw = 3.2 if glass else 4.0
    ncol = max(1, int((flen - 2) / cw)); nfl = max(1, int((b.h - 3) / fh))
    pxm = FOC / Zm  # px por metro
    side = kind == 'side'
    litp = b.lit * (.55 if side else 1.0) * (.25 + .75 * cm) * LITK[M.name]
    wc1, wc2 = mat['win']
    tone = rnd.random()
    # cada edificio tiene un tono dominante (oficina fria, cian, calida) y pocas notas de otro
    dom = [(R('mist', 2), R('mist', 3), R('wht', 0)), (R('cyan', 3), R('mist', 3), R('cyan', 2)),
           (R('amb', 3), R('amb', 2), R('mist', 3)), (R('mist', 1), R('mist', 2), R('mist', 3))][
        0 if tone < .4 else (1 if tone < .55 or wc1 == 'cyan' and tone < .8 else (2 if tone < .8 else 3))]
    def wcol(r2):
        if r2 < .5: return dom[0]
        if r2 < .8: return dom[1]
        if r2 < .93: return dom[2]
        return R('amb', 3) if dom[0] != R('amb', 3) else R('mist', 3)
    # bloques de planta: grupos de pisos encendidos (como oficinas reales)
    lit_floor = [rnd.random() < litp * 1.4 for _ in range(nfl)]
    if pxm * fh < 1.6:
        # lejos: plantas encendidas como tramos continuos (se leen como oficinas, no como ruido)
        step = max(1, int(1.6 / (pxm * cw)))
        for fl in range(0, nfl, max(1, int(1.6 / (pxm * fh)))):
            run0 = rnd.randint(0, ncol); run1 = run0 + rnd.randint(ncol // 3, ncol)
            for k in range(0, ncol, step):
                inrun = lit_floor[fl] and run0 <= k <= run1
                if rnd.random() < (.85 if inrun else litp * .18):
                    t = (k + .5) / ncol * flen
                    x, y = P(a[0] + du * t, a[1] + dv * t, 2 + fl * fh + fh * .5)
                    col = mix(wcol(rnd.random()), hz, fa * .7)
                    col = mix(col, R('ink', 1), (1 - cm) * .6)
                    pix(x, y, col, emis='w')
        return
    if glass:
        # torres de cristal: lineas de forjado claras + franjas de pisos encendidos
        for fl in range(nfl):
            y0 = 2 + fl * fh
            if lit_floor[fl] or rnd.random() < litp * .5:
                k0 = rnd.randint(0, ncol // 3); k1 = ncol - rnd.randint(0, ncol // 3)
                t0, t1 = k0 / ncol * flen, k1 / ncol * flen
                col = mix(wcol(rnd.random() * .9), hz, fa * .6)
                col = mix(col, R('glass', 1), (1 - cm) * .7)
                q = [P(a[0] + du * t0, a[1] + dv * t0, y0 + .6), P(a[0] + du * t1, a[1] + dv * t1, y0 + .6),
                     P(a[0] + du * t1, a[1] + dv * t1, y0 + fh - 1.1), P(a[0] + du * t0, a[1] + dv * t0, y0 + fh - 1.1)]
                poly(q, col, emis='w')
            if pxm * fh >= 3 and fl % 2 == 0:
                lc = mix(R('glass', 3), hz, fa); lc = mix(lc, R('glass', 0), 1 - cm)
                x0, y = P(*a, y0); x1, y1 = P(*c, y0)
                S.d.line([(round(x0), round(y)), (round(x1), round(y1))], fill=lc)
        # montantes verticales
        if pxm * cw * 3 >= 4:
            for k in range(0, ncol + 1, 3):
                t = k / ncol * flen
                x, y0 = P(a[0] + du * t, a[1] + dv * t, 0); _, y1 = P(a[0] + du * t, a[1] + dv * t, b.h)
                S.d.line([(round(x), round(y1)), (round(x), round(y0))], fill=mix(base, R('ink', 0), .4))
        return
    gap_u = .9 if pxm * cw > 5 else .55
    for fl in range(nfl):
        y0 = 2 + fl * fh
        pf = litp * (1.25 if lit_floor[fl] else .45)
        for k in range(ncol):
            r = rnd.random()
            t0 = k * cw + gap_u + (flen - ncol * cw) / 2; t1 = t0 + cw - gap_u * 2
            if r < pf:
                col = wcol(rnd.random()); emis = True
            else:
                col = mix(base, R('ink', 0), .55) if pxm * cw > 3 else None; emis = False
            if col is None: continue
            col = mix(col, hz, fa * (.55 if emis else 1))
            if emis: col = mix(col, R('ink', 1), (1 - cm) * .65)
            q = [P(a[0] + du * t0, a[1] + dv * t0, y0 + .7), P(a[0] + du * t1, a[1] + dv * t1, y0 + .7),
                 P(a[0] + du * t1, a[1] + dv * t1, y0 + fh - 1.2), P(a[0] + du * t0, a[1] + dv * t0, y0 + fh - 1.2)]
            poly(q, col, emis='w' if emis else False)


def draw_building(b):
    rnd = random.Random(b.seed)
    u0, v0, u1, v1, h = b.u0, b.v0, b.u1, b.v1, b.h
    # caras visibles
    faces = []
    if UC < u0: faces.append(('front', (u0, v0), (u0, v1)))
    if VC < v0: faces.append(('side', (u1, v0), (u0, v0)))
    elif VC > v1: faces.append(('side', (u0, v1), (u1, v1)))
    for kind, a, c in faces:
        draw_face(b, a, c, kind, rnd)
    # azotea
    Zm = b.Z
    hz = haze_col(Zm)
    xm = P((u0 + u1) / 2, (v0 + v1) / 2, h)[0]; cm = calm(xm)
    rbase = R(*MATS[b.mat]['roof'])
    rv_ = rnd.random()
    if b.mat in ('conc', 'dark'): rbase = (R('ink', 3), R('slate', 0), R('ink', 2), R('slate', 1))[int(rv_ * 4)]
    rc = mix(rbase, hz, fogk(Zm, h))
    rc = mix(rc, R('ink', 0), (1 - cm) * .45)
    roof = [P(u0, v0, h), P(u1, v0, h), P(u1, v1, h), P(u0, v1, h)]
    poly(roof, rc)
    # borde de luz (rim) del pretil: linea fina del lado de camara
    rim = mix(R('mist', 1) if b.mat != 'glass' else R('cyan', 1), hz, fogk(Zm, h))
    rim = mix(rim, R('ink', 1), (1 - cm) * .7)
    x0, y0 = P(u0, v0, h); x1, y1 = P(u0, v1, h)
    if FOC / Zm > .25:
        S.d.line([(round(x0), round(y0)), (round(x1), round(y1))], fill=rim)
    # arista vertical frontal (luz de borde)
    if faces and FOC / Zm * h > 20:
        corner = (u0, v0) if VC < v0 else (u0, v1)
        xa, ya = P(*corner, 0); _, yb = P(*corner, h)
        ec = b.neon or rim
        if b.neon:
            ec = mix(ec, hz, fogk(Zm, h) * .5)
            S.d.line([(round(xa), round(yb)), (round(xa), round(ya))], fill=ec)
            S.dE.line([(round(xa), round(yb)), (round(xa), round(ya))], fill=ec); S.dB.line([(round(xa), round(yb)), (round(xa), round(ya))], fill=ec)
            S.dK.line([(round(xa), round(yb)), (round(xa), round(ya))], fill=255)
    # equipos de azotea en edificios cercanos
    pxm = FOC / Zm
    if pxm > .9 and (u1 - u0) > 14:
        for _ in range(rnd.randint(1, 3)):
            ru = rnd.uniform(u0 + 3, u1 - 9); rv = rnd.uniform(v0 + 3, v1 - 9)
            ww, dd, hh = rnd.uniform(4, 8), rnd.uniform(4, 8), rnd.uniform(2, 5)
            c1 = mix(R('slate', 1), hz, fogk(Zm, h)); c2 = mix(R('ink', 3), hz, fogk(Zm, h))
            c3 = mix(R('slate', 2), hz, fogk(Zm, h))
            if cm < 1: c1, c2, c3 = (mix(c, R('ink', 0), (1 - cm) * .5) for c in (c1, c2, c3))
            poly([P(ru, rv, h), P(ru, rv + dd, h), P(ru, rv + dd, h + hh), P(ru, rv, h + hh)], c1)
            if VC < rv: poly([P(ru, rv, h), P(ru + ww, rv, h), P(ru + ww, rv, h + hh), P(ru, rv, h + hh)], c2)
            else: poly([P(ru, rv + dd, h), P(ru + ww, rv + dd, h), P(ru + ww, rv + dd, h + hh), P(ru, rv + dd, h + hh)], c2)
            poly([P(ru, rv, h + hh), P(ru + ww, rv, h + hh), P(ru + ww, rv + dd, h + hh), P(ru, rv + dd, h + hh)], c3)
    # antena con luz roja en los altos
    if h > 120 and pxm > .25:
        au, av = (u0 + u1) / 2, (v0 + v1) / 2
        xa, ya = P(au, av, h); _, yb = P(au, av, h + 14)
        S.d.line([(round(xa), round(ya)), (round(xa), round(yb))], fill=mix(R('slate', 2), hz, .4))
        pix(xa, yb - 1, R('red', 2), emis=True, crisp=True)
    # carteles/pantallas
    if b.sign:
        for f in (b.sign if isinstance(b.sign, list) else [b.sign]): f(b)


# ------------------------------------------------------------------ geometria de la ciudad
AVE = 21.0       # media anchura de la avenida
BLK_U = 96.0; ST_U = 13.0
BLK_V = 64.0; ST_V = 11.0


def screen_to_local(x, Z):
    X = (x - CX) * Z / FOC
    return (X - X0) * SA + (Z - Z0) * CA, (X - X0) * CA - (Z - Z0) * SA


def rail_path():
    # puntos de control fijados en pantalla (x, distancia): entra abajo a la derecha y curva hacia el fondo
    ctrl = [screen_to_local(x, Z) for x, Z in ((850, 420), (805, 540), (778, 720), (764, 1000), (755, 1450), (749, 2200), (745, 3200), (742, 5200))]
    pts = []
    for i in range(len(ctrl) - 1):   # Catmull-Rom
        p0 = ctrl[max(0, i - 1)]; p1 = ctrl[i]; p2 = ctrl[i + 1]; p3 = ctrl[min(len(ctrl) - 1, i + 2)]
        n = max(2, int(math.hypot(p2[0] - p1[0], p2[1] - p1[1]) / 22))
        for k in range(n):
            t = k / n; t2 = t * t; t3 = t2 * t
            pts.append(tuple(.5 * (2 * p1[j] + (-p0[j] + p2[j]) * t + (2 * p0[j] - 5 * p1[j] + 4 * p2[j] - p3[j]) * t2 + (-p0[j] + 3 * p1[j] - 3 * p2[j] + p3[j]) * t3) for j in range(2)))
    pts.append(ctrl[-1])
    return pts


RAIL = rail_path()
TOWER = screen_to_local(640, 2300)


def near_rail(u, v, r):
    for (a, b) in RAIL:
        if abs(a - u) < r + 12 and abs(b - v) < r: return True
    return False


HEROES = {}


def make_city():
    rnd = random.Random(7)
    blds = []
    for iu in range(-1, 64):
        ub = iu * (BLK_U + ST_U)
        if ub > 6200: break
        for side in (-1, 1):
            for iv in range(0, 46):
                vb0 = AVE + 3 + iv * (BLK_V + ST_V)
                v0, v1 = (vb0, vb0 + BLK_V) if side > 0 else (-vb0 - BLK_V, -vb0)
                Zc = depth(ub + BLK_U / 2, (v0 + v1) / 2)
                X, _ = L2W(ub + BLK_U / 2, (v0 + v1) / 2)
                if Zc < 300 or abs(X) > Zc * 0.72 + 120: continue
                # subdividir manzana en 1-4 parcelas
                cuts_u = [ub]
                n_u = rnd.choice((1, 2, 2, 3))
                for k in range(1, n_u): cuts_u.append(ub + BLK_U * k / n_u + rnd.uniform(-6, 6))
                cuts_u.append(ub + BLK_U)
                for k in range(len(cuts_u) - 1):
                    pu0, pu1 = cuts_u[k] + 1.5, cuts_u[k + 1] - 1.5
                    n_v = rnd.choice((1, 2))
                    cv = [v0, (v0 + v1) / 2 + rnd.uniform(-8, 8), v1] if n_v == 2 else [v0, v1]
                    for j in range(len(cv) - 1):
                        pv0, pv1 = cv[j] + 1.5, cv[j + 1] - 1.5
                        uc, vc = (pu0 + pu1) / 2, (pv0 + pv1) / 2
                        if near_rail(uc, vc, 26 + (pv1 - pv0) / 2): continue
                        if any(hb.u0 - 4 < uc < hb.u1 + 4 and hb.v0 - 4 < vc < hb.v1 + 4 for hb in HEROES.values()): continue
                        Zb = depth(uc, vc)
                        # alturas: mas altas en el anillo medio y junto a la avenida
                        d_av = abs(vc)
                        base = 22 + 64 * math.exp(-d_av / 380)
                        near = clamp((Zb - 500) / 900, 0, 1)          # cerca de la camara: mas bajos
                        if rnd.random() < .05 + .12 * near: base *= rnd.uniform(2.0, 3.6)
                        h = base * rnd.uniform(.6, 1.4) * (.55 + .45 * near) * (1.2 if Zb > 1600 else 1)
                        if 0 < vc < AVE + 80 and Zb < 1900: h = min(h, 16 + (Zb - 380) * .05)   # no tapar la avenida
                        elif 0 < vc < VCAM + 60 and Zb < 1200: h = min(h, 30 + (Zb - 380) * .08)
                        if Zb > 2800 and rnd.random() < .10: h = rnd.uniform(110, 260)        # skyline lejano
                        h = clear_view(pu0, pv0, pu1, pv1, h, math.hypot(*L2W(uc, vc)))
                        if h < 6: continue
                        mat = rnd.choices(['conc', 'dark', 'glass', 'plum'], [5, 4, 2.2 if h > 60 else .6, 1])[0]
                        lit = rnd.uniform(.25, .7)
                        neon = None
                        if rnd.random() < .12 and h > 40: neon = rnd.choice((R('cyan', 2), R('mag', 2), R('cyan', 3)))
                        blds.append(Bld(pu0, pv0, pu1, pv1, h, mat, rnd.randint(0, 1 << 30), lit, neon=neon))
    return blds


# ------------------------------------------------------------------ suelo, calles, coches
def draw_ground():
    night = M.name == 'noche'
    asphalt = (12, 14, 28) if night else (36, 42, 58)
    for y in range(HY, H):
        Z = FOC * CAMH / max(1e-3, (y - HY))
        c = mix(asphalt, haze_col(Z), fogk(Z, 0))
        S.d.line([(0, y), (W, y)], fill=c)
    S.dG.rectangle([0, HY, W, H], fill=255)


def ground_quad(u0, v0, u1, v1, col, ground=True):
    poly([P(u0, v0), P(u1, v0), P(u1, v1), P(u0, v1)], col, ground=ground)


def draw_streets():
    night = M.name == 'noche'
    side = (22, 26, 46) if night else (54, 60, 78)
    # aceras de la avenida y cruces con pasos de cebra
    for iu in range(-1, 40):
        ub = iu * (BLK_U + ST_U)
        Z = depth(ub, 0)
        if Z > 5000: break
        f = fogk(Z, 0)
        for s in (-1, 1):
            a, b = (AVE, AVE + 3) if s > 0 else (-AVE - 3, -AVE)
            ground_quad(ub, a, ub + BLK_U, b, mix(side, haze_col(Z), f))
        # paso de cebra en el cruce
        us = ub + BLK_U
        if Z < 2600:
            zc = mix((150, 160, 186) if night else (170, 176, 190), haze_col(Z), f)
            zc = mix(zc, (12, 14, 28), .55)
            for k in range(-8, 8):
                v = k * 2.2
                ground_quad(us + 1.5, v, us + 4.5, v + 1.2, zc)
                ground_quad(us + ST_U - 4.5, v, us + ST_U - 1.5, v + 1.2, zc)
    # lineas de carril
    for iu in range(0, 300):
        u = iu * 9.0
        Z = depth(u, 0)
        if Z > 3200: break
        c = mix((90, 96, 120), haze_col(Z), fogk(Z, 0)); c = mix(c, (12, 14, 28), .5)
        for v in (-5.6, 5.6, -11.2, 11.2):
            ground_quad(u, v - .25, u + 4, v + .25, c)
        ground_quad(u, -.45, u + 9, .45, mix(R('amb', 0), haze_col(Z), fogk(Z, 0)))


def streaks():
    """estelas de larga exposicion en la avenida: rojas (se alejan) y blancas (vienen)."""
    if M.name != 'noche': return
    rnd = random.Random(3)
    lanes = [(-15.0, 'red'), (-10.0, 'red'), (-5.0, 'red'), (5.0, 'wht'), (10.0, 'wht'), (15.0, 'amb')]
    for v, cn in lanes:
        u = -60.0
        while u < 4200:
            ln = rnd.uniform(40, 200) if cn != 'red' else rnd.uniform(20, 160); gap = rnd.uniform(10, 90)
            Z = depth(u, v)
            f = fogk(Z, 0)
            base = R(cn, 2 if cn != 'wht' else 1) if Z < 1400 else R(cn, 1 if cn != 'wht' else 0)
            col = mix(base, haze_col(Z), f * .6)
            n = 6
            for k in range(n):
                ua = u + ln * k / n; ub = u + ln * (k + 1) / n
                a, b = P(ua, v), P(ub, v)
                wv = .35 if Z > 900 else .5
                c = mix(col, R('ink', 1), .5 * (1 - math.sin(math.pi * (k + .5) / n)))
                poly([P(ua, v - wv), P(ub, v - wv), P(ub, v + wv), P(ua, v + wv)], c, ground=True, emis=True)
            u += ln + gap


CARS = []


def car(u, v, dirn, body, kind='car'):
    """coche en perspectiva: caja baja con luces."""
    L, Wd, Hc = (4.6, 2.0, 1.5) if kind == 'car' else (11.0, 2.6, 3.2)
    u0, u1 = u, u + L
    v0, v1 = v - Wd / 2, v + Wd / 2
    Z = depth(u, v); f = fogk(Z, 0); hz = haze_col(Z)
    cb = mix(body, hz, f); ct = mix(mul(body, 1.4), hz, f); cs = mix(mul(body, .6), hz, f)
    poly([P(u0, v0, 0), P(u0, v1, 0), P(u0, v1, Hc), P(u0, v0, Hc)], cb)
    if VC < v0: poly([P(u1, v0, 0), P(u0, v0, 0), P(u0, v0, Hc), P(u1, v0, Hc)], cs)
    else: poly([P(u0, v1, 0), P(u1, v1, 0), P(u1, v1, Hc), P(u0, v1, Hc)], cs)
    poly([P(u0, v0, Hc), P(u1, v0, Hc), P(u1, v1, Hc), P(u0, v1, Hc)], ct)
    if kind == 'bus':
        for k in range(1, 6):
            uu = u0 + k * 1.8
            x, y = P(uu, v0 if VC < v0 else v1, Hc * .65)
            pix(x, y, R('amb', 3), emis=True)
    # luces (traseras rojas si se aleja, faros si viene)
    lc = R('red', 2) if dirn > 0 else R('wht', 1)
    for vv in (v0 + .3, v1 - .3):
        x, y = P(u0, vv, Hc * .45)
        pix(x, y, lc, emis=True, crisp=True)
        if dirn < 0:   # haz de faros en el asfalto mojado
            for k in range(1, 7):
                xx, yy = P(u0 - k * 1.6, vv, 0)
                pix(xx, yy, mix(R('wht', 0), R('ink', 2), k / 7), emis=True)


def draw_cars():
    rnd = random.Random(11)
    bodies = [(40, 46, 80), (70, 40, 90), (28, 60, 72), (90, 34, 60), (60, 62, 74), (130, 120, 60)]
    for v, d in ((-14.0, 1), (-8.5, 1), (-3.0, 1), (3.0, -1), (8.5, -1), (14.0, -1)):
        u = rnd.uniform(-40, 30)
        while u < 1800:
            kind = 'bus' if rnd.random() < .08 else 'car'
            body = (200, 160, 40) if rnd.random() < .12 else rnd.choice(bodies)   # taxis amarillos
            CARS.append((depth(u, v), u, v, d, body, kind))
            u += rnd.uniform(18, 70) * (1 + u / 900)


# ------------------------------------------------------------------ farolas
def lamps():
    out = []
    for iu in range(0, 60):
        u = iu * 27.0
        for v in (-AVE - 1.2, AVE + 1.2):
            out.append((depth(u, v), u, v))
    return out


def draw_lamp(u, v):
    Z = depth(u, v)
    if Z > 3000 or M.name != 'noche': return
    x0, y0 = P(u, v, 0); x1, y1 = P(u, v, 9)
    f = fogk(Z, 0)
    pc = mix((40, 46, 70), haze_col(Z), f)
    S.d.line([(round(x0), round(y0)), (round(x1), round(y1))], fill=pc)
    lc = mix(R('amb', 3), haze_col(Z), f * .5)
    xl = x1 + (2 if v < 0 else -2) * (FOC / Z > 1.2)
    pix(xl, y1, lc, emis=True, crisp=True)
    if FOC / Z > 1.0:
        pix(xl + 1, y1, R('amb', 2), emis=True); pix(xl - 1, y1, R('amb', 2), emis=True)
    # charco de luz bajo la farola (escalonado)
    if FOC / Z > .7:
        for r, c, k in ((4.0, R('amb', 0), .7), (1.8, R('amb', 0), .35)):
            pts = [P(u + r * math.cos(t), v + r * math.sin(t), 0) for t in [i * math.pi / 6 for i in range(12)]]
            poly(pts, mix(c, (12, 14, 28), k), ground=True)


# ------------------------------------------------------------------ via elevada y tren
def draw_rail_seg(i):
    (ua, va), (ub, vb) = RAIL[i], RAIL[i + 1]
    Zm = depth((ua + ub) / 2, (va + vb) / 2)
    hz = haze_col(Zm); f = fogk(Zm, 20)
    nx, ny = -(vb - va), (ub - ua); nl = math.hypot(nx, ny); nx, ny = nx / nl, ny / nl
    hw = 7.0; Y = 20.0; T = 3.2
    A0 = (ua - nx * hw, va - ny * hw); A1 = (ua + nx * hw, va + ny * hw)
    B0 = (ub - nx * hw, vb - ny * hw); B1 = (ub + nx * hw, vb + ny * hw)
    # pilar
    if i % 1 == 0:
        pu, pv = ua, va
        x0, y0 = P(pu, pv, 0); x1, y1 = P(pu, pv, Y)
        wpx = max(1, round(FOC / Zm * 2.4))
        S.d.rectangle([round(x0) - wpx // 2, round(y1), round(x0) + (wpx - 1) // 2, round(y0)], fill=mix((26, 30, 52), hz, f))
        S.dG.rectangle([round(x0) - wpx // 2, round(y1), round(x0) + (wpx - 1) // 2, round(y0)], fill=0)
    # costado visible (el mas cercano a la camara)
    dA0 = math.hypot(*L2W(*A0)); dA1 = math.hypot(*L2W(*A1))
    Sa, Sb = (A0, B0) if dA0 < dA1 else (A1, B1)
    side = mix((34, 40, 66), hz, f)
    poly([P(*Sa, Y - T), P(*Sb, Y - T), P(*Sb, Y), P(*Sa, Y)], side)
    # luz de borde cian bajo el tablero (linea LED)
    xa, ya = P(*Sa, Y - T + .4); xb, yb = P(*Sb, Y - T + .4)
    lc = mix(R('cyan', 1), hz, f * .6)
    S.d.line([(round(xa), round(ya)), (round(xb), round(yb))], fill=lc)
    S.dE.line([(round(xa), round(ya)), (round(xb), round(yb))], fill=lc); S.dB.line([(round(xa), round(ya)), (round(xb), round(yb))], fill=lc)
    # tablero
    poly([P(*A0, Y), P(*B0, Y), P(*B1, Y), P(*A1, Y)], mix((26, 30, 50), hz, f))
    # carriles: dos vias con brillo de lluvia
    for off in (-3.2, -1.6, 1.6, 3.2):
        a = P(ua + nx * off, va + ny * off, Y + .2); b = P(ub + nx * off, vb + ny * off, Y + .2)
        rc = mix(R('mist', 1) if abs(off) > 2 else R('slate', 2), hz, f)
        S.d.line([(round(a[0]), round(a[1])), (round(b[0]), round(b[1]))], fill=rc)
    # baranda superior con reflejo
    for o in (-hw, hw):
        a = P(ua + nx * o, va + ny * o, Y + 1.2); b = P(ub + nx * o, vb + ny * o, Y + 1.2)
        S.d.line([(round(a[0]), round(a[1])), (round(b[0]), round(b[1]))], fill=mix(R('slate', 3), hz, f))
    # tren
    if TRAIN[0] <= i < TRAIN[1]:
        tw = 3.4; th = 4.6
        o = -2.4
        C0 = (ua + nx * (o - tw / 2), va + ny * (o - tw / 2)); C1 = (ua + nx * (o + tw / 2), va + ny * (o + tw / 2))
        D0 = (ub + nx * (o - tw / 2), vb + ny * (o - tw / 2)); D1 = (ub + nx * (o + tw / 2), vb + ny * (o + tw / 2))
        dC0 = math.hypot(*L2W(*C0)); dC1 = math.hypot(*L2W(*C1))
        Ta, Tb = (C0, D0) if dC0 < dC1 else (C1, D1)
        poly([P(*Ta, Y + .3), P(*Tb, Y + .3), P(*Tb, Y + th), P(*Ta, Y + th)], mix((150, 160, 186), hz, f))
        poly([P(*C0, Y + th), P(*D0, Y + th), P(*D1, Y + th), P(*C1, Y + th)], mix((190, 200, 220), hz, f))
        # franja de ventanas encendidas
        n = 8
        for k in range(n):
            if k % 4 == 3: continue
            t0, t1 = k / n, (k + .8) / n
            qa = (Ta[0] + (Tb[0] - Ta[0]) * t0, Ta[1] + (Tb[1] - Ta[1]) * t0)
            qb = (Ta[0] + (Tb[0] - Ta[0]) * t1, Ta[1] + (Tb[1] - Ta[1]) * t1)
            poly([P(*qa, Y + 1.8), P(*qb, Y + 1.8), P(*qb, Y + 3.4), P(*qa, Y + 3.4)], mix(R('cyan', 3), hz, f * .5), emis=True)
        xa, ya = P(*Ta, Y + 1.0); xb, yb = P(*Tb, Y + 1.0)
        S.d.line([(round(xa), round(ya)), (round(xb), round(yb))], fill=mix(R('mag', 2), hz, f * .5))
        if i == TRAIN[0]:
            x, y = P(*Ta, Y + 1.5); pix(x - 1, y, R('wht', 1), emis=True, crisp=True)


TRAIN = (2, 9)


# ------------------------------------------------------------------ torre-faro
def draw_tower():
    u, v = TOWER
    Z = depth(u, v); s = FOC / Z
    hz = haze_col(Z); f = fogk(Z, 120) * .45
    Ht = 520.0
    bx, by = P(u, v, 0); _, ty = P(u, v, Ht)
    col_hi = R('amb', 3); col = R('amb', 2); col_lo = R('amb', 1); col_d = R('amb', 0)
    S.Tw = (bx, by, ty)
    def half(yy):  # media anchura en metros a altura yy (perfil curvo)
        t = yy / Ht
        return 4 + 46 * (1 - t) ** 2.6
    ystep = 1.0 / s
    yy = 0.0
    rows = []
    while yy < Ht:
        hw = half(yy) * s
        _, sy = P(u, v, yy)
        rows.append((sy, hw, yy)); yy += ystep
    # silueta de celosia: dos patas con arriostramiento en X
    prev = None
    for k, (sy, hw, yy) in enumerate(rows):
        sy = round(sy)
        xl, xr = round(bx - hw), round(bx + hw)
        c = mix(col_lo, hz, f)
        if hw > 1.5:
            for xx in (xl, xl + 1, xr, xr - 1): pix(xx, sy, c if xx in (xl + 1, xr - 1) else mix(col, hz, f), emis=True)
        else:
            for xx in range(xl, xr + 1): pix(xx, sy, mix(col, hz, f), emis=True)
        # tramado de celosia: patron X
        cyc = 6
        ph = k % cyc
        if hw > 3:
            span = xr - xl
            for j in range(0, span, cyc):
                x1 = xl + j + ph; x2 = xl + j + cyc - ph
                for xx in (x1, x2):
                    if xl < xx < xr: pix(xx, sy, mix(col_d, hz, f * .6), emis=True)
        if k % cyc == 0 and hw > 2:
            for xx in range(xl, xr + 1): pix(xx, sy, mix(col_lo, hz, f), emis=True)
    # miradores
    for yy, wdt, hgt in ((150.0, 16, 9), (250.0, 9, 6)):
        _, sy = P(u, v, yy); _, sy2 = P(u, v, yy + hgt)
        hw = (half(yy) + 3) * s
        S.d.rectangle([round(bx - hw), round(sy2), round(bx + hw), round(sy)], fill=mix(col_d, hz, f))
        S.d.line([(round(bx - hw), round(sy2)), (round(bx + hw), round(sy2))], fill=col_hi)
        for xx in range(round(bx - hw) + 1, round(bx + hw), 2):
            pix(xx, round((sy + sy2) / 2), R('wht', 1), emis=True, crisp=True)
        S.dE.rectangle([round(bx - hw), round(sy2), round(bx + hw), round(sy)], fill=col); S.dB.rectangle([round(bx - hw), round(sy2), round(bx + hw), round(sy)], fill=col)
    # antena + baliza
    _, sa = P(u, v, Ht + 60)
    S.d.line([(round(bx), round(ty)), (round(bx), round(sa))], fill=mix(R('wht', 0), hz, .2))
    pix(bx, sa - 1, R('red', 3), emis=True, crisp=True); pix(bx, sa - 2, R('red', 2), emis=True)
    return (u, v)


def tower_halo():
    u, v = TOWER; Z = depth(u, v)
    bx, by = P(u, v, 0); _, ty = P(u, v, 520)
    halo_ellipse(bx, (by + ty) / 2 - 10, 34, (by - ty) / 2 + 20, R('amb', 1), .16)


def halo_ellipse(cx, cy, rx, ry, col, a):
    """halo escalonado: 3 anillos concentricos de opacidad decreciente (el tramado los convierte en escalones)."""
    lay = Image.new('L', (W, H), 0); dl = ImageDraw.Draw(lay)
    for k, aa in ((1.0, a * .5), (.7, a * .8), (.42, a)):
        dl.ellipse([cx - rx * k, cy - ry * k, cx + rx * k, cy + ry * k], fill=int(255 * aa))
    S.img = Image.composite(ImageChops.add(S.img, Image.new('RGB', (W, H), col)), S.img, lay); S.d = ImageDraw.Draw(S.img)


# ------------------------------------------------------------------ cuantizacion con tramado ordenado
BAYER = [[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]


def palette_flat():
    cols = []
    for k in ('ink', 'slate', 'mist', 'glass', 'cyan', 'mag', 'vio', 'amb', 'red', 'grn', 'wht'):
        cols += M.R[k]
    return cols


def quantize(img, crisp, amp=22):
    tile = Image.new('L', (4, 4)); tile.putdata([int((BAYER[y][x] + .5) / 16 * amp) for y in range(4) for x in range(4)])
    off = Image.new('L', (W, H))
    for y in range(0, H, 4):
        for x in range(0, W, 4): off.paste(tile, (x, y))
    offrgb = Image.merge('RGB', (off, off, off))
    d = ImageChops.subtract(ImageChops.add(img, offrgb), Image.new('RGB', (W, H), (amp // 2,) * 3))
    d = Image.composite(img, d, crisp)
    cols = palette_flat()
    flat = []
    for c in cols: flat += list(c)
    flat += list(cols[0]) * (256 - len(cols))
    pal = Image.new('P', (1, 1)); pal.putpalette(flat)
    return d.quantize(palette=pal, dither=Image.Dither.NONE).convert('RGB'), len(cols)


# ------------------------------------------------------------------ escena
def build_city_layer():
    new_canvases(); CARS.clear(); HEROES.clear(); make_heroes()
    draw_sky(); draw_ground(); draw_streets(); streaks(); draw_cars()
    objs = [(b.dist, 0, b) for b in make_city() + list(HEROES.values())]
    objs += [(math.hypot(*L2W(c[1], c[2])), 1, c) for c in CARS]
    objs += [(math.hypot(*L2W(l[1], l[2])), 2, l) for l in lamps()]
    for i in range(len(RAIL) - 1):
        (ua, va), (ub, vb) = RAIL[i], RAIL[i + 1]
        objs.append((math.hypot(*L2W((ua + ub) / 2, (va + vb) / 2)), 3, i))
    objs.append((math.hypot(*L2W(*TOWER)), 4, None))
    objs.sort(key=lambda o: -o[0])
    for _, k, o in objs:
        if k == 0: draw_building(o)
        elif k == 1: car(o[1], o[2], o[3], o[4], o[5])
        elif k == 2: draw_lamp(o[1], o[2])
        elif k == 3: draw_rail_seg(o)
        else: tower_halo(); draw_tower()


def hero(name, Z, vc, wv, du, h, mat, sign=None, neon=None, lit=.55):
    """edificio protagonista: front face centrada en v=vc a distancia Z (en el eje de la avenida)."""
    # resolver u para que el centro de la fachada frontal este a profundidad Z
    u = (Z - Z0 + vc * SA) / CA
    b = Bld(u, vc - wv / 2, u + du, vc + wv / 2, h, mat, hash(name) & 0xffff, lit, sign=sign, neon=neon)
    HEROES[name] = b
    return b


DATA = {'hora': '21:37', 'fecha': 'MAR 10 NOV'}   # datos de ejemplo (en el tema real vienen del sistema)
SIGNS = {}   # nombre -> funcion que devuelve la imagen RGBA del cartel (se rellena mas abajo)
LEDMASK = None


def mount(b, simg, t, ym, halo=None, face='front'):
    """pega un cartel nativo sobre la fachada con cizallado por columnas (sin reescalar)."""
    if face == 'front':
        a0, a1 = (b.u0, b.v0), (b.u0, b.v1)
    else:
        a0, a1 = ((b.u1, b.v0), (b.u0, b.v0)) if VC < b.v0 else ((b.u0, b.v1), (b.u1, b.v1))
    pa, pb = P(*a0, ym), P(*a1, ym)
    cx = pa[0] + (pb[0] - pa[0]) * t; cy = pa[1] + (pb[1] - pa[1]) * t
    slope = (pb[1] - pa[1]) / (pb[0] - pa[0])
    w, h = simg.size
    x0 = round(cx - w / 2); y0 = round(cy - h / 2)
    # cizallado por bandas: el sign se divide en franjas horizontales (lineas de texto);
    # dentro de cada franja el escalon de 1 px solo cae en columnas vacias de esa franja,
    # asi cada glifo baja entero (como hacen los pixel artists) y nunca se parte.
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
    # unir franjas separadas por 1-2 filas vacias (matrices LED, glifos con huecos)
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
    DETAIL_BOXES.append((simg.info.get('name', '?'), (x0 - 4, y0 + min(dys) - 4, x0 + w + 4, y0 + h + max(dys) + 4)))
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
    # fondo: la silueta del cartel con la pantalla vacia, para que los escalones no dejen huecos
    back = simg.copy(); bd_ = ImageDraw.Draw(back)
    bd_.rectangle([5, 5, w - 6, h - 6], fill=R('ink', 0) + (255,))
    for i in range(w):
        S.img.paste(back.crop((i, 0, i + 1, h)), (x0 + i, y0 + dys[i]), alpha.crop((i, 0, i + 1, h)))
    for i in range(w):
        for (j0, j1, _), dl in zip(bands, band_dys):
            hh = j1 - j0 + 1
            col = simg.crop((i, j0, i + 1, j1 + 1)); am = alpha.crop((i, j0, i + 1, j1 + 1))
            pos = (x0 + i, y0 + j0 + dl[i])
            box = (pos[0], pos[1], pos[0] + 1, pos[1] + hh)
            S.img.paste(col, pos, am); S.E.paste(col, pos, am); S.B.paste(col, pos, am)
            S.K.paste(255, box, am); S.G.paste(0, box, am)
            if led is not None:
                lm = led.crop((i, j0, i + 1, j1 + 1)); LEDMASK.paste(lm, pos, lm)
    S.d = ImageDraw.Draw(S.img); S.dE = ImageDraw.Draw(S.E); S.dK = ImageDraw.Draw(S.K); S.dG = ImageDraw.Draw(S.G); S.dB = ImageDraw.Draw(S.B)
    return (x0, y0, w, h)


def placeholder(w, h, col):
    im = Image.new('RGBA', (w, h), col + (255,)); return im


def make_heroes():
    SIGN_RECTS.clear()
    for nm, Z, vc, wv, du, h, mat, sg, lit in HERO_LIST:
        b = hero(nm, Z, vc, wv, du, h, mat, sign=sg, lit=lit)
        for f in (sg if isinstance(sg, list) else [sg] if sg else []):
            w, hh, t, ym, legs = f.geom
            r = sign_rect(b, w, hh, t, ym)
            if legs: r = (r[0], r[1], r[2], P(b.u0, b.v0, b.h)[1])
            SIGN_RECTS.append(r + (b.dist,))


def sign_slot(name, w, h, col, t=.5, ym=None, face='front', halo=True, legs=False):
    def f(b):
        im = SIGNS[name]() if name in SIGNS else placeholder(w, h, col)
        im.info['name'] = name
        if legs: draw_legs(b, im, t, ym)
        mount(b, im, t, ym if ym is not None else b.h * .7, halo=(col, 1.0) if halo else None, face=face)
    f.geom = (w, h, t, ym, legs)
    return f


SIGN_RECTS = []


def sign_rect(b, w, h, t, ym):
    pa, pb = P(b.u0, b.v0, ym), P(b.u0, b.v1, ym)
    cx = pa[0] + (pb[0] - pa[0]) * t; cy = pa[1] + (pb[1] - pa[1]) * t
    return (cx - w / 2 - 6, cy - h / 2 - 6, cx + w / 2 + 6, cy + h / 2 + 6)


def clear_view(u0, v0, u1, v1, h, dist):
    """rebaja edificios de relleno que taparian un cartel protagonista."""
    xs = [P(u, v)[0] for u in (u0, u1) for v in (v0, v1)]
    bx0, bx1 = min(xs), max(xs)
    for (x0, y0, x1, y1, hd) in SIGN_RECTS:
        if dist >= hd or bx1 < x0 or bx0 > x1: continue
        # altura maxima para que la azotea quede por debajo del cartel
        for (u, v) in ((u0, v0), (u0, v1), (u1, v0), (u1, v1)):
            Z = depth(u, v)
            hmax = CAMH - (y1 + 2 - HY) * Z / FOC
            h = min(h, hmax)
    return h


def draw_legs(b, im, t, ym):
    """estructura de celosia para un cartel de azotea."""
    w, h = im.size
    v = b.v0 + (b.v1 - b.v0) * t
    cx, cy = P(b.u0 + 4, v, ym)
    bot = round(cy + h / 2)
    for dx in (-w // 2 + 6, 0, w // 2 - 6):
        x = round(cx + dx)
        _, yr = P(b.u0 + 4, v, b.h)
        S.d.line([(x, bot), (x, round(yr))], fill=R('slate', 1)); S.d.line([(x + 1, bot), (x + 1, round(yr))], fill=R('ink', 2))
    yr = round(P(b.u0 + 4, v, b.h)[1])
    for k in range(-w // 2 + 6, w // 2 - 6, 4):
        x = round(cx + k)
        S.d.line([(x, bot), (x + 4, yr)], fill=R('ink', 3))
    S.d.line([(round(cx - w / 2 + 3), bot + 1), (round(cx + w / 2 - 3), bot + 1)], fill=R('slate', 2))


TDV = screen_to_local(905, 500)[1]   # torre derecha: fachada centrada en x=905
HERO_LIST = [
    # nombre, Z, v centro, ancho(v), fondo(u), altura, material, cartel(es), luces
    ('reloj', 650, -150, 115, 50, 205, 'dark', sign_slot('reloj', 100, 58, R('cyan', 2), t=.5, ym=150), .35),
    ('cpu', 980, -262, 175, 60, 265, 'glass', sign_slot('cpu', 108, 50, R('mag', 2), t=.5, ym=225), .5),
    ('izq', 760, -420, 90, 60, 300, 'glass', None, .4),
    ('git', 560, -75, 90, 40, 46, 'conc', sign_slot('git', 72, 42, R('amb', 2), t=.5, ym=27), .45),
    ('net', 540, 62, 64, 40, 24, 'conc', sign_slot('net', 84, 46, R('cyan', 2), t=.5, ym=50, legs=True), .5),
    ('torre_der', 500, TDV, 84, 70, 300, 'glass', [sign_slot('vpn', 66, 40, R('grn', 2), t=.5, ym=225),
                                                 sign_slot('bat', 64, 40, R('mag', 2), t=.5, ym=140)], .55),
    ('ram', 820, -82, 110, 50, 160, 'conc', sign_slot('ram', 92, 50, R('vio', 2), t=.5, ym=108), .4),
]


# ================================================================== CARTELES (pixel a pixel)
FJ = ImageFont.truetype(FONTDIR + 'DotGothic16-Regular.ttf', 16)   # kana para carteles decorativos
GL = {  # glifos propios (x = pixel)
    'dn': ["xxxxx", ".xxx.", "..x.."], 'up': ["..x..", ".xxx.", "xxxxx"],
    'ok': [".....x", "....xx", "x..xx.", "xxxx..", ".xx..."], 'no': ["x...x", ".x.x.", "..x..", ".x.x.", "x...x"],
    'deg': [".x.", "x.x", ".x."], 'tri': ["x..", "xx.", "xxx", "xx.", "x.."], 'dot': [".x.", "xxx", ".x."],
}
FONTS = {'D': (FD, 7, 3), 'M': (FM, 4, 3)}
_F35 = """A .x. x.x xxx x.x x.x|B xx. x.x xx. x.x xx.|C .xx x.. x.. x.. .xx|D xx. x.x x.x x.x xx.|E xxx x.. xx. x.. xxx
F xxx x.. xx. x.. x..|G .xx x.. x.x x.x .xx|H x.x x.x xxx x.x x.x|I xxx .x. .x. .x. xxx|J ..x ..x ..x x.x .x.
K x.x x.x xx. x.x x.x|L x.. x.. x.. x.. xxx|M x.x xxx xxx x.x x.x|N xx. x.x x.x x.x x.x|O .x. x.x x.x x.x .x.
P xx. x.x xx. x.. x..|Q .x. x.x x.x xx. .xx|R xx. x.x xx. x.x x.x|S .xx x.. .x. ..x xx.|T xxx .x. .x. .x. .x.
U x.x x.x x.x x.x xxx|V x.x x.x x.x x.x .x.|W x.x x.x xxx xxx x.x|X x.x x.x .x. x.x x.x|Y x.x x.x .x. .x. .x.
Z xxx ..x .x. x.. xxx|0 xxx x.x x.x x.x xxx|1 .x. xx. .x. .x. xxx|2 xx. ..x .x. x.. xxx|3 xx. ..x .x. ..x xx.
4 x.x x.x xxx ..x ..x|5 xxx x.. xx. ..x xx.|6 .xx x.. xxx x.x xxx|7 xxx ..x .x. .x. .x.|8 xxx x.x xxx x.x xxx
9 xxx x.x xxx ..x xx.|: . x . x .|. . . . . x|/ ..x ..x .x. x.. x..|% x.x ..x .x. x.. x.x
- ... ... xxx ... ...|+ ... .x. xxx .x. ...|! x x x . x|, . . . x x|' x x . . .|> x.. .x. ..x .x. x..
( .x x. x. x. .x|) x. .x .x .x x.|? xx. ..x .x. ... .x.|Ñ xxx ... xx. x.x x.x|_ ... ... ... ... xxx"""
F35 = {}
for _ln in _F35.replace('\n', '|').split('|'):
    _p = _ln.split(' '); F35[_p[0]] = _p[1:]   # fuente, avance entero, desplazamiento a la linea de mayusculas


def glyph(d, name, x, y, col):
    for j, row in enumerate(GL[name]):
        for i, ch in enumerate(row):
            if ch == 'x': d.point((x + i, y + j), fill=col)
    return len(GL[name][0]) + 1


def txt(d, x, y, s, col, f='D'):
    """texto alineado a rejilla: caracter a caracter con avance entero; {xx} = glifo propio."""
    font, adv, off = FONTS[f]
    d.fontmode = "1"
    if f == 'M':   # fuente propia 3x5
        i = 0
        while i < len(s):
            ch = s[i]
            if ch == '{':
                j = s.index('}', i); x += glyph(d, s[i + 1:j], x, y, col); i = j + 1; continue
            g = F35.get(ch.upper())
            if g is None: x += 2; i += 1; continue
            for jj, row in enumerate(g):
                for ii, c in enumerate(row):
                    if c == 'x': d.point((x + ii, y + jj), fill=col)
            x += len(g[0]) + 1; i += 1
        return x
    i = 0
    while i < len(s):
        if s[i] == '{':
            j = s.index('}', i); x += glyph(d, s[i + 1:j], x, y + (1 if f == 'D' else 0), col); i = j + 1; continue
        d.text((x, y - off), s[i], font=font, fill=col)
        x += adv if s[i] != ' ' else adv - 2
        i += 1
    return x


def twidth(s, f='D'):
    im = Image.new('RGBA', (300, 20)); return txt(ImageDraw.Draw(im), 0, 4, s, (255, 255, 255, 255), f) - 1


def rp(n): return [c + (255,) for c in M.R[n]]


def bitmap(ch, font=FD, off=3):
    im = Image.new('1', (12, 16), 0); d = ImageDraw.Draw(im); d.fontmode = "1"
    d.text((0, -off), ch, font=font, fill=1)
    bb = im.getbbox()
    return im, (bb[2] if bb else 4)


LED57 = {  # fuente LED 5x7 clasica (filas de 5 bits)
    '0': [14, 17, 19, 21, 25, 17, 14], '1': [4, 12, 4, 4, 4, 4, 14], '2': [14, 17, 1, 2, 4, 8, 31],
    '3': [31, 2, 4, 2, 1, 17, 14], '4': [2, 6, 10, 18, 31, 2, 2], '5': [31, 16, 30, 1, 1, 17, 14],
    '6': [6, 8, 16, 30, 17, 17, 14], '7': [31, 1, 2, 4, 8, 8, 8], '8': [14, 17, 17, 14, 17, 17, 14],
    '9': [14, 17, 17, 15, 1, 2, 12], ':': [0, 12, 12, 0, 12, 12, 0], ' ': [0] * 7,
    'A': [14, 17, 17, 31, 17, 17, 17], 'C': [14, 17, 16, 16, 16, 17, 14], 'D': [28, 18, 17, 17, 17, 18, 28],
    'E': [31, 16, 16, 30, 16, 16, 31], 'G': [14, 17, 16, 23, 17, 17, 15], 'I': [14, 4, 4, 4, 4, 4, 14],
    'L': [16, 16, 16, 16, 16, 16, 31], 'M': [17, 27, 21, 21, 17, 17, 17], 'N': [17, 17, 25, 21, 19, 17, 17],
    'O': [14, 17, 17, 17, 17, 17, 14], 'P': [30, 17, 17, 30, 16, 16, 16], 'R': [30, 17, 17, 30, 20, 18, 17],
    'S': [15, 16, 16, 14, 1, 1, 30], 'T': [31, 4, 4, 4, 4, 4, 4], 'U': [17, 17, 17, 17, 17, 17, 14],
    'B': [30, 17, 17, 30, 17, 17, 30], 'H': [17, 17, 17, 31, 17, 17, 17], 'Q': [14, 17, 17, 17, 21, 18, 13],
    'V': [17, 17, 17, 17, 17, 10, 4], 'Y': [17, 17, 10, 4, 4, 4, 4], 'Z': [31, 1, 2, 4, 8, 16, 31],
    'F': [31, 16, 16, 30, 16, 16, 16], 'K': [17, 18, 20, 24, 20, 18, 17], 'J': [7, 2, 2, 2, 2, 18, 12],
    'W': [17, 17, 17, 21, 21, 21, 10], 'X': [17, 17, 10, 4, 10, 17, 17], '.': [0, 0, 0, 0, 0, 12, 12],
    '/': [1, 1, 2, 4, 8, 16, 16], '-': [0, 0, 0, 31, 0, 0, 0], '+': [0, 4, 4, 31, 4, 4, 0],
    '!': [4, 4, 4, 4, 4, 0, 4], ',': [0, 0, 0, 0, 12, 4, 8], '>': [8, 4, 2, 1, 2, 4, 8], '%': [24, 25, 2, 4, 8, 19, 3],
}


def led_text(d, x, y, s, acc, pitch=3, dot=2, show_off=True):
    """matriz de LED: cada bit del glifo 5x7 es un punto; los apagados se ven tenues."""
    on1, on2, off = acc[3], acc[2], rp('ink')[2]
    for ch in s:
        rows = LED57.get(ch.upper(), LED57[' '])
        cols = 5
        lo, hi = 0, 5
        if ch == ':': lo, hi = 1, 3
        for j in range(7):
            for i in range(lo, hi):
                px, py = x + (i - lo) * pitch, y + j * pitch
                if rows[j] >> (4 - i) & 1:
                    if dot == 1: d.point((px, py), fill=on2)
                    else: d.rectangle([px, py, px + dot - 1, py + dot - 1], fill=on2); d.point((px, py), fill=on1)
                elif show_off:
                    d.point((px, py), fill=off)
        x += (hi - lo) * pitch + pitch
    return x


def chamf(x0, y0, x1, y1, c):
    return [(x0 + c, y0), (x1 - c, y0), (x1, y0 + c), (x1, y1 - c), (x1 - c, y1), (x0 + c, y1), (x0, y1 - c), (x0, y0 + c)]


def frame(w, h, acc, title=None, tabw=None):
    """marco metalico con bisel, esquinas achaflanadas, filete de neon, tornillos y pestaña de titulo."""
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    ink, sl, mi = rp('ink'), rp('slate'), rp('mist')
    d.polygon(chamf(0, 0, w - 1, h - 1, 3), fill=ink[0])                     # contorno
    d.polygon(chamf(1, 1, w - 2, h - 2, 2), fill=sl[1])                       # cuerpo del marco
    d.line([(3, 1), (w - 4, 1)], fill=mi[1]); d.line([(1, 3), (1, h - 4)], fill=sl[3])      # luz arriba/izq
    d.line([(3, h - 2), (w - 4, h - 2)], fill=ink[2]); d.line([(w - 2, 3), (w - 2, h - 4)], fill=ink[3])  # sombra
    d.point((2, 2), fill=mi[0]); d.point((w - 3, h - 3), fill=ink[2])
    d.rectangle([3, 3, w - 4, h - 4], fill=acc[1])                             # filete de neon
    d.rectangle([4, 4, w - 5, h - 5], fill=ink[0])                             # pantalla
    d.line([(5, 4), (w - 6, 4)], fill=acc[0])                                  # retroiluminacion
    for (x, y) in ((3, 3), (w - 4, 3), (3, h - 4), (w - 4, h - 4)):            # esquinas brillantes
        d.point((x, y), fill=acc[3])
    for (x, y) in ((4, 1), (w - 5, 1), (4, h - 2), (w - 5, h - 2)):            # tornillos
        d.point((x, y), fill=mi[2])
    if title:
        tw = tabw or twidth(title, 'M') + 6
        d.polygon([(6, 0), (6 + tw, 0), (6 + tw, 5), (6 + tw - 2, 7), (6, 7)], fill=acc[2])
        d.line([(6, 0), (6 + tw - 1, 0)], fill=acc[3])
        txt(d, 9, 1, title, ink[0], 'M')
    led = Image.new('L', (w, h), 0); ImageDraw.Draw(led).rectangle([4, 8 if title else 4, w - 5, h - 5], fill=255)
    im.info['led'] = led
    return im, d


def ring(d, cx, cy, load, ramp_ok, ramp_bg):
    for j in range(-5, 6):
        for i in range(-5, 6):
            r = math.hypot(i, j)
            if 3.4 <= r <= 5.45:
                a = (math.atan2(i + .01, -j) / (2 * math.pi)) % 1
                if a < load:
                    c = ramp_ok[3] if r > 4.8 and j < 0 else ramp_ok[2]
                else:
                    c = ramp_bg
                d.point((cx + i, cy + j), fill=c)


def load_ramp(v):
    return rp('grn') if v < .6 else (rp('amb') if v < .85 else rp('red'))


def segbar(d, x, y, n, frac, h=3, pitch=3, grad=True):
    for k in range(n):
        f = (k + .5) / n
        if f <= frac:
            c = load_ramp(f if grad else frac)[2]
            if k == int(frac * n) - 1: c = load_ramp(f if grad else frac)[3]
        else:
            c = rp('ink')[3]
        d.rectangle([x + k * pitch, y, x + k * pitch + pitch - 2, y + h - 1], fill=c)


def series(n, seed, base, var, smooth=.7):
    rnd = random.Random(seed); v = base; out = []
    for _ in range(n):
        v = v * smooth + (base + rnd.uniform(-var, var)) * (1 - smooth); out.append(clamp(v, 0, 1))
    return out


# ---- cartel: reloj + agenda
def s_reloj():
    acc = rp('cyan'); w, h = 100, 58
    im, d = frame(w, h, acc)
    x = led_text(d, 8, 8, DATA['hora'], acc)
    # segundero: barra de progreso de puntos
    for k in range(28):
        d.point((10 + k * 3, 30), fill=acc[2] if k < 17 else acc[0])
    mg = rp('mag')
    dia_, resto = DATA['fecha'].split(' ', 1)
    txt(d, 10, 34, dia_, mg[3]); txt(d, 10 + 7 * 4, 34, resto, acc[3])
    for xx in range(6, w - 6, 2): d.point((xx, 44), fill=rp('slate')[1])
    am = rp('amb')
    glyph(d, 'tri', 8, 47, am[2])
    x = txt(d, 13, 47, '22:00', am[3], 'M'); txt(d, x + 3, 47, 'COPIA DATOS', rp('mist')[2], 'M'); txt(d, w - 15, 47, '+2', acc[2], 'M')
    return im


# ---- cartel: CPU por nucleo
def s_cpu():
    acc = rp('mag'); w, h = 108, 50
    im, d = frame(w, h, acc, 'CPU')
    loads = [.62, .35, .91, .41, .23, .57, .74, .30]
    tot = sum(loads) / len(loads)
    txt(d, w - 7 - twidth('47%'), 10, '47%', acc[3]); txt(d, 7, 11, '8 NUCLEOS 3.8GHZ', rp('mist')[2], 'M')
    for k, l in enumerate(loads):
        cx = 11 + k * 12; cy = 25
        ring(d, cx, cy, l, load_ramp(l), rp('ink')[3])
        d.point((cx, cy), fill=load_ramp(l)[1])
        s = str(int(l * 100))
        txt(d, cx - 3, 33, s, rp('mist')[3] if l < .85 else rp('red')[3], 'M')
    # historico de carga total (barras finas)
    hist = series(48, 4, .47, .5, .5)
    for k, v in enumerate(hist):
        hh = 1 + int(v * 5)
        c = load_ramp(v)
        d.line([(6 + k * 2, 45), (6 + k * 2, 45 - hh + 1)], fill=c[0]); d.point((6 + k * 2, 45 - hh + 1), fill=c[2])
    return im


# ---- cartel: red
def s_net():
    acc = rp('cyan'); w, h = 84, 46
    im, d = frame(w, h, acc, 'NET')
    mg = rp('mag')
    # icono wifi en barras
    for k in range(4):
        d.rectangle([w - 18 + k * 3, 6 - k, w - 17 + k * 3, 6], fill=acc[2] if k < 3 else acc[0])
    glyph(d, 'dn', 7, 13, acc[3]); txt(d, 14, 11, '4.2', acc[3]); txt(d, 37, 13, 'MB/S', acc[2], 'M')
    glyph(d, 'up', 7, 22, mg[3]); txt(d, 14, 20, '0.3', mg[3]); txt(d, 37, 22, 'MB/S', mg[2], 'M')
    txt(d, 58, 13, 'IP OK', rp('grn')[2], 'M'); txt(d, 58, 22, '12MS', rp('mist')[2], 'M')
    # grafica: rejilla punteada, area de bajada con tramado, linea de subida
    gx, gy, gw, gh = 6, 29, w - 12, 12
    for xx in range(gx, gx + gw, 4):
        for yy in range(gy, gy + gh, 4): d.point((xx, yy), fill=rp('ink')[3])
    dn = series(gw, 9, .45, .9, .82); up = series(gw, 5, .18, .3, .8)
    for k in range(gw):
        top = gy + gh - 1 - int(dn[k] * (gh - 1))
        for yy in range(top + 1, gy + gh):
            d.point((gx + k, yy), fill=acc[0] if yy > top + 1 or k % 2 else acc[1])
        d.point((gx + k, top), fill=acc[2])
        uy = gy + gh - 1 - int(up[k] * (gh - 1))
        d.point((gx + k, uy), fill=mg[2])
    d.point((gx + gw - 1, gy + gh - 1 - int(dn[-1] * (gh - 1))), fill=rp('wht')[1])
    return im


# ---- cartel: RAM / GPU / disco
def s_ram():
    acc = rp('vio'); w, h = 92, 50
    im, d = frame(w, h, acc, 'SISTEMA')
    mi = rp('mist')
    rows = [('RAM', '10.2/16G', .64), ('GPU', '41% 58{deg}C', .41), ('DISCO /', '62%', .62)]
    y = 10
    for lab, val, fr in rows:
        txt(d, 7, y, lab, mi[3], 'M')
        txt(d, w - 6 - twidth(val, 'M'), y, val, acc[3], 'M')
        segbar(d, 7, y + 7, 26, fr, h=3, pitch=3)
        y += 13
    return im


# ---- cartel: VPN en tubo de neon
def s_vpn():
    g = rp('grn'); w, h = 66, 40
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    ink = rp('ink')
    d.polygon(chamf(0, 0, w - 1, h - 1, 2), fill=ink[0])
    for yy in range(2, h - 2, 2):                       # chapa perforada de soporte
        for xx in range(2 + (yy // 2) % 2, w - 2, 2): d.point((xx, yy), fill=ink[1])
    d.line([(2, 0), (w - 3, 0)], fill=rp('slate')[2]); d.line([(2, h - 1), (w - 3, h - 1)], fill=ink[2])
    # escudo con check
    sh = ["xxxxxxxxx", "x.......x", "x.......x", "x......xx", "x.....x.x", "xx...x..x", "x.x.x...x", ".x.x...x.", ".x.....x.", "..x...x..", "...x.x...", "....x...."]
    for j, row in enumerate(sh):
        for i, ch in enumerate(row):
            if ch == 'x': d.point((5 + i, 6 + j), fill=g[2] if not (5 <= i and 3 <= j <= 7 or (i, j) in ((1, 5), (2, 6), (3, 7))) else g[3])
    # letras de tubo: glifo x2, contorno oscuro + nucleo brillante
    mask = Image.new('1', (60, 20), 0); md = ImageDraw.Draw(mask); md.fontmode = "1"
    md.text((0, -3), 'VPN', font=FD, fill=1)
    mask = mask.crop((0, 0, 21, 8)).resize((42, 16), Image.NEAREST)
    outer = mask.filter(ImageFilter.MaxFilter(3))
    ox, oy = 18, 5
    for yy in range(18):
        for xx in range(44):
            if xx < 42 and yy < 16 and mask.getpixel((xx, yy)):
                up_ = yy > 0 and mask.getpixel((xx, yy - 1))
                d.point((ox + xx, oy + yy), fill=g[2] if up_ else g[3])
            elif xx < 42 and yy < 16 and outer.getpixel((xx, yy)):
                d.point((ox + xx, oy + yy), fill=g[0])
    txt(d, 6, 27, 'ACTIVA', g[3], 'M'); glyph(d, 'ok', 31, 27, g[2])
    txt(d, 40, 27, 'WG0', rp('mist')[2], 'M')
    for xx in range(4, w - 4, 3): d.point((xx, 35), fill=g[0])
    return im


# ---- cartel: git
def s_git():
    acc = rp('amb'); w, h = 72, 42
    im, d = frame(w, h, acc, 'GIT')
    # grafo de ramas
    c1, c2 = acc[2], rp('mag')[2]
    for y in range(11, 37): d.point((10, y), fill=c1)
    for (x, y) in ((11, 30), (12, 29), (13, 28), (14, 27), (14, 26), (14, 25), (14, 24), (14, 23), (13, 22), (12, 21), (11, 20)):
        d.point((x, y), fill=c2)
    for y in (13, 20, 30, 35):
        d.rectangle([9, y - 1, 11, y + 1], fill=acc[3]); d.point((10, y), fill=rp('ink')[0])
    d.rectangle([13, 24, 15, 26], fill=rp('mag')[3])
    txt(d, 19, 10, '3', acc[3]); txt(d, 28, 12, 'REPOS', rp('mist')[3], 'M')
    txt(d, 19, 19, 'CON CAMBIOS', rp('mist')[2], 'M')
    x = txt(d, 19, 26, '+12', rp('grn')[2], 'M'); txt(d, x + 3, 26, '-3', rp('red')[2], 'M')
    glyph(d, 'up', 19, 33, acc[2]); txt(d, 26, 33, '1 SIN PUSH', acc[2], 'M')
    return im


# ---- cartel: bateria + temperatura
def s_bat():
    acc = rp('mag'); w, h = 64, 40
    im, d = frame(w, h, acc, 'ENERGIA')
    g = rp('grn')
    d.rectangle([7, 11, 27, 19], outline=g[2]); d.rectangle([28, 13, 29, 17], fill=g[2])
    for k in range(5):
        d.rectangle([9 + k * 4, 13, 11 + k * 4, 17], fill=g[3] if k < 4 else rp('ink')[3])
    txt(d, 33, 12, '78%', rp('wht')[1])
    am, rd = rp('amb'), rp('red')
    th = [".x.", "x.x", "x.x", "x.x", "xxx", "xxx", "xxx", "xxx", ".x."]
    for j, row in enumerate(th):
        for i, ch in enumerate(row):
            if ch == 'x': d.point((9 + i, 24 + j), fill=rd[2] if j >= 3 else rp('mist')[2])
    txt(d, 15, 25, '52', am[3]); glyph(d, 'deg', 29, 25, am[3]); txt(d, 33, 25, 'C', am[3])
    txt(d, 43, 27, 'CPU', rp('mist')[2], 'M')
    for k in range(10): d.point((8 + k * 5, 35), fill=load_ramp(k / 10)[1])
    return im


SIGNS.update({'reloj': s_reloj, 'cpu': s_cpu, 'net': s_net, 'ram': s_ram, 'vpn': s_vpn, 'git': s_git, 'bat': s_bat})


# ---- etiquetas pequeñas (drones, azoteas)
def tag(text, acc, icon=None):
    w = twidth(text, 'M') + 8 + (8 if icon else 0); h = 11
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.polygon(chamf(0, 0, w - 1, h - 1, 2), fill=acc[1]); d.rectangle([1, 1, w - 2, h - 2], fill=rp('ink')[0])
    d.point((1, 1), fill=acc[3]); d.point((w - 2, h - 2), fill=acc[3])
    x = 4
    if icon: x += glyph(d, icon, 4, 3, acc[3]) + 1
    txt(d, x, 3, text, acc[3], 'M')
    led = Image.new('L', (w, h), 0); ImageDraw.Draw(led).rectangle([1, 1, w - 2, h - 2], fill=255); im.info['led'] = led
    return im


# ---- pantallas decorativas (anuncios) para dar vida
def s_kana(text, acc, w=20):
    """banderola vertical con katakana (DotGothic16)."""
    h = len(text) * 17 + 6
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im); d.fontmode = "1"
    d.rectangle([0, 0, w - 1, h - 1], fill=acc[1]); d.rectangle([1, 1, w - 2, h - 2], fill=rp('ink')[0])
    for i, ch in enumerate(text):
        d.text((2, 3 + i * 17 - 5), ch, font=FJ, fill=acc[3] if i % 2 == 0 else acc[2])
    led = Image.new('L', (w, h), 0); ImageDraw.Draw(led).rectangle([1, 1, w - 2, h - 2], fill=255); im.info['led'] = led
    return im


def s_ad(w, h, acc, acc2, seed, kana=None):
    """anuncio: degradado tramado + franjas + kana grande."""
    rnd = random.Random(seed)
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im); d.fontmode = "1"
    d.rectangle([0, 0, w - 1, h - 1], fill=rp('ink')[1])
    for y in range(1, h - 1):
        t = y / h
        for x in range(1, w - 1):
            b = BAYER[y % 4][x % 4] / 16
            d.point((x, y), fill=acc[1] if t < .35 + b * .3 else (acc[0] if t < .75 + b * .25 else rp('ink')[0]))
    for k in range(rnd.randint(2, 4)):
        yy = rnd.randint(2, h - 4); d.line([(1, yy), (w - 2, yy)], fill=acc2[2])
    if kana:
        x = (w - 16 * len(kana)) // 2
        for i, ch in enumerate(kana): d.text((x + i * 16, (h - 16) // 2 - 5), ch, font=FJ, fill=rp('wht')[1])
    d.rectangle([0, 0, w - 1, h - 1], outline=acc[3])
    led = Image.new('L', (w, h), 0); ImageDraw.Draw(led).rectangle([1, 1, w - 2, h - 2], fill=255); im.info['led'] = led
    return im


# ================================================================== CIELO VIVO: zepelin y drones
TIPS = 'CONSEJO: HAZ COMMIT A MENUDO  +  GUARDA COPIA DE TUS DATOS  +  CTRL+ALT+T ABRE LA TERMINAL  +  '


def draw_zeppelin(cx=372, cy=58, scroll=58):
    night = M.name == 'noche'
    rx, ry = 104, 23
    sh = [R('ink', 2), R('slate', 0), R('slate', 1), R('slate', 2), R('slate', 3)]
    px = S.img.load()
    # aletas (detras)
    fins = [([cx - rx + 10, cy - 4], [cx - rx - 16, cy - 27], [cx - rx + 4, cy - 26], [cx - rx + 30, cy - 9]),
            ([cx - rx + 10, cy + 4], [cx - rx - 16, cy + 26], [cx - rx + 4, cy + 25], [cx - rx + 30, cy + 9])]
    for pts, c in zip(fins, (R('slate', 0), R('ink', 3))):
        poly([tuple(p) for p in pts], c, crisp=True)
        S.d.line([tuple(pts[1]), tuple(pts[2])], fill=R('mist', 1))
    # casco con sombreado por rampas y bordes tramados
    for y in range(cy - ry, cy + ry + 1):
        for x in range(cx - rx, cx + rx + 1):
            nx, ny = (x - cx) / rx, (y - cy) / ry
            r2 = nx * nx + ny * ny
            if r2 > 1: continue
            nz = math.sqrt(1 - r2)
            lum = .55 * nz - .5 * ny - .15 * nx + .05
            lum += (BAYER[y % 4][x % 4] / 16 - .5) * .18
            k = int(clamp(lum * 3.2 + 1.2, 0, 4))
            c = sh[k]
            if r2 > .86 and ny > .2: c = R('mag', 1) if x > cx - 30 else R('vio', 1)   # luz de la ciudad desde abajo
            if r2 > .93 and ny > .45: c = R('mag', 2)
            # costillas
            if (x - cx) % 18 == 0 and abs(nx) < .9: c = sh[max(0, k - 1)]
            S.img.putpixel((x, y), c); S.K.putpixel((x, y), 255); S.G.putpixel((x, y), 0)
    # contorno superior oscuro
    for x in range(cx - rx, cx + rx + 1):
        nx = (x - cx) / rx
        if abs(nx) <= 1:
            yt = round(cy - ry * math.sqrt(1 - nx * nx))
            pix(x, yt - 1, R('ink', 1), crisp=True)
    # aleta lateral (delante)
    poly([(cx - rx + 14, cy + 1), (cx - rx - 10, cy + 3), (cx - rx - 8, cy + 6), (cx - rx + 26, cy + 5)], R('slate', 2), crisp=True)
    # gondola
    gx0, gx1, gy = cx - 22, cx + 26, cy + ry - 3
    poly([(gx0, gy), (gx1, gy), (gx1 - 3, gy + 9), (gx0 + 3, gy + 9)], R('ink', 3), crisp=True)
    S.d.line([(gx0, gy), (gx1, gy)], fill=R('slate', 3))
    for k in range(gx0 + 4, gx1 - 3, 3): pix(k, gy + 4, R('amb', 3) if k % 2 else R('cyan', 3), emis=True, crisp=True)
    # haz de busqueda hacia la niebla (cono tramado)
    lay = Image.new('L', (W, H), 0); dl = ImageDraw.Draw(lay)
    bx, by = cx + 6, gy + 9
    if night:
        dl.polygon([(bx - 2, by), (bx + 2, by), (bx + 60, by + 150), (bx + 6, by + 158)], fill=34)
        dl.polygon([(bx - 1, by), (bx + 1, by), (bx + 40, by + 152), (bx + 18, by + 156)], fill=30)
        S.img = Image.composite(ImageChops.add(S.img, Image.new('RGB', (W, H), (90, 150, 170))), S.img, lay); S.d = ImageDraw.Draw(S.img)
    # pantalla LED con consejos desplazandose
    sw, shh = 136, 22
    sx0, sy0 = cx - sw // 2 + 6, cy - shh // 2 - 1
    scr = Image.new('RGBA', (sw, shh), (0, 0, 0, 0)); d = ImageDraw.Draw(scr)
    d.rectangle([0, 0, sw - 1, shh - 1], fill=R('ink', 0) + (255,))
    d.rectangle([0, 0, sw - 1, shh - 1], outline=R('amb', 1) + (255,))
    for (x, y) in ((0, 0), (sw - 1, 0), (0, shh - 1), (sw - 1, shh - 1)): d.point((x, y), fill=R('amb', 3) + (255,))
    strip = Image.new('RGBA', (len(TIPS) * 12 + 12, 14), (0, 0, 0, 0)); sd = ImageDraw.Draw(strip)
    led_text(sd, 0, 0, TIPS, rp('amb'), pitch=2, dot=1, show_off=False)
    # rejilla de LED apagados
    for y in range(4, shh - 4, 2):
        for x in range(3, sw - 3, 2): d.point((x, y), fill=R('ink', 2) + (255,))
    for k in (0, 1):
        scr.paste(strip.crop((0, 0, strip.width, 14)), (3 - scroll + k * (len(TIPS) * 12), 4), strip.crop((0, 0, strip.width, 14)))
    d.rectangle([0, 0, 2, shh - 1], fill=R('ink', 0) + (255,)); d.rectangle([sw - 3, 0, sw - 1, shh - 1], fill=R('ink', 0) + (255,))
    d.rectangle([0, 0, sw - 1, shh - 1], outline=R('amb', 1) + (255,))
    for (x, y) in ((0, 0), (sw - 1, 0), (0, shh - 1), (sw - 1, shh - 1)): d.point((x, y), fill=R('amb', 3) + (255,))
    led = Image.new('L', (sw, shh), 0); ImageDraw.Draw(led).rectangle([1, 1, sw - 2, shh - 2], fill=255)
    S.img.paste(scr, (sx0, sy0), scr); S.E.paste(scr, (sx0, sy0), scr); S.B.paste(scr, (sx0, sy0), scr); S.K.paste(255, (sx0, sy0, sx0 + sw, sy0 + shh))
    LEDMASK.paste(led, (sx0, sy0))
    halo_rect(sx0, sy0, sw, shh, R('amb', 1), .9)
    # luces de navegacion
    pix(cx + rx - 1, cy - 3, R('red', 2), emis=True, crisp=True); pix(cx - rx + 2, cy - 2, R('grn', 2), emis=True, crisp=True)
    pix(cx - rx - 15, cy - 27, R('wht', 1), emis=True, crisp=True)
    S.d = ImageDraw.Draw(S.img)


def halo_rect(x0, y0, w, h, col, k=1.0):
    for r, a in ((6, .06 * k), (3, .10 * k), (1, .16 * k)):
        lay = Image.new('L', (W, H), 0)
        ImageDraw.Draw(lay).rectangle([x0 - r, y0 - r, x0 + w + r - 1, y0 + h + r - 1], fill=int(255 * a))
        ImageDraw.Draw(lay).rectangle([x0, y0, x0 + w - 1, y0 + h - 1], fill=0)
        S.img = Image.composite(ImageChops.add(S.img, Image.new('RGB', (W, H), col)), S.img, lay)
    S.d = ImageDraw.Draw(S.img)


DRONE = ["x.....x", "xx.x.xx", "..xxx..", "...x..."]


def draw_drone(x, y, label=None, acc=None, icon=None, blink=True):
    for j, row in enumerate(DRONE):
        for i, ch in enumerate(row):
            if ch == 'x': pix(x + i, y + j, R('slate', 3) if j == 0 else R('ink', 3), crisp=True)
    pix(x + 3, y + 3, R('red', 2) if blink else R('grn', 2), emis=True, crisp=True)
    if label:
        S.d.line([(x + 3, y + 4), (x + 3, y + 7)], fill=R('slate', 1))
        im = tag(label, rp(acc), icon)
        tx = x + 3 - im.width // 2
        S.img.paste(im, (tx, y + 8), im); S.E.paste(im, (tx, y + 8), im); S.B.paste(im, (tx, y + 8), im); S.K.paste(255, (tx, y + 8, tx + im.width, y + 8 + im.height))
        LEDMASK.paste(im.info['led'], (tx, y + 8), im.info['led'])
        halo_rect(tx, y + 8, im.width, im.height, R(acc, 1), .7)


# ================================================================== POSTPROCESO
def reflections():
    """calle mojada: cada pixel de suelo recoge las luces que tiene encima (estela vertical)."""
    acc = Image.new('RGB', (W, H))
    for k, sh in enumerate(range(2, 60, 3)):
        dim = Image.eval(ImageChops.offset(S.E, 0, sh), lambda v, f=(1 - sh / 62) * .62: int(v * f))
        acc = ImageChops.lighter(acc, dim)
    # rizado: filas alternas mas tenues (agua), mascara de suelo
    rip = Image.new('L', (W, H), 0); dr = ImageDraw.Draw(rip)
    rnd = random.Random(5)
    for y in range(HY, H):
        a = 255 if y % 2 else 150
        dr.line([(0, y), (W, y)], fill=a)
    m = ImageChops.multiply(S.G, rip)
    S.img = Image.composite(ImageChops.lighter(S.img, acc), S.img, m); S.d = ImageDraw.Draw(S.img)


def bloom(k=1.0):
    """halo de neon: el emisivo desenfocado se suma y luego el tramado lo convierte en escalones."""
    g1 = S.B.filter(ImageFilter.BoxBlur(2)); g2 = S.B.filter(ImageFilter.BoxBlur(7))
    g = ImageChops.add(Image.eval(g1, lambda v: int(v * .30 * k)), Image.eval(g2, lambda v: int(v * .34 * k)))
    out = ImageChops.add(S.img, g)
    S.img = Image.composite(S.img, out, S.K); S.d = ImageDraw.Draw(S.img)


def calm_left():
    """oscurece la zona de iconos (izquierda) en degradado."""
    lay = Image.new('L', (W, H), 0); px = lay.load()
    for x in range(0, 380):
        a = int(255 * (1 - x / 380) ** 1.4 * .62)
        for y in range(H): px[x, y] = a
    S.img = Image.composite(Image.new('RGB', (W, H), R('ink', 0)), S.img, lay); S.d = ImageDraw.Draw(S.img)


def rain(img, seed=1, n_far=900, n_near=160):
    d = ImageDraw.Draw(img); rnd = random.Random(seed)
    for _ in range(n_far):
        x, y = rnd.randrange(W), rnd.randrange(16, H)
        d.line([(x, y), (x, y + 2)], fill=R('slate', 1) if y < HY else R('slate', 2))
    for _ in range(n_near):
        x, y = rnd.randrange(W), rnd.randrange(16, H)
        d.line([(x, y), (x - 1, y + 5)], fill=R('slate', 3))
        d.point((x - 1, y + 5), fill=R('mist', 1))


def splashes(img, seed=2):
    d = ImageDraw.Draw(img); rnd = random.Random(seed); g = S.G.load()
    for _ in range(500):
        x, y = rnd.randrange(1, W - 1), rnd.randrange(HY + 40, H - 1)
        if g[x, y] > 0:
            d.point((x - 1, y), fill=R('slate', 3)); d.point((x + 1, y), fill=R('slate', 3)); d.point((x, y - 1), fill=R('mist', 1))


def led_grid(big, ledm):
    """rejilla de LED visible solo dentro de las pantallas (a resolucion final)."""
    pat = Image.new('L', big.size)
    row0 = Image.new('L', (big.width, 1)); row0.putdata([255 if x % 2 == 0 else 196 for x in range(big.width)])
    row1 = Image.new('L', (big.width, 1)); row1.putdata([196 if x % 2 == 0 else 150 for x in range(big.width)])
    for y in range(big.height): pat.paste(row0 if y % 2 == 0 else row1, (0, y))
    dark = ImageChops.multiply(big, Image.merge('RGB', (pat, pat, pat)))
    return Image.composite(dark, big, ledm.resize(big.size, Image.NEAREST))


# ================================================================== BARRA SUPERIOR E ICONOS (portado de concepto.py)
CY = (0, 229, 255); MG = (255, 43, 214); GR = (57, 255, 136)
AM = (255, 176, 32); RD = (255, 59, 92); VI = (139, 92, 255)
ICONS = {
    'shield': ["XXXXXXXXX", "XXXXXXXoX", "XXoXXXoXX", "XXXoXoXXX", ".XXXoXXX.", ".XXXXXXX.", "..XXXXX..", "...XXX...", "....X...."],
    'sync': ["..XXXXX..", ".X.....X.", "X.....XXX", "X......X.", "X........", "X..X.....", ".XXXX...X", "..XXXXXX.", "........."],
    'vol': ["...X.....", "..XX..X..", ".XXX...X.", "XXXX.X.X.", "XXXX.X.X.", ".XXX...X.", "..XX..X..", "...X.....", "........."],
    'wifi': ["..XXXXX..", ".X.....X.", "X..XXX..X", "..X...X..", "...XXX...", "....X....", ".........", "....X....", "........."],
    'power': ["....X....", "..X.X.X..", ".X..X..X.", "X...X...X", "X.......X", "X.......X", ".X.....X.", "..XXXXX..", "........."],
    'term': ["XXXXXXXXX", "X.......X", "X.X.....X", "X..X....X", "X.X...XXX", "X.......X", "X.......X", "XXXXXXXXX", "........."],
    'folder': ["XXXX.....", "X..XXXXXX", "X.......X", "X.......X", "X.......X", "X.......X", "X.......X", "XXXXXXXXX", "........."],
    'globe': ["..XXXXX..", ".X..X..X.", "X...X...X", "XXXXXXXXX", "X...X...X", "X...X...X", ".X..X..X.", "..XXXXX..", "........."],
    'code': ["..X...X..", ".X.....X.", "X...X...X", "X..X....X", "X...X...X", ".X.....X.", "..X...X..", ".........", "........."],
}


def icon(d, name, x, y, c1, c2=None, s=2):
    for j, row in enumerate(ICONS[name]):
        for i, ch in enumerate(row):
            if ch in 'Xo':
                col = c1 if ch == 'X' else (c2 or (11, 14, 26))
                d.rectangle([x + i * s, y + j * s, x + i * s + s - 1, y + j * s + s - 1], fill=col)


def chamfer(x0, y0, x1, y1, c=4):
    return [(x0 + c, y0), (x1 - c, y0), (x1, y0 + c), (x1, y1 - c), (x1 - c, y1), (x0 + c, y1), (x0, y1 - c), (x0, y0 + c)]


def draw_bar(img, clock='21:37', date='MAR 10 NOV'):
    d = ImageDraw.Draw(img); d.fontmode = "1"; Wd = img.width; F14 = FB14
    BG, PAN, TXT = (11, 14, 26), (18, 23, 43), (230, 241, 255)
    for y in range(32):
        d.line([(0, y), (Wd, y)], fill=mix((20, 25, 47), (10, 12, 24), y / 31))
    d.line([(0, 31), (Wd, 31)], fill=mix(CY, BG, .35)); d.line([(0, 30), (Wd, 30)], fill=mix(CY, BG, .78))
    for i, a in enumerate((.14, .08, .04)):
        for x in range(Wd):
            img.putpixel((x, 32 + i * 2), mix(img.getpixel((x, 32 + i * 2)), CY, a)); img.putpixel((x, 33 + i * 2), mix(img.getpixel((x, 33 + i * 2)), CY, a * .6))
    cx = 18
    hexp = [(cx - 8, 5), (cx + 8, 5), (cx + 15, 16), (cx + 8, 27), (cx - 8, 27), (cx - 15, 16)]
    d.polygon(hexp, fill=mix(CY, BG, .82), outline=CY)
    d.polygon([(cx - 9, 8), (cx + 9, 8), (cx + 12, 16), (cx + 9, 24), (cx - 9, 24), (cx - 12, 16)], outline=mix(CY, BG, .55))
    d.text((cx - 8, 9), ">_", font=F14, fill=CY)
    sep = lambda x: d.line([(x, 8), (x, 23)], fill=mix(VI, BG, .45))
    sep(42)
    for i in range(4):
        x = 56 + i * 20; y = 16
        r = [(x, y - 6), (x + 6, y), (x, y + 6), (x - 6, y)]
        if i == 1:
            d.polygon(r, fill=CY); d.polygon([(x, y - 9), (x + 9, y), (x, y + 9), (x - 9, y)], outline=mix(CY, BG, .6))
        else: d.polygon(r, outline=mix(VI, TXT, .1))
    sep(142)
    apps = [('term', CY, 'open'), ('folder', VI, 'open'), ('globe', CY, 'attn'), ('code', CY, None)]
    for i, (nm, col, st) in enumerate(apps):
        x = 154 + i * 34; y = 4
        d.polygon(chamfer(x, y, x + 25, y + 24, 3), fill=PAN, outline=mix(col, BG, .55))
        d.line([(x + 4, y + 1), (x + 20, y + 1)], fill=mix(col, TXT, .3))
        icon(d, nm, x + 4, y + 4, col, s=2)
        if st == 'open': d.rectangle([x + 3, 28, x + 22, 29], fill=CY)
        if st == 'attn': d.rectangle([x + 3, 28, x + 22, 29], fill=MG); d.rectangle([x + 20, y - 1, x + 25, y + 4], fill=MG)
    cxm = Wd // 2; x0, x1 = cxm - 130, cxm + 130
    d.polygon([(x0 - 14, 0), (x1 + 14, 0), (x1 + 2, 29), (x0, 29)], fill=(8, 10, 21))
    d.polygon([(x0 - 8, 0), (x1 + 8, 0), (x1 - 2, 27), (x0 + 2, 27)], fill=mix(PAN, BG, .5), outline=mix(CY, BG, .4))
    d.line([(x0 - 8, 0), (x0 + 2, 27)], fill=CY); d.line([(x1 + 8, 0), (x1 - 2, 27)], fill=CY)
    d.line([(x0 + 2, 27), (x1 - 2, 27)], fill=mix(CY, BG, .3))
    tx = f"{clock}  ·  {date}"; w = d.textlength(tx, font=F14)
    d.text((cxm - w / 2, 7), clock, font=F14, fill=TXT)
    wc = d.textlength(clock + "  ", font=F14)
    d.text((cxm - w / 2 + wc, 7), "·", font=F14, fill=MG)
    d.text((cxm - w / 2 + wc + 14, 7), date, font=F14, fill=mix(CY, TXT, .55))
    x = Wd - 18
    icon(d, 'power', x - 12, 7, MG); x -= 36; sep(x + 14)
    bx = x - 44; d.rectangle([bx, 10, bx + 33, 22], outline=GR); d.rectangle([bx + 34, 14, bx + 36, 18], fill=GR)
    for i in range(6):
        d.rectangle([bx + 3 + i * 5, 12, bx + 5 + i * 5, 20], fill=GR if i < 5 else mix(GR, BG, .75))
    d.text((bx - 36, 9), "78%", font=F14, fill=TXT); x = bx - 46; sep(x + 4)
    x -= 26; icon(d, 'wifi', x, 7, CY)
    x -= 28; icon(d, 'vol', x, 7, CY)
    x -= 28; icon(d, 'sync', x, 7, CY)
    x -= 28; icon(d, 'shield', x, 7, GR, (11, 14, 26))
    for (a, b) in (((0, 0), (5, 0)), ((0, 0), (0, 5)), ((Wd - 1, 0), (Wd - 6, 0)), ((Wd - 1, 0), (Wd - 1, 5))):
        d.line([a, b], fill=CY)
    return img


def desktop_icons(big):
    d = ImageDraw.Draw(big); d.fontmode = "1"; F14 = FB14
    names = ['Proyectos', 'Documentos', 'Descargas', 'Imagenes', 'Musica', 'Papelera', 'Notas', 'Backups', 'Videos', 'Blog']
    for n, nm in enumerate(names):
        c, r = divmod(n, 6); x0 = 40 + c * 150; y0 = 70 + r * 150
        if n == 1: d.polygon(chamfer(x0 - 22, y0 - 10, x0 + 98, y0 + 108, 6), fill=mix(CY, (11, 14, 26), .82), outline=mix(CY, (11, 14, 26), .3))
        d.polygon([(x0, y0 + 6), (x0 + 24, y0 + 6), (x0 + 30, y0 + 12), (x0 + 38, y0 + 12), (x0 + 38, y0 + 18), (x0, y0 + 18)], fill=(120, 84, 200))
        d.polygon([(x0, y0 + 16), (x0 + 76, y0 + 16), (x0 + 76, y0 + 62), (x0, y0 + 62)], fill=(84, 56, 150))
        d.rectangle([x0, y0 + 16, x0 + 76, y0 + 18], fill=(170, 130, 255)); d.rectangle([x0, y0 + 56, x0 + 76, y0 + 62], fill=(52, 34, 98))
        d.rectangle([x0 + 3, y0 + 21, x0 + 73, y0 + 59], outline=(110, 76, 190)); d.line([(x0, y0 + 16), (x0 + 6, y0 + 16)], fill=CY)
        if n in (0, 3): d.rectangle([x0 + 10, y0 + 10, x0 + 60, y0 + 17], fill=(236, 240, 255))
        w = d.textlength(nm, font=F14); tx = x0 + 38 - w / 2
        d.text((tx + 1, y0 + 74), nm, font=F14, fill=(0, 0, 0)); d.text((tx, y0 + 73), nm, font=F14, fill=(230, 241, 255))


# ================================================================== COMPOSICION
def render(mode='noche', T=0):
    global LEDMASK
    M.name = mode; M.R = RAMPS_N if mode == 'noche' else RAMPS_D
    LEDMASK = Image.new('L', (W, H), 0); DETAIL_BOXES.clear()
    build_city_layer()
    reflections()
    draw_zeppelin(scroll=94 + T * 2)
    draw_drone(548, 150, 'UPD 12', 'amb', blink=T % 2 == 0)
    draw_drone(806, 150, 'SRV 1', 'red', 'no', blink=T % 2 == 1)
    draw_drone(470, 104, 'SYNC', 'grn', 'ok')
    for (x, y) in ((610, 70), (720, 128), (300, 160), (830, 96), (930, 150)): draw_drone(x, y, blink=(x + T) % 3 == 0)
    bloom(1.0 if mode == 'noche' else .45)
    calm_left()
    q, n = quantize(S.img, S.K, amp=24)
    if mode == 'noche':
        splashes(q); rain(q)
    else:
        rain(q, n_far=500, n_near=60)
    big = q.resize((W * 2, H * 2), Image.NEAREST)
    big = led_grid(big, LEDMASK)
    return q, big, n


def main():
    what = sys.argv[1] if len(sys.argv) > 1 else 'todo'
    os.makedirs(HERE, exist_ok=True)
    if what in ('noche', 'todo'):
        q, big, n = render('noche')
        detail(big)
        draw_bar(big, '21:37', 'MAR 10 NOV'); desktop_icons(big)
        big.save(os.path.join(HERE, 'propuesta-noche.png')); q.save(os.path.join(HERE, 'trabajo-960x600-noche.png'))
        print('noche ok, colores de paleta:', n)
    if what in ('dia', 'todo'):
        DATA.update(hora='08:12', fecha='MIE 11 NOV')
        q, big, n = render('dia')
        draw_bar(big, '08:12', 'MIE 11 NOV'); desktop_icons(big)
        big.save(os.path.join(HERE, 'propuesta-dia.png'))
        print('dia ok')


def detail(big):
    """4 carteles ampliados x4 respecto a la pantalla (incluye la rejilla LED y el halo escalonado)."""
    want = ['reloj', 'cpu', 'net', 'vpn']
    boxes = {n: b for n, b in DETAIL_BOXES}
    out = Image.new('RGB', (1920, 1200), (6, 7, 16)); d = ImageDraw.Draw(out); d.fontmode = "1"
    cells = [(0, 0), (960, 0), (0, 600), (960, 600)]
    for (cx, cy), n in zip(cells, want):
        x0, y0, x1, y1 = boxes[n]
        pad = 3
        crop = big.crop(((x0 - pad) * 2, (y0 - pad) * 2, (x1 + pad) * 2, (y1 + pad) * 2))
        k = min(4, (940) // crop.width, (560) // crop.height)
        crop = crop.resize((crop.width * k, crop.height * k), Image.NEAREST)
        out.paste(crop, (cx + (960 - crop.width) // 2, cy + 30 + (570 - crop.height) // 2))
        d.text((cx + 16, cy + 8), f"{n}  (x{k} sobre la pantalla final)", font=FB14, fill=(170, 248, 255))
    out.save(os.path.join(HERE, 'detalle-carteles.png'))


DETAIL_BOXES = []  # se calculan al montar los carteles

if __name__ == '__main__':
    main()
