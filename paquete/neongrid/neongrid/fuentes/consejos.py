#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Fuente consejos: frases rotativas del dirigible (consejos.txt del usuario o los de i18n)."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import comun


def medir():
    propios = comun.lineas_usuario(os.path.join(comun.dir_config(), "consejos.txt"))
    if propios:
        return {"estado": "ok", "lista": propios, "origen": "usuario"}
    lista = comun.textos().get("consejos.defecto", [])
    if not lista:
        return comun.neutro("sin consejos (falta i18n)", lista=[], origen=None)
    return {"estado": "ok", "lista": lista, "origen": "defecto"}


def demo():
    lista = comun.textos().get("consejos.defecto", [])
    return {"estado": "ok", "lista": lista, "origen": "defecto"}


if __name__ == "__main__":
    comun.ejecutar("consejos", medir, demo)
