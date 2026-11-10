#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Fuente carga: loadavg a 1 minuto e intensidad de la lluvia (0-1)."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import comun


def _resultado(l1, nuc):
    llu = max(0.0, min(1.0, l1 / max(1, nuc)))     # carga por núcleo: 1.0 = todos ocupados
    return {"estado": comun.estado_umbral(l1 / max(1, nuc), 1.0, 2.0), "loadavg1": round(l1, 2),
            "nucleos": nuc, "intensidad_lluvia": round(llu, 3)}


def medir():
    p = comun.leer("/proc/loadavg", "").split()
    if not p:
        return comun.neutro("sin /proc/loadavg")
    return _resultado(float(p[0]), os.cpu_count() or 1)


def demo():
    return _resultado(comun.onda(180, 0.3, 5.5), 8)


if __name__ == "__main__":
    comun.ejecutar("carga", medir, demo)
