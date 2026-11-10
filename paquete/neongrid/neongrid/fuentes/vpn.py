#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Fuente vpn: ¿hay una VPN activa? Neutro si no hay ninguna configurada."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import comun


def _por_interfaz():
    """Interfaces de túnel presentes: wg* (WireGuard), tun*/tap* (OpenVPN)."""
    try:
        nombres = os.listdir("/sys/class/net")
    except OSError:
        return None
    for n in sorted(nombres):
        if n.startswith("wg"):
            return "wireguard"
        if n.startswith(("tun", "tap")):
            return "openvpn"
    return None


def _networkmanager():
    """(activa_tipo, configurada) según nmcli (solo lectura)."""
    if not comun.hay("nmcli"):
        return None, False
    rc, out = comun.ejecutar_cmd(["nmcli", "-t", "-f", "TYPE,DEVICE", "connection", "show"], timeout=1.2)
    if rc != 0:
        return None, False
    activa = None
    configurada = False
    for l in out.splitlines():
        tipo, _, disp = l.partition(":")
        if tipo in ("vpn", "wireguard"):
            configurada = True
            if disp and disp != "--":
                activa = "wireguard" if tipo == "wireguard" else "nm"
    return activa, configurada


def _configurada_wireguard():
    try:
        return any(f.endswith(".conf") for f in os.listdir("/etc/wireguard"))
    except OSError:
        return False        # normalmente carpeta solo de root: no se puede saber


def medir():
    tipo = _por_interfaz()
    nm_activa, nm_conf = _networkmanager()
    tipo = tipo or nm_activa
    if tipo:
        return {"estado": "ok", "activa": True, "tipo": tipo}
    if nm_conf or _configurada_wireguard():
        return {"estado": "aviso", "activa": False, "tipo": None}     # hay VPN pero está apagada
    return comun.neutro("no hay VPN configurada", activa=False, tipo=None)


def demo():
    activa = comun.onda(420, 0, 1) < 0.75          # casi siempre activa; a ratos cae (aviso)
    return {"estado": "ok" if activa else "aviso", "activa": activa,
            "tipo": "wireguard" if activa else None}


if __name__ == "__main__":
    comun.ejecutar("vpn", medir, demo)
