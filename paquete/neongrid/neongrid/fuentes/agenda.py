#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Fuente agenda: próximo aviso de hoy según ~/.config/neongrid/agenda.txt (líneas «HH:MM texto»)."""
import os, re, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import comun

PAT = re.compile(r"^(\d{1,2}):(\d{2})\s+(.+)$")


def _entradas():
    res = []
    for l in comun.lineas_usuario(os.path.join(comun.dir_config(), "agenda.txt")):
        m = PAT.match(l)
        if m and int(m.group(1)) < 24 and int(m.group(2)) < 60:
            res.append((int(m.group(1)) * 60 + int(m.group(2)), "%02d:%s" % (int(m.group(1)), m.group(2)), m.group(3)))
    return sorted(res)


def _resolver(entradas, ahora_min):
    futuras = [e for e in entradas if e[0] >= ahora_min]
    prox = {"hora": futuras[0][1], "texto": futuras[0][2]} if futuras else None
    return {"estado": "ok", "proximo": prox, "restantes": len(futuras), "total": len(entradas)}


def medir():
    if not os.path.exists(os.path.join(comun.dir_config(), "agenda.txt")):
        return comun.neutro("no configurado: falta agenda.txt", proximo=None, restantes=0)
    e = _entradas()
    if not e:
        return comun.neutro("agenda.txt vacía", proximo=None, restantes=0)
    t = time.localtime()
    return _resolver(e, t.tm_hour * 60 + t.tm_min)


def demo():
    # próximo bloque ficticio siempre en el futuro: sube con los minutos de la hora actual
    t = time.localtime()
    ahora = t.tm_hour * 60 + t.tm_min
    ent = [(ahora + 25, "%02d:%02d" % (((ahora + 25) // 60) % 24, (ahora + 25) % 60), "Bloque de estudio"),
           (ahora + 90, "%02d:%02d" % (((ahora + 90) // 60) % 24, (ahora + 90) % 60), "Repaso"),
           (ahora + 180, "%02d:%02d" % (((ahora + 180) // 60) % 24, (ahora + 180) % 60), "Pausa larga")]
    return _resolver(ent, 0)


if __name__ == "__main__":
    comun.ejecutar("agenda", medir, demo)
