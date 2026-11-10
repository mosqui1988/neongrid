#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Pruebas de las fuentes de datos de NeonGrid en este equipo.

Ejecuta cada fuente y ejecutar-todas.py (real y --demo), valida el esquema del
contrato (campos y tipos) y los tiempos (< 2 s por fuente, < 3 s todas), y
repite con entorno mínimo (env -i) y con XDG_RUNTIME_DIR inexistente.
Uso: python3 probar.py     (código de salida 1 si algo falla)"""
import json
import os
import subprocess
import sys
import tempfile
import time

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FUENTES = os.path.join(RAIZ, "paquete", "neongrid", "neongrid", "fuentes")
I18N = os.path.join(RAIZ, "paquete", "neongrid", "neongrid", "i18n", "comprobar.py")

NUM = (int, float)
# campo -> tipos admitidos (type(None) = puede ser null)
N = type(None)
ESQUEMA = {
    "cpu": {"total": NUM, "nucleos": list, "freq_mhz": (NUM, N), "temp_c": (NUM, N)},
    "ram": {"usada_mb": NUM, "total_mb": NUM, "pct": NUM},
    "gpu": {"pct": (NUM, N), "temp_c": (NUM, N), "nombre": (str, N)},
    "disco": {"pct": NUM, "usado_gb": NUM, "total_gb": NUM},
    "red": {"bajada_kbps": NUM, "subida_kbps": NUM, "iface": (str, N), "conectada": bool, "ping_ms": N},
    "vpn": {"activa": bool, "tipo": (str, N)},
    "sync": {"estado_sync": (str, N)},
    "git": {"repos_con_cambios": int, "sin_subir": int, "total": int},
    "bateria": {"pct": NUM, "cargando": bool, "temp_c": (NUM, N)},
    "actualizaciones": {"pendientes": (int, N)},
    "servicios": {"fallidos": int, "lista": list},
    "agenda": {"proximo": (dict, N), "restantes": int},
    "consejos": {"lista": list},
    "trafico": {"nivel": NUM},
    "carga": {"loadavg1": NUM, "intensidad_lluvia": NUM},
}
# campos que no existen cuando la fuente es neutra por falta de hardware (se admite que falten)
ESTADOS = ("ok", "aviso", "error", "neutro")
LIM_FUENTE, LIM_TODAS = 2.0, 3.0

fallos = []
resumen = []


def tipo_ok(v, t):
    if isinstance(v, bool) and t is not bool and (t == NUM or t == (int, float) or t is int):
        return False        # bool no cuenta como número
    return isinstance(v, t)


def validar(id_, d):
    """Devuelve lista de problemas de esquema de un objeto de fuente."""
    p = []
    if not isinstance(d, dict):
        return ["no es un objeto"]
    if d.get("id") != id_:
        p.append("id incorrecto %r" % d.get("id"))
    if d.get("estado") not in ESTADOS:
        p.append("estado inválido %r" % d.get("estado"))
    if not isinstance(d.get("ts"), int):
        p.append("ts no es int")
    if d.get("estado") == "neutro" and not d.get("motivo") and not d.get("demo"):
        p.append("neutro sin motivo")
    for campo, t in ESQUEMA.get(id_, {}).items():
        if campo not in d:
            if d.get("estado") == "neutro":
                continue                    # neutro puede omitir campos
            p.append("falta %s" % campo)
        elif not tipo_ok(d[campo], t):
            p.append("%s: tipo %s" % (campo, type(d[campo]).__name__))
    # rangos
    for campo in ("total", "pct", "intensidad_lluvia", "nivel"):
        v = d.get(campo)
        if isinstance(v, NUM) and not isinstance(v, bool):
            tope = 1 if campo in ("intensidad_lluvia", "nivel") else 100
            if not 0 <= v <= tope:
                p.append("%s fuera de rango: %s" % (campo, v))
    if id_ == "cpu" and isinstance(d.get("nucleos"), list):
        if not all(isinstance(x, NUM) and 0 <= x <= 100 for x in d["nucleos"]):
            p.append("nucleos fuera de rango")
    return p


def lanzar(args, env=None, cwd="/"):
    t0 = time.time()
    r = subprocess.run([sys.executable] + args, capture_output=True, text=True, env=env, cwd=cwd, timeout=10)
    return r, time.time() - t0


def probar(etiqueta, env=None, demo=False):
    """Prueba cada fuente y ejecutar-todas con un entorno dado."""
    extra = ["--demo"] if demo else []
    print("\n== %s ==" % etiqueta)
    ids = list(ESQUEMA)
    for i in ids:
        r, dt = lanzar([os.path.join(FUENTES, i + ".py")] + extra, env)
        try:
            d = json.loads(r.stdout)
            p = validar(i, d)
        except ValueError:
            d, p = {}, ["salida no es JSON"]
        if r.returncode != 0:
            p.append("código de salida %d" % r.returncode)
        if dt >= LIM_FUENTE:
            p.append("lento: %.2f s" % dt)
        est = d.get("estado", "?")
        extra_txt = (" (%s)" % d["motivo"]) if d.get("motivo") else ""
        print("  %-16s %-7s %5.0f ms %s%s" % (i, est, dt * 1000, "OK" if not p else "FALLO " + "; ".join(p), extra_txt))
        resumen.append((etiqueta, i, est, d.get("motivo")))
        fallos.extend("%s/%s: %s" % (etiqueta, i, x) for x in p)
    r, dt = lanzar([os.path.join(FUENTES, "ejecutar-todas.py")] + extra, env)
    p = []
    try:
        d = json.loads(r.stdout)
        faltan = [i for i in ids if i not in d]
        if faltan:
            p.append("faltan " + ",".join(faltan))
        for i in ids:
            if i in d:
                p += ["%s: %s" % (i, x) for x in validar(i, d[i])]
    except ValueError:
        p.append("salida no es JSON")
    if r.returncode != 0:
        p.append("código de salida %d" % r.returncode)
    if dt >= LIM_TODAS:
        p.append("lento: %.2f s" % dt)
    print("  %-16s %-7s %5.0f ms %s" % ("ejecutar-todas", "", dt * 1000, "OK" if not p else "FALLO " + "; ".join(p)))
    fallos.extend("%s/todas: %s" % (etiqueta, x) for x in p)
    if demo and not p:
        estados = sorted({v["estado"] for v in d.values()})
        print("  estados vistos en demo:", ", ".join(estados))
        if not {"ok", "aviso"} <= set(estados):
            fallos.append("demo sin variedad de estados")


def main():
    base = dict(os.environ)
    tmp = tempfile.mkdtemp(prefix="neongrid-prueba-")
    probar("este equipo (real)", base)
    probar("este equipo (--demo)", base, demo=True)
    minimo = {"PATH": "/usr/bin", "HOME": os.path.join(tmp, "x")}      # equivalente a env -i
    probar("env -i PATH=/usr/bin HOME=/tmp/x", minimo)
    sin_rt = dict(base, XDG_RUNTIME_DIR=os.path.join(tmp, "no-existe"))
    probar("XDG_RUNTIME_DIR inexistente", sin_rt)
    # el fichero ~/.config/neongrid/demo activa el modo demo sin argumentos
    cfg = os.path.join(tmp, "cfg", "neongrid")
    os.makedirs(cfg)
    open(os.path.join(cfg, "demo"), "w").close()
    r, _ = lanzar([os.path.join(FUENTES, "ejecutar-todas.py")], dict(base, XDG_CONFIG_HOME=os.path.join(tmp, "cfg")))
    ok = all(v.get("demo") for v in json.loads(r.stdout).values())
    print("\nfichero demo activa el modo demo:", "OK" if ok else "FALLO")
    if not ok:
        fallos.append("fichero demo no activa el modo demo")
    # i18n
    r = subprocess.run([sys.executable, I18N], capture_output=True, text=True)
    print("i18n:", (r.stdout or r.stderr).strip())
    if r.returncode:
        fallos.append("i18n: " + r.stdout)
    neutros = sorted({"%s (%s)" % (i, m) for e, i, s, m in resumen if s == "neutro" and e.startswith("este equipo (real)")})
    print("\nNeutras en este equipo:", "; ".join(neutros) or "ninguna")
    print("\nRESULTADO:", "TODO OK" if not fallos else "%d fallo(s)" % len(fallos))
    for f in fallos:
        print("  -", f)
    return 1 if fallos else 0


if __name__ == "__main__":
    sys.exit(main())
