#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Fuente ram: memoria usada (total - disponible)."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import comun


def medir():
    mi = {}
    for l in comun.leer("/proc/meminfo", "").splitlines():
        k, _, v = l.partition(":")
        p = v.split()
        if p:
            mi[k] = int(p[0])                  # kB
    if "MemTotal" not in mi:
        return comun.neutro("sin /proc/meminfo")
    total = mi["MemTotal"] / 1024.0
    libre = mi.get("MemAvailable", mi.get("MemFree", 0)) / 1024.0
    usada = max(0.0, total - libre)
    pct = round(100.0 * usada / total, 1) if total else 0.0
    return {"estado": comun.estado_umbral(pct, 85, 95), "usada_mb": int(usada),
            "total_mb": int(total), "pct": pct}


def demo():
    total = 16384
    pct = round(comun.onda(200, 45, 92), 1)     # roza el aviso (>=85)
    return {"estado": comun.estado_umbral(pct, 85, 95), "usada_mb": int(total * pct / 100),
            "total_mb": total, "pct": pct}


if __name__ == "__main__":
    comun.ejecutar("ram", medir, demo)
