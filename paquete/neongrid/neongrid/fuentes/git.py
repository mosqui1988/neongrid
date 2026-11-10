#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Fuente git: repos con cambios sin confirmar y commits sin subir (solo lectura).

Lee repos.txt del usuario o busca repos en ~/Proyectos ~/projects ~/src ~/dev ~/code (prof. <= 3).
El resultado se guarda 30 s en caché para no lanzar git cada 2 s."""
import os, sys, time
from concurrent.futures import ThreadPoolExecutor, wait
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import comun

DIRS_DEFECTO = ("Proyectos", "projects", "src", "dev", "code")
IGNORAR = {"node_modules", "__pycache__", "venv", ".venv", "target", "build", "dist"}
MAX_REPOS = 60
PRESUPUESTO = 1.3        # segundos para todo el trabajo
TTL_CACHE = 30


def _repos():
    ruta = os.path.join(comun.dir_config(), "repos.txt")
    if os.path.exists(ruta):
        lista = [os.path.expanduser(l) for l in comun.lineas_usuario(ruta)
                 if os.path.isdir(os.path.join(os.path.expanduser(l), ".git"))]
        if lista:                                   # con rutas validas: solo esas; sin ninguna (p. ej. todo comentado): busqueda automatica
            return lista, True
    res = []
    t0 = time.time()
    for d in DIRS_DEFECTO:
        raiz = os.path.join(comun.home(), d)
        if not os.path.isdir(raiz):
            continue
        base = raiz.rstrip("/").count("/")
        for dirpath, dirs, _ in os.walk(raiz):
            if ".git" in dirs:
                res.append(dirpath)
                dirs[:] = []                       # no entrar dentro de un repo
                continue
            if dirpath.count("/") - base >= 3 or time.time() - t0 > 0.4:
                dirs[:] = []
            else:
                dirs[:] = [x for x in dirs if not x.startswith(".") and x not in IGNORAR]
            if len(res) >= MAX_REPOS:
                return res, False
    return res, False


def _revisar(repo):
    env = {"GIT_OPTIONAL_LOCKS": "0"}              # status no escribe el índice
    rc, out = comun.ejecutar_cmd(["git", "-C", repo, "status", "--porcelain"], timeout=1.0, env_extra=env)
    cambios = bool(out.strip()) if rc == 0 else False
    rc, out = comun.ejecutar_cmd(["git", "-C", repo, "rev-list", "--count", "@{u}..HEAD"],
                                 timeout=1.0, env_extra=env)
    sin_subir = int(out.strip()) if rc == 0 and out.strip().isdigit() else 0
    return cambios, sin_subir


def medir():
    if not comun.hay("git"):
        return comun.neutro("git no está instalado", repos_con_cambios=0, sin_subir=0, total=0)
    c = comun.leer_cache("git")
    if isinstance(c, dict) and time.time() - c.get("t", 0) < TTL_CACHE and "r" in c:
        return c["r"]
    repos, _ = _repos()
    if not repos:
        return comun.neutro("sin repositorios que vigilar", repos_con_cambios=0, sin_subir=0, total=0)
    ex = ThreadPoolExecutor(max_workers=8)
    futuros = [ex.submit(_revisar, r) for r in repos]
    hechos, _ = wait(futuros, timeout=PRESUPUESTO)
    ex.shutdown(wait=False)
    con_cambios = sin_subir = 0
    for f in hechos:
        try:
            cam, ss = f.result()
        except Exception:
            continue
        con_cambios += 1 if cam else 0
        sin_subir += ss
    r = {"estado": "aviso" if sin_subir > 0 else "ok", "repos_con_cambios": con_cambios,
         "sin_subir": sin_subir, "total": len(repos)}
    comun.guardar_cache("git", {"t": time.time(), "r": r})
    return r


def demo():
    return {"estado": "aviso", "repos_con_cambios": 2 + int(comun.onda(300, 0, 2.99)),
            "sin_subir": 3, "total": 7}


if __name__ == "__main__":
    comun.ejecutar("git", medir, demo)
