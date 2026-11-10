# -*- coding: utf-8 -*-
"""Utilidades comunes de las fuentes de datos de NeonGrid.

Solo librería estándar (Python 3.9+). Todo es de solo lectura.
Contrato: cada fuente imprime UN objeto JSON y sale con código 0 siempre.
"""
import json
import math
import os
import re
import shutil
import signal
import subprocess
import sys
import time

LIMITE_S = 2          # límite duro de cada fuente (segundos)
ESTADOS = ("ok", "aviso", "error", "neutro")


# --------------------------------------------------------------------------
# Rutas
# --------------------------------------------------------------------------
def home():
    return os.environ.get("HOME") or os.path.expanduser("~")


def dir_config():
    """~/.config/neongrid (respetando XDG_CONFIG_HOME)."""
    base = os.environ.get("XDG_CONFIG_HOME") or os.path.join(home(), ".config")
    return os.path.join(base, "neongrid")


def dir_paquete():
    """Carpeta que contiene fuentes/ e i18n/ (la del script)."""
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def dir_cache():
    """Carpeta para muestras anteriores: $XDG_RUNTIME_DIR/neongrid o /tmp/neongrid-UID."""
    candidatos = []
    rt = os.environ.get("XDG_RUNTIME_DIR")
    if rt and os.path.isdir(rt):
        candidatos.append(os.path.join(rt, "neongrid"))
    candidatos.append("/tmp/neongrid-%d" % os.getuid())
    for c in candidatos:
        try:
            os.makedirs(c, mode=0o700, exist_ok=True)
            if os.access(c, os.W_OK):
                return c
        except OSError:
            continue
    return None


# --------------------------------------------------------------------------
# Lectura de ficheros y comandos
# --------------------------------------------------------------------------
def leer(ruta, defecto=None):
    """Lee un fichero de texto (/proc, /sys...) y lo devuelve sin espacios; defecto si falla."""
    try:
        with open(ruta, "r", encoding="utf-8", errors="replace") as f:
            return f.read().strip()
    except (OSError, ValueError):
        return defecto


def leer_num(ruta, defecto=None):
    v = leer(ruta)
    if v is None:
        return defecto
    try:
        return float(v)
    except ValueError:
        return defecto


def lineas_usuario(ruta):
    """Líneas útiles de un fichero del usuario: sin vacías ni comentarios (#)."""
    txt = leer(ruta)
    if not txt:
        return []
    return [l.strip() for l in txt.splitlines() if l.strip() and not l.strip().startswith("#")]


def hay(herramienta):
    return shutil.which(herramienta) is not None


def ejecutar_cmd(args, timeout=1.5, env_extra=None):
    """Ejecuta un comando con timeout y devuelve (código, stdout) o (None, '') si falla.

    Mata el proceso si se pasa del tiempo: no deja nada colgando."""
    env = dict(os.environ)
    env["LC_ALL"] = "C"
    if env_extra:
        env.update(env_extra)
    try:
        p = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                             stdin=subprocess.DEVNULL, env=env, universal_newlines=True,
                             start_new_session=True)
    except (OSError, ValueError):
        return None, ""
    try:
        out, _ = p.communicate(timeout=timeout)
        return p.returncode, out
    except subprocess.TimeoutExpired:
        try:
            os.killpg(p.pid, signal.SIGKILL)   # solo nuestro propio grupo
        except OSError:
            p.kill()
        try:
            p.communicate(timeout=0.5)
        except Exception:
            pass
        return None, ""


# --------------------------------------------------------------------------
# Configuración e idioma
# --------------------------------------------------------------------------
def config():
    try:
        with open(os.path.join(dir_config(), "config.json"), encoding="utf-8") as f:
            d = json.load(f)
        return d if isinstance(d, dict) else {}
    except (OSError, ValueError):
        return {}


def idioma():
    """'es' o 'en' según config.json (es|en|auto) o variables de entorno."""
    i = str(config().get("idioma", "auto")).lower()
    if i in ("es", "en"):
        return i
    for var in ("LC_ALL", "LC_MESSAGES", "LANG", "LANGUAGE"):
        v = os.environ.get(var, "")
        if v:
            return "es" if v.lower().startswith("es") else "en"
    return "en"


