#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Fuente trafico: intensidad 0-1 derivada de red (para animar los coches voladores)."""
import math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import comun


def derivar(red):
    """A partir del objeto de la fuente red. Escala logarítmica: 0 con ~0 kbps, 1 con >= 100 Mbps."""
    if not isinstance(red, dict) or red.get("bajada_kbps") is None:
        return comun.neutro("sin datos de red", nivel=0.0, coches=0)
    kbps = float(red["bajada_kbps"]) + float(red.get("subida_kbps") or 0)
    nivel = max(0.0, min(1.0, math.log10(1 + kbps) / math.log10(1 + 100000)))
    nivel = round(nivel, 3)
    return {"estado": "ok" if red.get("conectada") else "neutro", "nivel": nivel,
            "coches": int(round(nivel * 10))}


def medir():
    import red                          # misma carpeta; sin guardar la muestra (la usa la fuente red)
    return derivar(red.medir(guardar=False))


def demo():
    import red
    return derivar(red.demo())


if __name__ == "__main__":
    comun.ejecutar("trafico", medir, demo)
