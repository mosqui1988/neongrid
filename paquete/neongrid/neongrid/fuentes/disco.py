#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Fuente disco: uso de la partición raíz."""
import os, shutil, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import comun

GB = 1024.0 ** 3


def medir():
    u = shutil.disk_usage("/")
    pct = round(100.0 * u.used / u.total, 1) if u.total else 0.0
    return {"estado": comun.estado_umbral(pct, 85, 95), "pct": pct,
            "usado_gb": round(u.used / GB, 1), "total_gb": round(u.total / GB, 1)}


def demo():
    total = 512.0
    pct = round(comun.onda(900, 60, 88), 1)
    return {"estado": comun.estado_umbral(pct, 85, 95), "pct": pct,
            "usado_gb": round(total * pct / 100, 1), "total_gb": total}


if __name__ == "__main__":
    comun.ejecutar("disco", medir, demo)
