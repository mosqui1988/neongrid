#!/bin/sh
# se ejecuta dentro de un KWin virtual aislado (ver probar.sh): lanza el guion indicado
sh "$NG_SESION_CMD" > "$NG_SESION_LOG" 2>&1
