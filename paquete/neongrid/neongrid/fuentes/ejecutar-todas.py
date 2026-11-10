#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Ejecuta todas las fuentes en paralelo y escribe UN JSON {id: objeto}.

- Cada fuente corre en su propio proceso con tope de 2 s; si falla o se pasa de
  tiempo se sustituye por {"estado": "neutro", ...}. Sale siempre con código 0.
- «trafico» no se ejecuta aparte: se deriva del resultado de «red» (misma muestra).
- Acepta --demo y se puede ampliar: cualquier <id>.py nuevo en esta carpeta
  (que imprima un JSON) se incluye solo.
"""
import glob
import importlib.util
import json
import os
import signal
import subprocess
import sys
import time

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import comun

LIMITE = 2.0
FUENTES_BASE = ["cpu", "ram", "gpu", "disco", "red", "vpn", "sync", "git", "bateria",
                "actualizaciones", "servicios", "agenda", "consejos", "trafico", "carga"]
PROPIAS = {"comun", "ejecutar-todas"}


def _lista():
    extra = sorted(os.path.basename(f)[:-3] for f in glob.glob(os.path.join(AQUI, "*.py"))
                   if os.path.basename(f)[:-3] not in PROPIAS | set(FUENTES_BASE)
                   and not os.path.basename(f).startswith("_"))
    return FUENTES_BASE + extra


def _trafico():
    spec = importlib.util.spec_from_file_location("trafico_ng", os.path.join(AQUI, "trafico.py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m.derivar


def main():
    demo = "--demo" in sys.argv
    ahora = time.time()
    ids = _lista()
    procs = {}
    for i in ids:
        if i == "trafico":
            continue
        cmd = [sys.executable, os.path.join(AQUI, i + ".py")] + (["--demo"] if demo else [])
        try:
            procs[i] = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                                        stdin=subprocess.DEVNULL, universal_newlines=True,
                                        start_new_session=True)
        except OSError:
            procs[i] = None
    fin = time.time() + LIMITE
    res = {}
    for i, p in procs.items():
        if p is None:
            res[i] = comun.neutro("no se pudo lanzar")
            continue
        try:
            out, _ = p.communicate(timeout=max(0.05, fin - time.time()))
            res[i] = json.loads(out.strip().splitlines()[-1])
            if not isinstance(res[i], dict):
                raise ValueError
        except subprocess.TimeoutExpired:
            try:
                os.killpg(p.pid, signal.SIGKILL)       # solo el grupo de esa fuente
            except OSError:
                p.kill()
            try:
                p.communicate(timeout=0.3)
            except Exception:
                pass
            res[i] = comun.neutro("tiempo agotado (2 s)")
        except Exception:
            res[i] = comun.neutro("salida inválida")
        res[i]["id"] = i
        res[i].setdefault("ts", int(ahora))
    if "trafico" in ids:
        try:
            t = _trafico()(res.get("red"))
        except Exception:
            t = comun.neutro("no se pudo derivar")
        t["id"], t["ts"] = "trafico", int(ahora)
        if demo or comun.demo_activo():
            t["demo"] = True
        res["trafico"] = t
    # orden estable: el de la lista de fuentes
    salida = {i: res[i] for i in ids if i in res}
    sys.stdout.write(json.dumps(salida, ensure_ascii=False) + "\n")
    sys.stdout.flush()


if __name__ == "__main__":
    try:
        main()
    except BaseException:
        sys.stdout.write(json.dumps({"error": comun.neutro("fallo interno")}) + "\n")
    os._exit(0)
