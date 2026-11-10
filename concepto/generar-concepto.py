#!/usr/bin/env python3
"""Concepto visual de NeonGrid (solo boceto; el generador final no usara Pillow)."""
import math, random, re, sys, os
from PIL import Image, ImageDraw, ImageFont, ImageChops

W, H = 960, 600
OX, OY = 480, 150
FONT = os.path.join(os.path.expanduser(os.environ.get('NG_FUENTES', '~/.local/share/fonts/neongrid-build')), 'DepartureMono-Regular.otf')
F11 = ImageFont.truetype(FONT, 11)
F14 = ImageFont.truetype(FONT, 14)
OUT = os.path.dirname(os.path.abspath(__file__))

CY = (0, 229, 255); MG = (255, 43, 214); GR = (57, 255, 136)
AM = (255, 176, 32); RD = (255, 59, 92); VI = (139, 92, 255)


def mix(a, b, t): return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))
def mul(c, k): return tuple(max(0, min(255, int(v * k))) for v in c)
def P(x, y, z=0): return (round(OX + (x - y) * 12), round(OY + (x + y) * 6 - z))
def clamp(v, a, b): return max(a, min(b, v))


MODES = {
    'noche': dict(sky=[(0, (4, 5, 18)), (.5, (24, 11, 56)), (1, (120, 26, 118))], haze=(62, 24, 98),
                  tint=None, tamt=0, lit=.20, neon=1.0, rain=True, stars=True, orb='moon',
                  street=(9, 11, 26), ground=(15, 17, 38)),
    'amanecer': dict(sky=[(0, (36, 28, 90)), (.5, (190, 66, 130)), (1, (255, 176, 100))], haze=(214, 104, 130),
                     tint=(255, 150, 120), tamt=.30, warm=(255, 190, 140), wamt=.06, lit=.22, neon=.7, rain=False, stars=False, orb='sun_low',
                     street=(34, 26, 56), ground=(46, 36, 76)),
    'dia': dict(sky=[(0, (30, 70, 128)), (.5, (70, 112, 156)), (1, (232, 168, 116))], haze=(112, 128, 156),
                tint=(96, 120, 168), tamt=.20, lit=.12, neon=.7, rain=False, stars=False, orb='sun_gold',
                street=(22, 28, 46), ground=(34, 42, 68), warm=(255, 176, 108), wamt=.16, clouds=True),
}
RAMPS = {
    'indigo': [(12, 14, 34), (22, 26, 60), (36, 42, 88), (70, 84, 150)],
    'violet': [(22, 12, 42), (38, 22, 72), (58, 36, 108), (100, 68, 168)],
    'teal': [(8, 20, 34), (14, 36, 58), (24, 56, 84), (48, 100, 132)],
    'plum': [(26, 10, 34), (44, 18, 58), (68, 30, 84), (114, 58, 132)],
}
LIT = [((255, 200, 110), .42), ((120, 240, 255), .30), ((255, 110, 220), .16), ((236, 240, 255), .12)]

GLYPH = {
    'ok': ["......X", ".....XX", "X...XX.", "XX.XX..", ".XXX...", "..X...."],
    'up': ["...X...", "..XXX..", "..XXX..", ".XXXXX.", ".XXXXX.", "XXXXXXX"],
    'dn': ["XXXXXXX", ".XXXXX.", ".XXXXX.", "..XXX..", "..XXX..", "...X..."],
    'x': ["XX...XX", ".XX.XX.", "..XXX..", "..XXX..", ".XX.XX.", "XX...XX"],
}
GCOL = {'ok': GR, 'up': AM, 'dn': CY, 'x': RD}


class S:  # estado global del dibujo
    img = None; d = None; m = None; px = None


def put(x, y, c, a=1.0):
    if 0 <= x < W and 0 <= y < H:
        if a >= 1: S.px[x, y] = tuple(c)
        else: S.px[x, y] = mix(S.px[x, y], c, a)


def poly(pts, fill): S.d.polygon(pts, fill=tuple(fill))
def line(a, b, c): S.d.line([a, b], fill=tuple(c))


def glow(polys, color, k=1.0):
    k *= S.m['neon']
    if k <= 0: return
    layer = Image.new('RGB', (W, H), (0, 0, 0)); d = ImageDraw.Draw(layer)
    for rad, it in ((6, .05), (4, .09), (2, .16)):
        c = mul(color, it * k)
        for a in range(12):
            dx = round(math.cos(a * math.pi / 6) * rad); dy = round(math.sin(a * math.pi / 6) * rad)
            for p in polys: d.polygon([(x + dx, y + dy) for x, y in p], fill=c)
    S.img.paste(ImageChops.add(S.img, layer)); S.d = ImageDraw.Draw(S.img); S.px = S.img.load()


# ---------- texto y carteles ----------
def line_img(text, color, scale=1, font=F11):
    segs = []; pos = 0
    for mt in re.finditer(r'\{(\w+)\}', text):
        if mt.start() > pos: segs.append(('t', text[pos:mt.start()]))
        segs.append(('g', mt.group(1))); pos = mt.end()
    if pos < len(text): segs.append(('t', text[pos:]))
    gw = lambda v: 40 if v.startswith('bar') else 8
    wtot = sum(gw(v) if t == 'g' else math.ceil(font.getlength(v)) for t, v in segs)
    im = Image.new('RGBA', (max(1, wtot), 11), (0, 0, 0, 0)); d = ImageDraw.Draw(im); d.fontmode = "1"
    x = 0
    for t, v in segs:
        if t == 't':
            d.text((x, -1), v, font=font, fill=color + (255,)); x += math.ceil(font.getlength(v))
        else:
            if v.startswith('bar'):
                lv = int(v[3:]); bc = GR if lv < 70 else (AM if lv < 90 else RD)
                d.rectangle([x, 2, x + 37, 9], outline=bc + (255,))
                d.rectangle([x + 2, 4, x + 2 + int(33 * lv / 100), 7], fill=bc + (255,))
                x += 40
            else:
                for j, row in enumerate(GLYPH[v]):
                    for i, ch in enumerate(row):
                        if ch == 'X': d.point((x + i, 2 + j), fill=GCOL[v] + (255,))
                x += 8
    if scale > 1: im = im.resize((im.width * scale, im.height * scale), Image.NEAREST)
    return im


