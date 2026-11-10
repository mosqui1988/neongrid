#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Comprueba que es.json y en.json tienen las mismas claves, tipos, longitudes de lista
y marcadores {x}. Sale con código 1 si hay diferencias. Uso: python3 comprobar.py"""
import json
import os
import re
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))


def cargar(nombre):
    with open(os.path.join(AQUI, nombre + ".json"), encoding="utf-8") as f:
        return json.load(f)


def marcas(v):
    return sorted(re.findall(r"\{(\w+)\}", json.dumps(v, ensure_ascii=False)))


def main():
    es, en = cargar("es"), cargar("en")
    problemas = []
    for k in sorted(set(es) - set(en)):
        problemas.append("falta en en.json: " + k)
    for k in sorted(set(en) - set(es)):
        problemas.append("falta en es.json: " + k)
    for k in sorted(set(es) & set(en)):
        a, b = es[k], en[k]
        if type(a) is not type(b):
            problemas.append("tipo distinto: " + k)
        elif isinstance(a, list) and len(a) != len(b):
            problemas.append("longitud distinta (%d/%d): %s" % (len(a), len(b), k))
        elif marcas(a) != marcas(b):
            problemas.append("marcadores {x} distintos: " + k)
        if a in ("", [], None) or b in ("", [], None):
            problemas.append("valor vacío: " + k)
    if len(es.get("consejos.defecto", [])) < 12:
        problemas.append("menos de 12 consejos por defecto")
    if problemas:
        print("\n".join(problemas))
        return 1
    print("i18n OK: %d claves en es y en" % len(es))
    return 0


if __name__ == "__main__":
    sys.exit(main())
