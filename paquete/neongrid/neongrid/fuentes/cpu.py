#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Fuente cpu: uso total y por núcleo, frecuencia y temperatura."""
import glob, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import comun


def _tomar():
    """Lee /proc/stat: {'cpu': [inactivo, total], 'cpu0': [...], ...}."""
    m = {}
    txt = comun.leer("/proc/stat", "")
    for l in txt.splitlines():
        if not l.startswith("cpu"):
            continue
        p = l.split()
        v = [int(x) for x in p[1:9]]          # user nice system idle iowait irq softirq steal
        m[p[0]] = [v[3] + v[4], sum(v)]
    return m


def _pct(a, b):
    di, dt = b[0] - a[0], b[1] - a[1]
    if dt <= 0:
        return 0.0
    return round(max(0.0, min(100.0, 100.0 * (1 - di / dt))), 1)


def _freq():
    """Frecuencia media en MHz (cpufreq o /proc/cpuinfo)."""
    vals = [comun.leer_num(f) for f in glob.glob("/sys/devices/system/cpu/cpu[0-9]*/cpufreq/scaling_cur_freq")]
    vals = [v / 1000.0 for v in vals if v]
    if not vals:
        for l in comun.leer("/proc/cpuinfo", "").splitlines():
            if l.lower().startswith("cpu mhz"):
                try:
                    vals.append(float(l.split(":")[1]))
                except ValueError:
                    pass
    return round(sum(vals) / len(vals)) if vals else None


def _temp():
    """Temperatura del procesador desde hwmon (coretemp, k10temp, zenpower...) o thermal_zone."""
    preferidos = ("coretemp", "k10temp", "zenpower", "cpu_thermal", "x86_pkg_temp")
    mejor = None
    for h in glob.glob("/sys/class/hwmon/hwmon*"):
        nombre = comun.leer(os.path.join(h, "name"), "")
        if nombre in preferidos:
            for f in sorted(glob.glob(os.path.join(h, "temp*_input"))):
                et = comun.leer(f.replace("_input", "_label"), "")
                v = comun.leer_num(f)
                if v is None:
                    continue
                if et in ("Package id 0", "Tctl", "Tdie") or mejor is None:
                    mejor = v / 1000.0
    if mejor is None:
        for z in glob.glob("/sys/class/thermal/thermal_zone*"):
            if comun.leer(os.path.join(z, "type"), "") in ("x86_pkg_temp", "cpu-thermal", "acpitz"):
                v = comun.leer_num(os.path.join(z, "temp"))
                if v:
                    mejor = v / 1000.0
                    break
    return round(mejor, 1) if mejor is not None else None


def medir():
    a, b, dt = comun.muestreo("cpu", _tomar)
    if "cpu" not in b:
        return comun.neutro("sin /proc/stat")
    total = _pct(a.get("cpu", b["cpu"]), b["cpu"])
    nucleos = []
    i = 0
    while "cpu%d" % i in b:
        nucleos.append(_pct(a.get("cpu%d" % i, b["cpu%d" % i]), b["cpu%d" % i]))
        i += 1
    t = _temp()
    est = comun.peor(comun.estado_umbral(total, 90, 101), comun.estado_umbral(t, 85, 95)) if t is not None \
        else comun.estado_umbral(total, 90, 101)
    if est == "neutro":
        est = "ok"
    return {"estado": est, "total": total, "nucleos": nucleos, "freq_mhz": _freq(), "temp_c": t}


def demo():
    n = 8
    nucleos = [round(comun.onda(40 + 7 * i, 5, 95, fase=i * 0.9), 1) for i in range(n)]
    total = round(sum(nucleos) / n, 1)
    t = round(comun.onda(240, 48, 98), 1)       # llega a >95: muestra el estado error
    est = comun.peor(comun.estado_umbral(total, 90, 101), comun.estado_umbral(t, 85, 95))
    return {"estado": est, "total": total, "nucleos": nucleos,
            "freq_mhz": int(comun.onda(60, 1200, 4200)), "temp_c": t}


if __name__ == "__main__":
    comun.ejecutar("cpu", medir, demo)
