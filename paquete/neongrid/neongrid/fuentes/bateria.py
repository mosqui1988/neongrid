#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Fuente bateria: carga, si está cargando y temperatura. Neutro si no hay batería."""
import glob, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import comun


def _estado(pct, cargando, temp):
    e = "ok"
    if not cargando:
        e = "error" if pct <= 10 else ("aviso" if pct <= 20 else "ok")
    return comun.peor(e, "aviso" if (temp is not None and temp >= 45) else "ok")


def medir():
    bats = [b for b in sorted(glob.glob("/sys/class/power_supply/*"))
            if comun.leer(os.path.join(b, "type")) == "Battery"
            and comun.leer(os.path.join(b, "scope"), "System") != "Device"]   # excluye ratón/mando
    if not bats:
        return comun.neutro("este equipo no tiene batería")
    b = bats[0]
    pct = comun.leer_num(os.path.join(b, "capacity"))
    if pct is None:
        return comun.neutro("la batería no informa de su carga")
    cargando = comun.leer(os.path.join(b, "status"), "") == "Charging"
    t = comun.leer_num(os.path.join(b, "temp"))
    t = round(t / 10.0, 1) if t is not None else None      # décimas de grado
    return {"estado": _estado(pct, cargando, t), "pct": int(pct), "cargando": cargando, "temp_c": t}


def demo():
    pct = int(comun.onda(600, 6, 100, fase=3.0))    # baja hasta el rojo y vuelve a subir
    cargando = comun.onda(600, 0, 1, fase=3.0 + 1.5708) > 0.5   # sube = cargando
    t = round(comun.onda(200, 30, 47), 1)
    return {"estado": _estado(pct, cargando, t), "pct": pct, "cargando": cargando, "temp_c": t}


if __name__ == "__main__":
    comun.ejecutar("bateria", medir, demo)