def make_sign(lines, color, pad=3, bg=(7, 9, 22), minw=0):
    ims = [line_img(t, c, s) for t, c, s in lines]
    w = max(max(i.width for i in ims) + pad * 2 + 2, minw); h = sum(i.height for i in ims) + pad * 2 + 2 + (len(ims) - 1) * 2
    sg = Image.new('RGBA', (w, h), bg + (255,)); d = ImageDraw.Draw(sg)
    d.rectangle([0, 0, w - 1, h - 1], outline=color + (255,))
    for cx, cy in ((0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1)):  # esquinas biseladas
        d.point((cx, cy), fill=(0, 0, 0, 0))
    d.line([(1, 1), (3, 1)], fill=mix(color, (255, 255, 255), .5) + (255,))
    y = pad + 1
    for i in ims:
        sg.paste(i, ((w - i.width) // 2, y), i); y += i.height + 2
    return sg


def blit_sign(sg, face, origin, halo=1.0, color=CY):
    sx0, sy0 = origin; w, h = sg.size
    dyw = (w // 2) if face == 'L' else -(w // 2)
    quad = [(sx0, sy0 - h), (sx0 + w, sy0 - h + dyw), (sx0 + w, sy0 + dyw), (sx0, sy0)]
    glow([quad], color, halo)
    for i in range(w):
        dy = i // 2 if face == 'L' else -(i // 2)
        col = sg.crop((i, 0, i + 1, h))
        S.img.paste(col, (sx0 + i, sy0 - h + dy), col)
    S.d = ImageDraw.Draw(S.img); S.px = S.img.load()
    return quad


# ---------- edificios ----------
def hz(c, f): return mix(c, S.m['haze'], f)


def rampc(name):
    r = RAMPS[name]
    if S.m['tint']: r = [mix(c, S.m['tint'], S.m['tamt']) for c in r]
    return r


def draw_windows(x, y, w, dd, h, z0, face, rng, hf, dens=1.0):
    n = w if face == 'L' else dd
    rp = S.cur_ramp; fc = rp[1] if face == 'L' else rp[0]
    glass = hz(mix(fc, rp[3], .16), hf)
    pt = (lambda u, z: P(x + u, y + dd, z)) if face == 'L' else (lambda u, z: P(x + w, y + dd - u, z))
    for f in range(max(0, int((h - 6) // 6))):
        z = z0 + 4 + f * 6
        for k in range(int(n * 2)):
            r = rng.random(); cr = rng.random(); band = rng.random()
            u0 = k * .5 + .13; u1 = u0 + .27
            lit = r < S.m['lit'] * dens
            if lit:
                acc = 0; col = LIT[0][0]
                for c, wt in LIT:
                    acc += wt
                    if cr <= acc: col = c; break
                col = hz(mix(col, glass, .38), hf * .6)
            else: col = glass
            q = [pt(u0, z), pt(u1, z), pt(u1, z + 3), pt(u0, z + 3)]
            poly(q, col)


def draw_box(x, y, w, dd, h, z0, rname, seed, hf=0.0, neon=None, dens=1.0, detail=True):
    rp = rampc(rname); S.cur_ramp = rp
    left, right, top = hz(rp[1], hf), hz(rp[0], hf), hz(rp[2], hf)
    topq = [P(x, y, z0 + h), P(x + w, y, z0 + h), P(x + w, y + dd, z0 + h), P(x, y + dd, z0 + h)]
    lq = [P(x, y + dd, z0), P(x + w, y + dd, z0), P(x + w, y + dd, z0 + h), P(x, y + dd, z0 + h)]
    rq = [P(x + w, y + dd, z0), P(x + w, y, z0), P(x + w, y, z0 + h), P(x + w, y + dd, z0 + h)]
    if S.m.get('warm'):
        wc, wa = S.m['warm'], S.m['wamt']
        left = mix(left, wc, wa * (1 - hf)); top = mix(top, wc, wa * .6 * (1 - hf)); right = mix(right, (20, 24, 60), .15)
    poly(lq, left); poly(rq, right); poly(topq, top)
    rim = hz(rp[3], hf)
    if S.m.get('warm'): rim = mix(rim, S.m['warm'], .5)
    line(P(x, y + dd, z0 + h), P(x + w, y + dd, z0 + h), rim); line(P(x + w, y + dd, z0 + h), P(x + w, y, z0 + h), mix(rim, right, .4))
    line(P(x, y + dd, z0 + h), P(x, y, z0 + h), mix(rim, top, .5)); line(P(x, y, z0 + h), P(x + w, y, z0 + h), mix(rim, top, .5))
    rng = random.Random(seed)
    if detail:
        draw_windows(x, y, w, dd, h, z0, 'L', rng, hf, dens)
        draw_windows(x, y, w, dd, h, z0, 'R', rng, hf, dens)
    if neon:
        nc = hz(neon, hf * .5)
        a, b = P(x + w, y + dd, z0 + 1), P(x + w, y + dd, z0 + h)
        glow([[a, b, (b[0] + 1, b[1]), (a[0] + 1, a[1])]], neon, .8)
        line(a, b, nc); line((a[0] - 1, a[1]), (b[0] - 1, b[1]), mix(nc, left, .55))
        line((a[0] + 1, a[1]), (b[0] + 1, b[1]), mix(nc, right, .55))
        line(P(x, y + dd, z0 + h), P(x + w, y + dd, z0 + h), nc)
    return topq


def roof_stuff(x, y, w, dd, h, rname, seed, hf):
    rng = random.Random(seed + 7); r = rng.random()
    if r < .45 and w > 2.5 and dd > 2.5:
        draw_box(x + w * .3, y + dd * .3, w * .35, dd * .35, rng.randint(5, 12), h, rname, seed, hf, None, .7)
    if r > .55:  # antena
        ax = P(x + w * .5, y + dd * .5, h)
        top = (ax[0], ax[1] - rng.randint(10, 24)); line((ax[0], ax[1]), top, hz((90, 100, 150), hf))
        put(top[0], top[1], RD if rng.random() < .6 else AM)


# ---------- ciudad ----------
def make_city():
    rng = random.Random(11)
    blocks = []
    for bi in range(-8, 14):
        for bj in range(-8, 14):
            cx, cy = P(bi * 8 + 3, bj * 8 + 3, 0)
            if -140 < cx < W + 140 and OY - 70 < cy < H + 120: blocks.append((bi, bj, cx, cy))
    targets = [
        ('reloj', 478, 322), ('net', 676, 300), ('cpu', 368, 262), ('vpn', 806, 392),
        ('sync', 590, 214), ('git', 392, 470), ('bar', 620, 505),
        ('gpu', 556, 420), ('ram', 880, 262), ('disco', 860, 520),
    ]
    heroes = {}
    for name, tx, ty in targets:
        best = min((b for b in blocks if (b[0], b[1]) not in heroes), key=lambda b: (b[2] - tx) ** 2 + (b[3] - ty) ** 2)
        heroes[(best[0], best[1])] = name
    return blocks, heroes


def build_scene(modename, T=0):
    m = MODES[modename]; S.m = m
    img = Image.new('RGB', (W, H), (0, 0, 0)); S.img = img; S.d = ImageDraw.Draw(img); S.px = img.load()
    rng = random.Random(5)
    # cielo
    for y in range(H):
        t = clamp(y / (OY + 70), 0, 1)
        stops = m['sky']
        for i in range(len(stops) - 1):
            if stops[i][0] <= t <= stops[i + 1][0]:
                tt = (t - stops[i][0]) / (stops[i + 1][0] - stops[i][0]); col = mix(stops[i][1], stops[i + 1][1], tt); break
        else: col = stops[-1][1]
        S.d.line([(0, y), (W, y)], fill=col)
    if m['stars']:
        for _ in range(130):
            x, y = rng.randint(0, W - 1), rng.randint(0, OY - 20)
            put(x, y, (200, 210, 255), rng.choice([.25, .45, .8]))
    # astro
    if m['orb'] == 'moon':
        glow_c = (130, 150, 255)
        for r, a in ((34, .05), (26, .09), (20, .16)): S.d.ellipse([310 - r, 70 - r, 310 + r, 70 + r], fill=mix(S.px[310, 70], glow_c, a * 1.6))
        S.d.ellipse([298, 58, 322, 82], fill=(226, 232, 255)); S.d.ellipse([306, 56, 330, 80], fill=S.px[330, 60])
    elif m['orb'] == 'sun':
        for r, a in ((44, .12), (32, .2), (24, .35)): S.d.ellipse([700 - r, 80 - r, 700 + r, 80 + r], fill=mix(S.px[700, 80], (255, 250, 220), a))
        S.d.ellipse([688, 68, 712, 92], fill=(255, 250, 225))
    elif m['orb'] == 'sun_gold':
        for r, a in ((70, .10), (50, .18), (34, .30)): S.d.ellipse([720 - r, 120 - r, 720 + r, 120 + r], fill=mix(S.px[720, 120], (255, 200, 130), a))
        S.d.ellipse([706, 106, 734, 134], fill=(255, 232, 178))
    elif m['orb'] == 'sun_low':
        for r, a in ((90, .12), (66, .2), (46, .35)): S.d.ellipse([500 - r, 150 - r, 500 + r, 150 + r], fill=mix(S.px[500, 150], (255, 210, 140), a))
        S.d.ellipse([474, 124, 526, 176], fill=(255, 226, 160))
    if m.get('clouds'):
        cr2 = random.Random(8)
        for _ in range(9):
            cx0, cy0 = cr2.randint(-20, W), cr2.randint(10, 120)
            for _k in range(6):
                ex, ey, er = cx0 + cr2.randint(-40, 40), cy0 + cr2.randint(-6, 6), cr2.randint(14, 30)
                S.d.ellipse([ex - er * 1.6, ey - er * .5, ex + er * 1.6, ey + er * .5], fill=mix(S.px[min(W - 1, max(0, ex)), min(H - 1, max(0, ey))], (14, 24, 52), .55))
            S.d.line([(cx0 - 60, cy0 + 12), (cx0 + 60, cy0 + 12)], fill=mix((70, 112, 156), (255, 176, 108), .5))
    # skyline lejano (2 capas)
    for layer, (hmax, k) in enumerate(((70, .78), (46, .55))):
        x = -10
        while x < W:
            wd = rng.randint(14, 34); hh = rng.randint(12, hmax)
            col = mix(S.m['haze'], mix(m['sky'][1][1], (0, 0, 0), .35), k - .3 + layer * .15)
            S.d.rectangle([x, OY + 8 - hh - layer * 0, x + wd, OY + 30], fill=col)
            for _ in range(hh // 6):
                wx, wy = x + rng.randint(1, wd - 2), OY + 8 - rng.randint(2, hh)
                if rng.random() < m['lit'] * 1.2: put(wx, wy, LIT[rng.choice([0, 1, 2])][0], .55)
            x += wd + rng.randint(0, 5)
    # suelo
    blocks, heroes = make_city()
    sc, gc = m['street'], m['ground']
    streaks = []
    for bi in range(-8, 14):
        for bj in range(-8, 14):
            for lx in range(8):
                for ly in range(8):
                    tx, ty = bi * 8 + lx, bj * 8 + ly
                    street = lx >= 6 or ly >= 6
                    c = sc if street else (gc if (tx + ty) % 2 else mul(gc, 1.06))
                    s = tx + ty
                    hf = clamp((72 - s) / 72, 0, 1) ** 1.4 * .7
                    q = [P(tx, ty), P(tx + 1, ty), P(tx + 1, ty + 1), P(tx, ty + 1)]
                    if all(-30 < p[0] < W + 30 and OY - 8 < p[1] < H + 30 for p in q): poly(q, hz(c, hf))
            # lineas de carril y bordillos
            for ax in (0, 1):
                a = P(bi * 8, bj * 8 + 7) if ax == 0 else P(bi * 8 + 7, bj * 8)
                b = P(bi * 8 + 8, bj * 8 + 7) if ax == 0 else P(bi * 8 + 7, bj * 8 + 8)
                n = 8
                for k in range(0, n, 2):
                    p0 = (a[0] + (b[0] - a[0]) * k / n, a[1] + (b[1] - a[1]) * k / n); p1 = (a[0] + (b[0] - a[0]) * (k + 1) / n, a[1] + (b[1] - a[1]) * (k + 1) / n)
                    hf = clamp((72 - (bi * 8 + bj * 8)) / 72, 0, 1) ** 1.4 * .7
                    line((round(p0[0]), round(p0[1])), (round(p1[0]), round(p1[1])), hz(mix(sc, CY, .35 * m['neon'] + .1), hf))
    # reflejos/brillos en calle mojada
    if m['neon'] > .5:
        for _ in range(260):
            tx, ty = rng.randint(-20, 70), rng.randint(-20, 70)
            if (tx % 8 >= 6 or ty % 8 >= 6):
                p = P(tx + .5, ty + .5)
                if 0 < p[0] < W - 4 and OY + 6 < p[1] < H:
                    c = rng.choice([CY, MG, VI]); put(p[0], p[1], c, .35 * m['neon']); put(p[0] + 1, p[1], c, .25 * m['neon']); put(p[0] + 2, p[1], c, .12 * m['neon'])

    items = []
    names = {'reloj': None}
    clock = {'h': {'noche':'21:37','dia':'13:05','amanecer':'07:48'}[modename], 'f': 'MAR 10 NOV'}
    for (bi, bj, cx, cy) in blocks:
        r = random.Random(bi * 977 + bj * 131 + 3)
        hero = heroes.get((bi, bj))
        left = clamp((250 - cx) / 250, 0, 1)  # zona iconos: baja y apagada
        dens = 1.0 - left * .65
        far = clamp((cy - OY) / 450, 0, 1)
        center = math.exp(-(((cx - 500) / 300) ** 2 + ((cy - 330) / 200) ** 2))
        scale = (.42 + .55 * center) * clamp(1.3 - far * .9, .4, 1.1) * (1 - left * .55)
        bx, by = bi * 8, bj * 8
        hf = clamp((72 - (bx + by + 6)) / 72, 0, 1) ** 1.4 * .7
        rn = r.choice(list(RAMPS))
        if hero:
            items.append((bx + 5.5 + by + 5.5, 'hero', (hero, bx, by, rn, hf, clock)))
            continue
        layout = r.random()
        if layout < .35: parts = [(.8, .8, 4.4, 4.4)]
        elif layout < .65: parts = [(.8, .8, 2.1, 4.4), (3.1, .8, 2.1, 4.4)]
        elif layout < .85: parts = [(.8, .8, 4.4, 2.1), (.8, 3.1, 4.4, 2.1)]
        else: parts = [(.8, .8, 2.1, 2.1), (3.1, .8, 2.1, 2.1), (.8, 3.1, 2.1, 2.1), (3.1, 3.1, 2.1, 2.1)]
        for pi, (ox, oy, w, dd) in enumerate(parts):
            h = max(12, int((20 + r.randint(8, 60)) * scale * (1.3 if layout < .35 else 1.0)))
            if r.random() < .06 * (1 - left): h = int(h * 1.6)
            neon = None
            if r.random() < .38 * (1 - left): neon = r.choice([CY, CY, MG, MG, VI, AM])
            items.append((bx + ox + w + by + oy + dd, 'box', (bx + ox, by + oy, w, dd, h, rn, bi * 31 + bj * 7 + pi, hf, neon, dens)))
    # coches voladores: por carril, periodo 16 casillas, avanzan T*0.5 casillas
    for bj in range(-8, 14):
        for li, lane in enumerate((6.55, 7.45)):
            for ax in (0, 1):
                cr = random.Random(bj * 53 + li * 7 + ax * 1000 + 5)
                kinds = ['sedan'] * 9 + ['van'] * 3 + ['truck'] * 2 + ['moto'] * 3 + ['bus'] + ['taxi'] * 2
                cars_l = [(cr.uniform(0, 16), cr.choice([10, 16, 24, 34]), cr.choice([CY, MG, AM, GR, VI, CY, MG]),
                           cr.choice(kinds), cr.choice(BODIES), cr.choice([1, 1, 1, 2])) for _ in range(3)]
                sgn = 1 if li == 0 else -1
                for off, z, col, kind, body, spd in cars_l:
                    for k in range(-6, 8):
                        pos = off + k * 16 + sgn * T * .5 * spd
                        if ax == 0: x, y = pos, bj * 8 + lane
                        else: x, y = bj * 8 + lane, pos
                        px_, py_ = P(x, y, z)
                        if -40 < px_ < W + 40 and OY - 40 < py_ < H + 30:
                            items.append((x + y + .3, 'car', (x, y, z, ('x' if ax == 0 else 'y') + ('' if li == 0 else 'r'), col, kind, body)))
    items.sort(key=lambda t: t[0])
    ctx = dict(rng=rng, streaks=streaks)
    for key, kind, a in items:
        if kind == 'box': do_box(*a)
        elif kind == 'hero': do_hero(*a)
        else: do_car(*a)
    # drones, dirigible
    draw_drones(T); draw_airship(T)
    # niebla de horizonte
    for y in range(OY - 40, OY + 110):
        t = 1 - abs(y - (OY + 20)) / 90
        if t > 0:
            for x in range(0, W, 1):
                S.px[x, y] = mix(S.px[x, y], m['haze'], clamp(t, 0, 1) * (.30 if modename == 'noche' else .38))
    # lluvia
    if m['rain']:
        rr = random.Random(99)
        for _ in range(520):
            x, y = rr.randint(0, W), rr.randint(0, H); l = rr.randint(3, 6)
            for k in range(l): put(x - k // 2, y + k, (150, 200, 255), .22 * (k + 1) / l)
    # oscurecer zona de iconos y vineta
    for y in range(H):
        for x in range(0, 340):
            t = (1 - x / 340) ** 1.25 * .58
            S.px[x, y] = mix(S.px[x, y], (3, 4, 12), t)
    for y in range(H):
        for x in range(W):
            dxn = (x - W / 2) / (W / 2); dyn = (y - H / 2) / (H / 2)
            v = clamp((dxn * dxn + dyn * dyn - .55) * .25, 0, .3)
            if v: S.px[x, y] = mix(S.px[x, y], (2, 3, 10), v)
    return S.img


def do_box(x, y, w, dd, h, rn, seed, hf, neon, dens):
    draw_box(x, y, w, dd, h, 0, rn, seed, hf, neon, dens)
    roof_stuff(x, y, w, dd, h, rn, seed, hf)
    # base reflejada en calle mojada
    if neon and S.m['neon'] > .5:
        for k in range(3):
            p = P(x + w, y + dd, 0)
            for j in range(4 + k * 3): put(p[0] - 1 + k - 1, p[1] + 1 + j * 2, neon, .30 - j * .05)


def hero_sign_L(x, y, w, dd, u0, z0, lines, col, halo=1.0):
    sg = make_sign(lines, col); blit_sign(sg, 'L', P(x + u0, y + dd, z0), halo, col); return sg


def do_hero(name, bx, by, rn, hf, clock):
    # tamano y altura por tipo
    spec = {
        'reloj': (1.0, 1.0, 4.0, 4.0, 230, 'indigo'), 'net': (.8, .8, 4.4, 4.4, 110, 'violet'),
        'cpu': (1.4, 1.4, 3.0, 3.0, 190, 'teal'), 'vpn': (.8, .8, 4.0, 4.0, 140, 'plum'),
        'sync': (1.2, 1.2, 3.2, 3.2, 130, 'indigo'), 'git': (.8, .8, 4.4, 4.4, 56, 'teal'),
        'bar': (.8, .8, 4.4, 4.2, 40, 'plum'),
        'gpu': (.8, .8, 4.2, 4.2, 96, 'violet'), 'ram': (.8, .8, 3.8, 3.8, 70, 'indigo'), 'disco': (.8, .8, 4.0, 4.0, 58, 'teal'),
    }[name]
    ox, oy, w, dd, h, rn = spec; x, y = bx + ox, by + oy
    neon = {'reloj': CY, 'net': CY, 'cpu': MG, 'vpn': GR, 'sync': CY, 'git': AM, 'bar': MG, 'gpu': GR, 'ram': CY, 'disco': VI}[name]
    draw_box(x, y, w, dd, h, 0, rn, hash(name) & 255, hf, neon, .9)
    if name == 'reloj':
        draw_box(x + .7, y + .7, w - 1.4, dd - 1.4, 44, h, rn, 5, hf, None, .9)
        draw_box(x + 1.3, y + 1.3, w - 2.6, dd - 2.6, 22, h + 44, rn, 6, hf, None, .5)
        ax = P(x + w / 2, y + dd / 2, h + 66); top = (ax[0], ax[1] - 26)
        line(ax, top, (140, 150, 210)); put(top[0], top[1], RD); glow([[(top[0] - 1, top[1] - 1), (top[0] + 1, top[1] - 1), (top[0] + 1, top[1] + 1), (top[0] - 1, top[1] + 1)]], RD, 1)
        hero_sign_L(x, y, w, dd, .4, 120, [(clock['h'], CY, 2), (clock['f'], (230, 241, 255), 1)], CY, 1.2)
        sg = make_sign([('ESTUDIO', MG, 1), ('22:00 {ok}', (230, 241, 255), 1)], MG)
        blit_sign(sg, 'R', P(x + w, y + dd - .3, 40), 1.0, MG)
    elif name == 'net':
        hero_sign_L(x, y, w, dd, .3, 66, [('NET', CY, 1), ('{dn} 42.1', (230, 241, 255), 1), ('{up}  8.3', (230, 241, 255), 1)], CY)
        sg = make_sign([('Mb/s', VI, 1)], VI); blit_sign(sg, 'R', P(x + w, y + dd - .6, 30), .6, VI)
    elif name == 'cpu':
        loads = [.9, .35, .6, .15, .75, .45, .25, .55]
        for i, ld in enumerate(loads):  # una planta por nucleo: bandas iluminadas segun carga
            z = 10 + i * 20
            for face in ('L', 'R'):
                n = w if face == 'L' else dd
                pt = (lambda u, zz: P(x + u, y + dd, zz)) if face == 'L' else (lambda u, zz: P(x + w, y + dd - u, zz))
                col = mix(CY, MG, clamp((ld - .4) / .5, 0, 1))
                q = [pt(.2, z), pt(.2 + (n - .4) * ld, z), pt(.2 + (n - .4) * ld, z + 6), pt(.2, z + 6)]
                glow([q], col, .35 * ld); poly(q, col)
        sg = make_sign([('CPU 47%', MG, 1), ('{bar47}', MG, 1)], MG)
        blit_sign(sg, 'L', P(x + .1, y + dd, h - 28), .9, MG)
    elif name == 'vpn':
        sg = make_sign([('VPN', GR, 2), ('{ok} ACTIVA', GR, 1)], GR)
        blit_sign(sg, 'L', P(x + .1, y + dd, 78), 1.2, GR)
    elif name == 'sync':
        ax = P(x + w / 2, y + dd / 2, h); top = (ax[0], ax[1] - 44)
        line(ax, top, (150, 160, 220)); line((ax[0] - 1, ax[1]), (top[0] - 1, top[1] + 20), (60, 66, 110))
        for r in (3, 6, 9):
            S.d.ellipse([top[0] - r, top[1] - r // 2 - 1, top[0] + r, top[1] + r // 2 + 1], outline=mix(S.px[top[0], top[1] - 4], GR, .5 * S.m['neon'] + .15))
        glow([[(top[0] - 2, top[1] - 2), (top[0] + 2, top[1] - 2), (top[0] + 2, top[1] + 2), (top[0] - 2, top[1] + 2)]], GR, 1.3)
        S.d.rectangle([top[0] - 1, top[1] - 1, top[0] + 1, top[1] + 1], fill=GR)
        sg = make_sign([('SYNC {ok}', GR, 1)], GR); blit_sign(sg, 'L', P(x + .3, y + dd, 50), .8, GR)
    elif name == 'git':
        sg = make_sign([('REPOS', AM, 1), ('{up} 3', (230, 241, 255), 2)], AM); blit_sign(sg, 'L', P(x + .4, y + dd, 36), 1.0, AM)
    elif name == 'bar':
        sg = make_sign([('BAR', MG, 2), ('BAT 78%  52C', (230, 241, 255), 1)], MG); blit_sign(sg, 'L', P(x + .1, y + dd, 30), 1.1, MG)
        sg2 = make_sign([('OPEN', CY, 1)], CY); blit_sign(sg2, 'R', P(x + w, y + dd - .4, 18), .7, CY)
    elif name == 'gpu':
        vals = [.3, .6, .45, .8, .5, .9, .55, .35, .7, .4]
        n = len(vals)
        for i, v in enumerate(vals):  # ecualizador en la fachada
            u0 = .25 + i * (w - .5) / n; u1 = u0 + (w - .5) / n * .6
            zt = 8 + v * (h - 34)
            col = mix(GR, AM, clamp((v - .5) / .4, 0, 1))
            q = [P(x + u0, y + dd, 6), P(x + u1, y + dd, 6), P(x + u1, y + dd, zt), P(x + u0, y + dd, zt)]
            glow([q], col, .25); poly(q, col)
        sg = make_sign([('GPU 41%  58C', GR, 1), ('{bar41}', GR, 1)], GR); blit_sign(sg, 'L', P(x + .1, y + dd, h - 4 + 18), .9, GR)
    elif name == 'ram':
        tx, ty = P(x + w / 2, y + dd / 2, h)
        for lx in (-9, -3, 3, 9):  # patas
            line((tx + lx, ty - 2 + (abs(lx) // 3)), (tx + lx, ty + 3 - 0), (110, 120, 170))
        cyl = [tx - 12, ty - 36, tx + 12, ty - 8]
        S.d.rectangle(cyl, fill=(12, 16, 36)); S.d.ellipse([cyl[0], cyl[1] - 4, cyl[2], cyl[1] + 4], fill=(30, 40, 80), outline=(140, 150, 220))
        lvl = int(24 * .64); fl = cyl[3] - 1 - lvl
        S.d.rectangle([cyl[0] + 2, fl, cyl[2] - 2, cyl[3] - 2], fill=CY)
        S.d.ellipse([cyl[0] + 2, fl - 2, cyl[2] - 2, fl + 2], fill=mix(CY, (255, 255, 255), .4))
        S.d.ellipse([cyl[0], cyl[3] - 4, cyl[2], cyl[3] + 4], fill=(12, 16, 36), outline=mix(CY, (12, 16, 36), .4))
        S.d.line([(cyl[0], cyl[1]), (cyl[0], cyl[3])], fill=(140, 150, 220)); S.d.line([(cyl[2], cyl[1]), (cyl[2], cyl[3])], fill=(140, 150, 220))
        glow([[(cyl[0] + 2, fl), (cyl[2] - 2, fl), (cyl[2] - 2, cyl[3] - 2), (cyl[0] + 2, cyl[3] - 2)]], CY, .6)
        sg = make_sign([('RAM 10.2/16G', CY, 1), ('{bar64}', CY, 1)], CY); blit_sign(sg, 'L', P(x + .1, y + dd, 20), .9, CY)
    elif name == 'disco':
        sg = make_sign([('DISCO 62%', VI, 1), ('{bar62}', VI, 1)], VI); blit_sign(sg, 'L', P(x + .1, y + dd, 28), .9, VI)
    # reflejo en el suelo
    p = P(x + w, y + dd, 0)
    for j in range(12): put(p[0] - 2, p[1] + 1 + j, neon, .35 - j * .025); put(p[0] + 1, p[1] + 1 + j, neon, .22 - j * .015)


BODIES = [(44, 48, 86), (72, 40, 96), (30, 64, 76), (96, 34, 66), (62, 64, 76), (30, 36, 60), (88, 60, 110), (120, 120, 140)]
CAR_KINDS = {'sedan': (2.0, 4, 1.0, 3), 'taxi': (2.0, 4, 1.0, 3), 'van': (2.3, 6, 0, 0), 'truck': (3.6, 6, 0, 0), 'moto': (1.1, 3, .4, 2), 'bus': (4.2, 6, 0, 0)}


def do_car(x, y, z, ax, col, kind='sedan', body=(44, 48, 86)):
    sgn = 1 if not ax.endswith('r') else -1
    d = (1, 0) if ax[0] == 'x' else (0, 1)
    L, h, cl, ch = CAR_KINDS[kind]
    if kind == 'taxi': body = (216, 164, 28)
    if S.m['tint']: body = mix(body, S.m['tint'], .18)
    pt = lambda u, zz: P(x + d[0] * u * sgn, y + d[1] * u * sgn, zz)
    def quad(u0, u1, z0, z1): return [pt(u0, z0), pt(u1, z0), pt(u1, z1), pt(u0, z1)]
    glow([quad(0, L, z - 1, z + 1)], col, .22)
    glass = mix((14, 22, 48), (110, 190, 255), .25)
    if kind == 'truck':
        poly(quad(0, L - .9, z, z + h + 2), mix(body, (200, 200, 220), .15)); poly(quad(L - .9, L, z, z + h - 1), body)
        poly(quad(L - .7, L - .15, z + h - 3, z + h - 1), glass); line(pt(0, z + h + 2), pt(L - .9, z + h + 2), mix(body, (255, 255, 255), .4))
    elif kind == 'bus':
        poly(quad(0, L, z, z + h), body); poly(quad(.15, L - .15, z + h - 3, z + h - 1), mix(CY, (14, 22, 48), .35))
        line(pt(0, z + h), pt(L, z + h), mix(body, (255, 255, 255), .45))
    elif kind == 'van':
        poly(quad(0, L, z, z + h), body); poly(quad(L - .55, L - .08, z + h - 3, z + h - 1), glass)
        line(pt(0, z + h), pt(L, z + h), mix(body, (255, 255, 255), .4))
    elif kind == 'moto':
        poly(quad(0, L, z, z + 2), body); poly(quad(.25, .55, z + 2, z + 4), mix(body, (255, 255, 255), .25))
    else:
        poly(quad(0, L, z, z + h), body); poly(quad(.22, .22 + cl, z + h, z + h + ch), glass)
        line(pt(.22, z + h + ch), pt(.22 + cl, z + h + ch), mix(body, (255, 255, 255), .5)); line(pt(0, z + h), pt(L, z + h), mix(body, (255, 255, 255), .4))
        if kind == 'taxi': put(*pt(.5, z + h + ch + 1), (255, 255, 200))
    # franja de color (identidad) y luces
    line(pt(.1, z + 1), pt(L - .1, z + 1), col)
    fx, fy = pt(L, z + max(h, 2) - 1); put(fx, fy, (255, 255, 235)); put(fx, fy - 1, (255, 255, 235), .6)
    bx_, by_ = pt(0, z + max(h, 2) - 1); put(bx_, by_, RD); put(bx_, by_ - 1, RD, .6)
    for i in range(1, 13):  # estela
        t = pt(-i * .5, z + 1)
        put(t[0], t[1], col, min(1, .55 * (1 - i / 13) * (0.5 + S.m['neon'])))
    sp = P(x, y, 0); put(sp[0], sp[1], (0, 0, 0), .5); put(sp[0] + 1, sp[1], (0, 0, 0), .4)


DRONES = [(430, 200, 40, 14, 0.0, 'UPD 12', AM), (700, 150, 60, 12, 1.5, None, None), (500, 262, 40, 8, 3.1, 'SRV {x} 1', RD),
          (860, 300, 40, 16, 2.2, None, None), (330, 330, 40, 12, 4.0, None, None), (640, 230, 70, 10, 5.0, None, None),
          (760, 440, 50, 12, .8, None, None), (470, 430, 60, 10, 2.8, None, None), (900, 200, 30, 10, 1.1, None, None), (400, 120, 50, 8, 3.7, None, None)]


def draw_drones(T=0):
    for (cx, cy, ax_, ay_, ph, tag, tc) in DRONES:
        ang = 2 * math.pi * T / 96 + ph
        x = round(cx + ax_ * math.sin(ang)); y = round(cy + ay_ * math.sin(2 * ang + ph))
        S.d.rectangle([x - 3, y, x + 3, y + 2], fill=(46, 52, 92)); S.d.line([(x - 6, y - 1), (x + 6, y - 1)], fill=(90, 100, 150))
        rot = (110, 120, 170) if T % 2 else (160, 170, 220)
        for dx in (-7, -6, 6, 7): put(x + dx, y - 2, rot)
        put(x, y - 1, (60, 66, 110))
        put(x - 1, y + 2, RD if (T // 3) % 2 else (80, 20, 30)); put(x + 1, y + 2, GR)
        glow([[(x - 2, y + 1), (x + 2, y + 1), (x + 2, y + 3), (x - 2, y + 3)]], RD, .5)
        if tag:
            sg = make_sign([(tag, tc, 1)], tc, pad=2); S.img.paste(sg, (x - sg.width // 2, y - sg.height - 6), sg)
            line((x, y - 5), (x, y - 1), tc)
            S.d = ImageDraw.Draw(S.img); S.px = S.img.load()


TIPS = ['TIP: git commit a menudo', 'TIP: haz copia de seguridad', 'TIP: Ctrl+Alt+T abre la terminal', 'TIP: revisa las actualizaciones', 'TIP: cierra lo que no uses']


def tips_strip():
    parts = [line_img(t, AM) for t in TIPS]; sep = line_img(' // ', VI)
    wd = sum(i.width + sep.width for i in parts)
    strip = Image.new('RGBA', (wd, 11), (0, 0, 0, 0)); x = 0
    for i in parts:
        strip.paste(i, (x, 0), i); x += i.width; strip.paste(sep, (x, 0), sep); x += sep.width
    return strip


def draw_airship(T=0):
    prog = (T % 96) / 96
    cx = round(-150 + (W + 300) * prog); cy = round(92 + 5 * math.sin(2 * math.pi * prog * 3))
    body = mix((78, 70, 150), S.m['tint'], S.m['tamt'] * .6) if S.m['tint'] else (78, 70, 150)
    dark = mix(body, (0, 0, 0), .35); lite = mix(body, (170, 170, 255), .55)
    RX, RY = 104, 27
    # aletas y cuerpo
    S.d.polygon([(cx - RX + 8, cy - 2), (cx - RX - 14, cy - 24), (cx - RX + 4, cy - 22), (cx - RX + 22, cy - 8)], fill=dark)
    S.d.polygon([(cx - RX + 8, cy + 2), (cx - RX - 14, cy + 24), (cx - RX + 4, cy + 22), (cx - RX + 22, cy + 8)], fill=dark)
    S.d.ellipse([cx - RX, cy - RY, cx + RX, cy + RY], fill=body)
    S.d.arc([cx - RX + 2, cy - RY + 2, cx + RX - 2, cy + RY - 2], 200, 340, fill=lite)
    S.d.arc([cx - RX + 5, cy - RY + 5, cx + RX - 5, cy + RY - 5], 205, 335, fill=mix(body, lite, .45))
    for i in range(-5, 6):  # costillas
        xx = cx + i * 17; hh = int(RY * math.sqrt(max(0, 1 - ((xx - cx) / RX) ** 2)))
        line((xx, cy - hh + 1), (xx, cy + hh - 1), mix(body, dark, .5))
    S.d.arc([cx - RX, cy - RY, cx + RX, cy + RY], 20, 160, fill=dark)
    # gondola y helice
    S.d.rectangle([cx - 22, cy + RY - 2, cx + 22, cy + RY + 7], fill=(26, 26, 54), outline=mix(body, lite, .4))
    for i in range(-3, 4): put(cx + i * 6, cy + RY + 3, AM if i % 2 else CY)
    S.d.rectangle([cx + RX - 2, cy - 3, cx + RX + 3, cy + 3], fill=dark)
    put(cx + RX + 5, cy - 4 + (T % 2) * 3, (200, 210, 255), .7); put(cx + RX + 5, cy + 4 - (T % 2) * 3, (200, 210, 255), .7)
    # pantalla LED con consejos que pasan
    sw, sh = 156, 19; sx0, sy0 = cx - sw // 2, cy - sh // 2 - 2
    S.d = ImageDraw.Draw(S.img); S.px = S.img.load()
    glow([[(sx0, sy0), (sx0 + sw, sy0), (sx0 + sw, sy0 + sh), (sx0, sy0 + sh)]], AM, .55)
    scr = Image.new('RGBA', (sw, sh), (8, 8, 20, 255)); strip = tips_strip()
    off = int(prog * strip.width * 3) % strip.width
    for k in (-1, 0, 1, 2):
        scr.paste(strip, (6 - off + k * strip.width, 4), strip)
    sd = ImageDraw.Draw(scr)
    for xx in range(0, sw, 2): sd.point((xx, sh - 2), fill=(0, 0, 0, 90))
    sd.rectangle([0, 0, sw - 1, sh - 1], outline=AM + (255,))
    for a in ((0, 0), (sw - 1, 0), (0, sh - 1), (sw - 1, sh - 1)): sd.point(a, fill=(0, 0, 0, 0))
    S.img.paste(scr, (sx0, sy0), scr)
    S.d = ImageDraw.Draw(S.img); S.px = S.img.load()
    for px_, py_, c in ((cx + RX - 2, cy - 2, RD if (T // 4) % 2 else (90, 20, 30)), (cx - RX + 2, cy - 2, GR if (T // 4) % 2 else (20, 80, 40))):
        put(px_, py_, c)


# ---------- barra ----------
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


def draw_bar(img, clock='21:37', date='MAR 10 NOV', dia=False):
    d = ImageDraw.Draw(img); d.fontmode = "1"; Wd = img.width
    BG, PAN, TXT = (11, 14, 26), (18, 23, 43), (230, 241, 255)
    for y in range(32):  # fondo con degradado suave
        d.line([(0, y), (Wd, y)], fill=mix((20, 25, 47), (10, 12, 24), y / 31))
    for y in range(0, 32, 2): d.line([(0, y), (Wd, y)], fill=(255, 255, 255, 0)) if False else None
    d.line([(0, 31), (Wd, 31)], fill=mix(CY, BG, .35)); d.line([(0, 30), (Wd, 30)], fill=mix(CY, BG, .78))
    for i, a in enumerate((.14, .08, .04)):  # halo bajo la barra
        for x in range(Wd): img.putpixel((x, 32 + i * 2), mix(img.getpixel((x, 32 + i * 2)), CY, a)); img.putpixel((x, 33 + i * 2), mix(img.getpixel((x, 33 + i * 2)), CY, a * .6))
    # nucleo >_
    cx = 18
    hexp = [(cx - 8, 5), (cx + 8, 5), (cx + 15, 16), (cx + 8, 27), (cx - 8, 27), (cx - 15, 16)]
    d.polygon([(x + 0, y) for x, y in hexp], fill=mix(CY, BG, .82), outline=CY)
    d.polygon([(cx - 9, 8), (cx + 9, 8), (cx + 12, 16), (cx + 9, 24), (cx - 9, 24), (cx - 12, 16)], outline=mix(CY, BG, .55))
    d.text((cx - 8, 9), ">_", font=F14, fill=CY)
    sep = lambda x: d.line([(x, 8), (x, 23)], fill=mix(VI, BG, .45))
    sep(42)
    # escritorios: rombos
    for i in range(4):
        x = 56 + i * 20; y = 16
        r = [(x, y - 6), (x + 6, y), (x, y + 6), (x - 6, y)]
        if i == 1:
            d.polygon(r, fill=CY); d.polygon([(x, y - 9), (x + 9, y), (x, y + 9), (x - 9, y)], outline=mix(CY, BG, .6))
        else: d.polygon(r, outline=mix(VI, TXT, .1))
    sep(142)
    # apps
    apps = [('term', CY, 'open'), ('folder', VI, 'open'), ('globe', CY, 'attn'), ('code', CY, None)]
    for i, (nm, col, st) in enumerate(apps):
        x = 154 + i * 34; y = 4
        d.polygon(chamfer(x, y, x + 25, y + 24, 3), fill=PAN, outline=mix(col, BG, .55))
        d.line([(x + 4, y + 1), (x + 20, y + 1)], fill=mix(col, TXT, .3))
        icon(d, nm, x + 4, y + 3, col, s=2) if False else icon(d, nm, x + 4, y + 4, col, s=2)
        if st == 'open': d.rectangle([x + 3, 28, x + 22, 29], fill=CY)
        if st == 'attn': d.rectangle([x + 3, 28, x + 22, 29], fill=MG); d.rectangle([x + 20, y - 1, x + 25, y + 4], fill=MG)
    # reloj en muesca biselada
    cxm = Wd // 2; x0, x1 = cxm - 130, cxm + 130
    d.polygon([(x0 - 14, 0), (x1 + 14, 0), (x1 + 2, 29), (x0 + 12 - 12 + 0, 29)], fill=(8, 10, 21))
    d.polygon([(x0 - 8, 0), (x1 + 8, 0), (x1 - 2, 27), (x0 + 2, 27)], fill=mix(PAN, BG, .5), outline=mix(CY, BG, .4))
    d.line([(x0 - 8, 0), (x0 + 2, 27)], fill=CY); d.line([(x1 + 8, 0), (x1 - 2, 27)], fill=CY)
    d.line([(x0 + 2, 27), (x1 - 2, 27)], fill=mix(CY, BG, .3))
    tx = f"{clock}  ·  {date}"; w = d.textlength(tx, font=F14)
    d.text((cxm - w / 2, 7), clock, font=F14, fill=TXT)
    wc = d.textlength(clock + "  ", font=F14)
    d.text((cxm - w / 2 + wc, 7), "·", font=F14, fill=MG)
    d.text((cxm - w / 2 + wc + 14, 7), date, font=F14, fill=mix(CY, TXT, .55))
    # bandeja (de derecha a izquierda)
    x = Wd - 18
    icon(d, 'power', x - 12, 7, MG); x -= 36; sep(x + 14)
    # bateria 6 rallitas
    bx = x - 44; d.rectangle([bx, 10, bx + 33, 22], outline=GR); d.rectangle([bx + 34, 14, bx + 36, 18], fill=GR)
    for i in range(6):
        c = GR if i < 5 else mix(GR, BG, .75)
        d.rectangle([bx + 3 + i * 5, 12, bx + 5 + i * 5, 20], fill=c)
    d.text((bx - 36, 9), "78%", font=F11 if False else F14, fill=TXT); x = bx - 46; sep(x + 4)
    x -= 26; icon(d, 'wifi', x, 7, CY)
    x -= 28; icon(d, 'vol', x, 7, CY)
    x -= 28; icon(d, 'sync', x, 7, CY)
    x -= 28; icon(d, 'shield', x, 7, GR, (11, 14, 26))
    # esquinas "corchete"
    for (a, b) in (((0, 0), (5, 0)), ((0, 0), (0, 5)), ((Wd - 1, 0), (Wd - 6, 0)), ((Wd - 1, 0), (Wd - 1, 5))):
        d.line([a, b], fill=CY)
    return img


def compose(modename, clock, date, T=60):
    scene = build_scene(modename, T)
    big = scene.resize((W * 2, H * 2), Image.NEAREST)
    draw_bar(big, clock, date)
    return scene, big


def desktop_icons(big):
    d = ImageDraw.Draw(big); d.fontmode = "1"
    names = ['Proyectos', 'Documentos', 'Descargas', 'Imagenes', 'Musica', 'Papelera', 'Notas', 'Backups', 'Videos', 'Blog']
    for n, nm in enumerate(names):
        c, r = divmod(n, 6); x0 = 40 + c * 150; y0 = 70 + r * 150
        if n == 1: d.polygon(chamfer(x0 - 22, y0 - 10, x0 + 98, y0 + 108, 6), fill=(0, 229, 255, 40) if False else mix(CY, (11, 14, 26), .82), outline=mix(CY, (11, 14, 26), .3))
        d.polygon([(x0, y0 + 6), (x0 + 24, y0 + 6), (x0 + 30, y0 + 12), (x0 + 38, y0 + 12), (x0 + 38, y0 + 18), (x0, y0 + 18)], fill=(120, 84, 200))
        d.polygon([(x0, y0 + 16), (x0 + 76, y0 + 16), (x0 + 76, y0 + 62), (x0, y0 + 62)], fill=(84, 56, 150))
        d.rectangle([x0, y0 + 16, x0 + 76, y0 + 18], fill=(170, 130, 255)); d.rectangle([x0, y0 + 56, x0 + 76, y0 + 62], fill=(52, 34, 98))
        d.rectangle([x0 + 3, y0 + 21, x0 + 73, y0 + 59], outline=(110, 76, 190)); d.line([(x0, y0 + 16), (x0 + 6, y0 + 16)], fill=CY)
        if n in (0, 3): d.rectangle([x0 + 10, y0 + 10, x0 + 60, y0 + 17], fill=(236, 240, 255))
        w = d.textlength(nm, font=F14); tx = x0 + 38 - w / 2
        d.text((tx + 1, y0 + 74), nm, font=F14, fill=(0, 0, 0)); d.text((tx, y0 + 73), nm, font=F14, fill=(230, 241, 255))


def frame(args):
    m, T = args
    return build_scene(m, T).copy()


if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True)
    clocks = {'noche': ('21:37', 'MAR 10 NOV'), 'dia': ('13:05', 'MAR 10 NOV'), 'amanecer': ('07:48', 'MAR 10 NOV')}
    if sys.argv[1:2] == ['anim']:
        from multiprocessing import Pool
        for m in sys.argv[2:]:
            with Pool(8) as pool: fr = pool.map(frame, [(m, T) for T in range(96)])
            d_ = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'frames-' + m); os.makedirs(d_, exist_ok=True)
            for i_, f_ in enumerate(fr): f_.save(f'{d_}/f{i_:03d}.png')
            os.system(f"ffmpeg -y -loglevel error -framerate 8 -i {d_}/f%03d.png -vf scale=1920:1200:flags=neighbor -c:v libx264 -pix_fmt yuv420p -crf 20 {OUT}/animacion-{m}.mp4")
            print('mp4', m)
    else:
        for m in (sys.argv[1:] or ['noche', 'dia', 'amanecer']):
            sc, big = compose(m, *clocks[m])
            big.save(f'{OUT}/concepto-{m}.png')
            if m == 'noche': desktop_icons(big); big.save(f'{OUT}/concepto-noche-iconos.png')
            if m == 'noche':
                big.crop((0, 0, 960, 80)).resize((1920, 160), Image.NEAREST).save(f'{OUT}/barra-izquierda.png')
                big.crop((960, 0, 1920, 80)).resize((1920, 160), Image.NEAREST).save(f'{OUT}/barra-derecha.png')
            print('ok', m)
