#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Fuente sync: estado de Syncthing local (127.0.0.1:8384). Neutro si no responde.

Único acceso de red permitido: el puerto local de Syncthing, con tope total de 300 ms.
La clave de API se lee de config.xml del propio usuario y NUNCA se imprime."""
import json, os, re, socket, sys, time
import urllib.request
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import comun

HOST, PUERTO = "127.0.0.1", 8384
TOPE = 0.3


def _clave():
    base_cfg = os.environ.get("XDG_CONFIG_HOME") or os.path.join(comun.home(), ".config")
    base_st = os.environ.get("XDG_STATE_HOME") or os.path.join(comun.home(), ".local", "state")
    for d in (os.path.join(base_st, "syncthing"), os.path.join(base_cfg, "syncthing")):
        txt = comun.leer(os.path.join(d, "config.xml"))
        if txt:
            m = re.search(r"<apikey>([^<]+)</apikey>", txt)
            if m:
                return m.group(1)
    return None


def medir():
    t0 = time.time()
    try:
        socket.create_connection((HOST, PUERTO), 0.1).close()
    except OSError:
        return comun.neutro("Syncthing no está en ejecución", estado_sync=None)
    clave = _clave()

    def get(ruta):
        resto = TOPE - (time.time() - t0)
        if resto <= 0.02:
            raise TimeoutError
        req = urllib.request.Request("http://%s:%d%s" % (HOST, PUERTO, ruta))
        if clave:
            req.add_header("X-API-Key", clave)
        with urllib.request.urlopen(req, timeout=resto) as r:
            return json.loads(r.read().decode("utf-8", "replace") or "null")

    try:
        miid = get("/rest/system/status").get("myID")
        remotos = [d for d in get("/rest/config/devices") if d.get("deviceID") != miid and not d.get("paused")]
        if not remotos:
            return {"estado": "ok", "estado_sync": "al_dia", "dispositivos": 0}
        conex = get("/rest/system/connections").get("connections", {})
        conectados = sum(1 for d in remotos if conex.get(d["deviceID"], {}).get("connected"))
        if conectados == 0:
            return {"estado": "aviso", "estado_sync": "desconectado", "dispositivos": len(remotos)}
        comp = get("/rest/db/completion")           # completitud global (0-100)
        sincronizando = float(comp.get("completion", 100)) < 100 or int(comp.get("needBytes", 0)) > 0
        return {"estado": "ok", "estado_sync": "sincronizando" if sincronizando else "al_dia",
                "dispositivos": len(remotos)}
    except Exception:
        # Responde el puerto pero sin clave/permiso: al menos sabemos que está vivo
        try:
            with urllib.request.urlopen("http://%s:%d/rest/noauth/health" % (HOST, PUERTO),
                                        timeout=max(0.05, TOPE - (time.time() - t0))) as r:
                if b"OK" in r.read():
                    return {"estado": "ok", "estado_sync": "al_dia", "dispositivos": None}
        except Exception:
            pass
        return comun.neutro("Syncthing no responde a tiempo", estado_sync=None)


def demo():
    ciclo = comun.onda(240, 0, 1)
    if ciclo > 0.85:
        return {"estado": "ok", "estado_sync": "sincronizando", "dispositivos": 2}
    if ciclo < 0.08:
        return {"estado": "aviso", "estado_sync": "desconectado", "dispositivos": 2}
    return {"estado": "ok", "estado_sync": "al_dia", "dispositivos": 2}


if __name__ == "__main__":
    comun.ejecutar("sync", medir, demo)
