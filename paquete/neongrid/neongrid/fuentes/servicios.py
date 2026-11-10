#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Fuente servicios: unidades systemd fallidas (sistema y usuario)."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import comun


def _fallidas(extra):
    rc, out = comun.ejecutar_cmd(["systemctl"] + extra + ["--failed", "--no-legend", "--plain", "--no-pager"],
                                 timeout=1.5)
    if rc is None:
        return None
    nombres = []
    for l in out.splitlines():
        p = l.replace("●", " ").split()
        if p and "." in p[0]:
            nombres.append(p[0])
    return nombres


def _est(n):
    return "ok" if n == 0 else ("aviso" if n < 3 else "error")


def medir():
    if not comun.hay("systemctl"):
        return comun.neutro("systemd no disponible", fallidos=0, lista=[])
    s = _fallidas([])
    u = _fallidas(["--user"])
    if s is None and u is None:
        return comun.neutro("systemctl no responde", fallidos=0, lista=[])
    lista = (s or []) + [x for x in (u or []) if x not in (s or [])]
    return {"estado": _est(len(lista)), "fallidos": len(lista), "lista": lista}


def demo():
    return {"estado": "aviso", "fallidos": 1, "lista": ["bluetooth-demo.service"]}


if __name__ == "__main__":
    comun.ejecutar("servicios", medir, demo)
