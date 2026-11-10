#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Fuente actualizaciones: paquetes pendientes (pacman -Qu, apt, dnf --cacheonly o zypper --no-refresh; todas SIN red).

Comprobar actualizaciones puede tardar (algunas herramientas consultan los repos), así
que se hace en dos tiempos: esta fuente solo LEE una caché (30 min) y, si está caducada,
lanza UN refresco en segundo plano con tope de 60 s (tiene su propio límite y se
autodestruye; no queda nada colgando). Sin caché todavía: neutro «comprobando»."""
import os, signal, subprocess, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import comun

TTL = 1800
TOPE_REFRESCO = 60


def _herramienta():
    """(nombre, comando, contar). contar(stdout, rc) -> int|None."""
    # Arch: `pacman -Qu` compara con las bases de datos LOCALES ya descargadas (sin red ni sudo).
    # (No se usa `checkupdates`: sincroniza una base temporal y por tanto sale a la red.)
    if comun.hay("pacman"):
        return ("pacman", ["pacman", "-Qu"],
                lambda out, rc: len([l for l in out.splitlines() if l.strip()]) if rc in (0, 1) else None)   # 1 = nada pendiente
    if comun.hay("apt"):
        return ("apt", ["apt", "list", "--upgradable"],
                lambda out, rc: len([l for l in out.splitlines() if "/" in l and "upgradable" in l]) if rc == 0 else None)
    if comun.hay("dnf"):
        return ("dnf", ["dnf", "-q", "check-update", "--cacheonly"],
                lambda out, rc: (len([l for l in out.splitlines() if l.strip() and not l.startswith(("Obsoleting", " "))
                                      and len(l.split()) == 3]) if rc == 100 else (0 if rc == 0 else None)))
    if comun.hay("zypper"):
        return ("zypper", ["zypper", "--no-refresh", "-q", "lu"],
                lambda out, rc: len([l for l in out.splitlines() if l.startswith("v |")]) if rc == 0 else None)
    return None


def _refrescar():
    """Modo --refrescar: ejecuta la herramienta con tope y escribe la caché."""
    h = _herramienta()
    if not h:
        return
    rc, out = comun.ejecutar_cmd(h[1], timeout=TOPE_REFRESCO)
    n = h[2](out, rc) if rc is not None else None
    comun.guardar_cache("actualizaciones", {"t": time.time(), "n": n, "herramienta": h[0]})


def _lanzar_refresco():
    """Lanza el refresco desacoplado, con candado para no duplicarlo."""
    d = comun.dir_cache()
    if not d:
        return
    candado = os.path.join(d, "actualizaciones.lock")
    try:
        if time.time() - os.path.getmtime(candado) < TOPE_REFRESCO + 5:
            return                                  # ya hay uno en marcha
    except OSError:
        pass
    try:
        open(candado, "w").close()
        subprocess.Popen([sys.executable, os.path.abspath(__file__), "--refrescar"],
                         stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                         start_new_session=True, close_fds=True)
    except OSError:
        pass


def _est(n):
    return "ok" if n < 10 else ("aviso" if n < 100 else "error")


def medir():
    h = _herramienta()
    if not h:
        return comun.neutro("ninguna herramienta de actualizaciones disponible", pendientes=None)
    c = comun.leer_cache("actualizaciones")
    caducada = not (isinstance(c, dict) and time.time() - c.get("t", 0) < TTL)
    if caducada:
        _lanzar_refresco()
    if not isinstance(c, dict):
        return comun.neutro("comprobando actualizaciones", pendientes=None, herramienta=h[0])
    n = c.get("n")
    if n is None:
        return comun.neutro("no se pudo comprobar (sin conexión o repos)", pendientes=None, herramienta=h[0])
    return {"estado": _est(n), "pendientes": n, "herramienta": h[0]}


def demo():
    return {"estado": "aviso", "pendientes": 12, "herramienta": "demo"}


if __name__ == "__main__":
    if "--refrescar" in sys.argv:
        try:
            signal.alarm(TOPE_REFRESCO + 5)         # seguro extra: el proceso muere solo
            _refrescar()
        finally:
            os._exit(0)
    comun.ejecutar("actualizaciones", medir, demo)
