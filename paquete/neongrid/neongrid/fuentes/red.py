#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Fuente red: caudal de bajada/subida de la interfaz principal (sin ping, sin DNS)."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import comun

# interfaces virtuales que no cuentan como "la red" del equipo
VIRTUALES = ("lo", "docker", "veth", "virbr", "br-", "tun", "tap", "wg", "vmnet", "vboxnet",
             "tailscale", "zt", "podman", "cni", "flannel", "ifb", "dummy", "bond", "teql")


def _ruta_por_defecto():
    """Interfaz de la ruta por defecto (/proc/net/route), o None."""
    for l in comun.leer("/proc/net/route", "").splitlines()[1:]:
        p = l.split()
        if len(p) > 3 and p[1] == "00000000" and (int(p[3], 16) & 1):
            return p[0]
    return None


def _ifaces():
    try:
        return sorted(os.listdir("/sys/class/net"))
    except OSError:
        return []


def _elegir():
    """(iface, conectada). Prioriza la ruta por defecto; si no, una física que esté 'up'."""
    d = _ruta_por_defecto()
    if d:
        return d, True
    fisicas = [i for i in _ifaces() if not i.startswith(VIRTUALES)]
    for i in fisicas:
        if comun.leer("/sys/class/net/%s/operstate" % i) == "up":
            return i, True
    return (fisicas[0] if fisicas else None), False


def _contadores(iface):
    return {"rx": int(comun.leer("/sys/class/net/%s/statistics/rx_bytes" % iface, 0)),
            "tx": int(comun.leer("/sys/class/net/%s/statistics/tx_bytes" % iface, 0))}


def medir(guardar=True):
    iface, conectada = _elegir()
    if iface is None:
        return comun.neutro("no hay interfaz de red", bajada_kbps=0, subida_kbps=0, iface=None,
                            conectada=False, ping_ms=None)
    # la caché es por interfaz: si cambia, se vuelve a muestrear
    a, b, dt = comun.muestreo("red-" + iface, lambda: _contadores(iface), guardar=guardar)
    baj = max(0.0, (b["rx"] - a["rx"]) * 8 / 1000.0 / dt)
    sub = max(0.0, (b["tx"] - a["tx"]) * 8 / 1000.0 / dt)
    return {"estado": "ok" if conectada else "aviso", "bajada_kbps": round(baj, 1),
            "subida_kbps": round(sub, 1), "iface": iface, "conectada": conectada, "ping_ms": None}


def demo():
    baj = comun.onda(23, 40, 18000) * comun.onda(97, 0.2, 1.0, fase=1.0)
    sub = comun.onda(31, 10, 1800, fase=2.0)
    return {"estado": "ok", "bajada_kbps": round(baj, 1), "subida_kbps": round(sub, 1),
            "iface": "wlan0", "conectada": True, "ping_ms": None}


if __name__ == "__main__":
    comun.ejecutar("red", medir, demo)
