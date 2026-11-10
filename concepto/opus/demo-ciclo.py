#!/usr/bin/env python3
"""Demo del ciclo dia/noche de NeonGrid (propuesta opus).

Para cada paso (cada 30 min) se renderiza la escena en modo noche y en modo dia con la hora
real en los carteles, y se mezclan segun la altura del sol. Amanecer y atardecer llevan un
tinte calido con resplandor en el horizonte. Es una aproximacion para la demo; en el tema real
las capas de cada franja se pregeneran y se funden en QML.

Uso:  python demo-ciclo.py        -> demo-ciclo.mp4 + ciclo-hoja.png
"""
import os, sys, math, importlib.util
from multiprocessing import Pool
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location('gp', os.path.join(HERE, 'generar-propuesta.py'))
gp = importlib.util.module_from_spec(spec); spec.loader.exec_module(gp)
STEPS = 48


def smooth(t): t = max(0.0, min(1.0, t)); return t * t * (3 - 2 * t)


def day_factor(h):  # 0 = noche cerrada, 1 = pleno dia
    if h < 12: return smooth((h - 5.5) / 2.5)
    return 1 - smooth((h - 17.5) / 2.5)


def warm(h):  # intensidad del amanecer / atardecer
    return min(1.0, math.exp(-((h - 6.6) / .9) ** 2) + math.exp(-((h - 18.6) / .9) ** 2))


def render_one(args):
    i, mode, hour_txt = args
    gp.DATA.update(hora=hour_txt, fecha='MAR 10 NOV')
    q, big, n = gp.render(mode, T=i)
    return i, mode, big.tobytes(), big.size


def grade(img, w):
    """Tinte calido + resplandor en el horizonte (suave, escalonado por la cuantizacion posterior)."""
    if w < .02: return img
    from PIL import ImageChops
    W2, H2 = img.size
    px = img.load()
    glow = Image.new('RGB', (W2, H2), (0, 0, 0)); gp_ = glow.load()
    hy = gp.HY * 2
    for y in range(max(0, hy - 150), min(H2, hy + 90)):
        t = 1 - abs(y - (hy - 20)) / 120
        if t <= 0: continue
        for x in range(0, W2):
            g = math.exp(-((x - 1000) / 760) ** 2) * t * w
            gp_[x, y] = (int(255 * .34 * g), int(110 * .34 * g), int(70 * .34 * g))
    img = ImageChops.add(img, glow)
    tint = Image.new('RGB', (W2, H2), (255, 150, 110))
    return Image.blend(img, ImageChops.multiply(img, tint), .22 * w)


def main():
    jobs = []
    for i in range(STEPS):
        h = i * 24 / STEPS; hh, mm = int(h), int(round((h - int(h)) * 60))
        txt = f"{hh:02d}:{mm:02d}"
        jobs += [(i, 'noche', txt), (i, 'dia', txt)]
    with Pool(min(16, os.cpu_count() or 4)) as pool:
        res = pool.map(render_one, jobs)
    ims = {}
    for i, mode, data, size in res: ims[(i, mode)] = Image.frombytes('RGB', size, data)
    outdir = os.path.join(HERE, 'ciclo-frames'); os.makedirs(outdir, exist_ok=True)
    frames = []
    for i in range(STEPS):
        h = i * 24 / STEPS; hh, mm = int(h), int(round((h - int(h)) * 60))
        f = day_factor(h)
        img = Image.blend(ims[(i, 'noche')], ims[(i, 'dia')], f)
        img = grade(img, warm(h))
        gp.draw_bar(img, f"{hh:02d}:{mm:02d}", 'MAR 10 NOV'); gp.desktop_icons(img)
        img.save(f'{outdir}/f{i:03d}.png'); frames.append(img)
    os.system(f"ffmpeg -y -loglevel error -framerate 6 -i {outdir}/f%03d.png -c:v libx264 -pix_fmt yuv420p -crf 20 {HERE}/demo-ciclo.mp4")
    # hoja de contacto con 6 momentos clave
    keys = [2, 13, 24, 36, 38, 44]  # 02:00, 06:30, 12:00, 18:00, 19:00, 22:00
    sheet = Image.new('RGB', (1920, 800), (6, 7, 16))
    for k, idx in enumerate(keys):
        t = frames[idx].resize((640, 400), Image.LANCZOS)
        sheet.paste(t, ((k % 3) * 640, (k // 3) * 400))
    sheet.save(os.path.join(HERE, 'ciclo-hoja.png'))
    print('ok', len(frames))


if __name__ == '__main__':
    main()