def textos(lang=None):
    """Diccionario plano de i18n/<idioma>.json ({} si no se encuentra)."""
    lang = lang or idioma()
    try:
        with open(os.path.join(dir_paquete(), "i18n", lang + ".json"), encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


# --------------------------------------------------------------------------
# Estados
# --------------------------------------------------------------------------
def estado_umbral(valor, aviso, error):
    """ok / aviso / error según umbrales (valor >= umbral). None -> neutro."""
    if valor is None:
        return "neutro"
    if valor >= error:
        return "error"
    if valor >= aviso:
        return "aviso"
    return "ok"


def peor(*estados):
    """El peor estado de una lista (neutro solo si todos son neutro)."""
    orden = {"error": 3, "aviso": 2, "ok": 1, "neutro": 0}
    return max(estados, key=lambda e: orden.get(e, 0)) if estados else "neutro"


def neutro(motivo, **extra):
    d = {"estado": "neutro", "motivo": motivo}
    d.update(extra)
    return d


# --------------------------------------------------------------------------
# Caché de muestras (deltas entre invocaciones)
# --------------------------------------------------------------------------
def leer_cache(nombre):
    d = dir_cache()
    if not d:
        return None
    try:
        with open(os.path.join(d, nombre + ".json"), encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def guardar_cache(nombre, datos):
    d = dir_cache()
    if not d:
        return
    try:
        tmp = os.path.join(d, "%s.%d.tmp" % (nombre, os.getpid()))
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(datos, f)
        os.replace(tmp, os.path.join(d, nombre + ".json"))   # escritura atómica
    except OSError:
        pass


def muestreo(nombre, tomar, guardar=True, max_edad=30.0):
    """Devuelve (muestra_previa, muestra_actual, dt_segundos).

    Usa la muestra guardada por la invocación anterior. Si no hay (o es muy
    vieja o demasiado reciente) toma dos muestras separadas 100 ms (nunca más)."""
    prev = leer_cache(nombre)
    t1 = time.time()
    actual = tomar()
    if (isinstance(prev, dict) and "t" in prev and "m" in prev
            and 0.05 <= t1 - prev["t"] <= max_edad):
        previa, dt = prev["m"], t1 - prev["t"]
    else:
        # sin muestra útil: segunda muestra 100 ms después
        previa, t0 = actual, t1
        time.sleep(0.1)
        t1 = time.time()
        actual = tomar()
        dt = max(t1 - t0, 0.001)
    ahora = t1
    if guardar:
        guardar_cache(nombre, {"t": ahora, "m": actual})
    return previa, actual, dt


# --------------------------------------------------------------------------
# Demo
# --------------------------------------------------------------------------
def demo_activo(argv=None):
    argv = sys.argv if argv is None else argv
    return "--demo" in argv or os.path.exists(os.path.join(dir_config(), "demo"))


def onda(periodo_s, minimo=0.0, maximo=1.0, fase=0.0, t=None):
    """Seno suave entre minimo y maximo (varía lento, sin saltos aleatorios)."""
    t = time.time() if t is None else t
    s = (math.sin(2 * math.pi * t / periodo_s + fase) + 1) / 2
    return minimo + (maximo - minimo) * s


# --------------------------------------------------------------------------
# Punto de entrada de cada fuente
# --------------------------------------------------------------------------
def _alarma(signum, frame):
    raise TimeoutError("límite de %d s" % LIMITE_S)


def ejecutar(id_, medir, demo=None):
    """Ejecuta medir() (o demo() con --demo), añade id/ts/estado y escribe el JSON.

    Nunca lanza excepciones ni sale con código distinto de 0."""
    try:
        signal.signal(signal.SIGALRM, _alarma)
        signal.alarm(LIMITE_S)
    except (ValueError, AttributeError):
        pass
    try:
        if demo is not None and demo_activo():
            datos = demo()
            datos["demo"] = True
        else:
            datos = medir()
    except BaseException as e:   # incluida la alarma: la fuente nunca falla "fuerte"
        datos = neutro("fallo interno: %s" % type(e).__name__)
    if not isinstance(datos, dict):
        datos = neutro("salida inválida")
    if datos.get("estado") not in ESTADOS:
        datos["estado"] = "neutro"
    datos["id"] = id_
    datos["ts"] = int(time.time())
    try:
        signal.alarm(0)
        sys.stdout.write(json.dumps(datos, ensure_ascii=False) + "\n")
        sys.stdout.flush()
    finally:
        os._exit(0)   # sale ya, sin esperar hilos ni procesos auxiliares
