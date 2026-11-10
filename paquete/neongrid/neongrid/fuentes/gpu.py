#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Fuente gpu: uso y temperatura (sysfs/hwmon, nvidia-smi o rocm-smi si existen)."""
import glob, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import comun

VENDORES = {"0x10de": "NVIDIA", "0x1002": "AMD", "0x8086": "Intel"}


def _sysfs():
    """Recorre /sys/class/drm/card*/device y devuelve (nombre, pct, temp) de la mejor GPU."""
    mejor = None
    for dev in sorted(glob.glob("/sys/class/drm/card[0-9]*/device")):
        ven = comun.leer(os.path.join(dev, "vendor"), "")
        drv = os.path.basename(os.path.realpath(os.path.join(dev, "driver"))) \
            if os.path.exists(os.path.join(dev, "driver")) else ""
        nombre = (VENDORES.get(ven, "GPU") + (" " + drv if drv else "")).strip()
        pct = comun.leer_num(os.path.join(dev, "gpu_busy_percent"))      # amdgpu
        temp = None
        for t in glob.glob(os.path.join(dev, "hwmon", "hwmon*", "temp1_input")):
            v = comun.leer_num(t)
            if v is not None:
                temp = v / 1000.0
                break
        cand = (nombre, pct, temp)
        # preferimos la que tenga lectura de uso; después la primera con temperatura
        if mejor is None or (pct is not None and mejor[1] is None) or \
                (mejor[1] is None and mejor[2] is None and temp is not None):
            mejor = cand
    return mejor


def _nvidia():
    if not comun.hay("nvidia-smi"):
        return None
    rc, out = comun.ejecutar_cmd(["nvidia-smi", "--query-gpu=name,utilization.gpu,temperature.gpu",
                                  "--format=csv,noheader,nounits"], timeout=1.2)
    if rc != 0 or not out.strip():
        return None
    p = [x.strip() for x in out.splitlines()[0].split(",")]
    try:
        return (p[0], float(p[1]), float(p[2]))
    except (ValueError, IndexError):
        return None


def _rocm():
    if not comun.hay("rocm-smi"):
        return None
    rc, out = comun.ejecutar_cmd(["rocm-smi", "--showuse", "--showtemp", "--json"], timeout=1.2)
    if rc != 0:
        return None
    try:
        import json
        d = json.loads(out)
        c = d[sorted(d)[0]]
        uso = float(c.get("GPU use (%)"))
        t = [float(v) for k, v in c.items() if "emperature" in k]
        return ("AMD", uso, t[0] if t else None)
    except Exception:
        return None


def medir():
    r = _nvidia() or _rocm() or _sysfs()
    if r is None:
        return comun.neutro("no hay GPU con lectura", pct=None, temp_c=None, nombre=None)
    nombre, pct, temp = r
    pct = round(pct, 1) if pct is not None else None
    temp = round(temp, 1) if temp is not None else None
    if pct is None and temp is None:
        return comun.neutro("la GPU no expone uso ni temperatura", pct=None, temp_c=None, nombre=nombre)
    est = comun.peor(comun.estado_umbral(pct, 95, 101), comun.estado_umbral(temp, 85, 95))
    return {"estado": est if est != "neutro" else "ok", "pct": pct, "temp_c": temp, "nombre": nombre}


def demo():
    pct = round(comun.onda(70, 5, 98, fase=1.0), 1)
    t = round(comun.onda(300, 45, 90, fase=2.0), 1)
    est = comun.peor(comun.estado_umbral(pct, 95, 101), comun.estado_umbral(t, 85, 95))
    return {"estado": est, "pct": pct, "temp_c": t, "nombre": "GPU demo"}


if __name__ == "__main__":
    comun.ejecutar("gpu", medir, demo)
