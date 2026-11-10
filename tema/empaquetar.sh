#!/usr/bin/env bash
# Empaqueta paquete/neongrid en dist/neongrid-VERSION.tar.gz tras comprobar privacidad y pasar las pruebas del instalador.
set -euo pipefail
R="$(cd "$(dirname "$0")/.." && pwd)"; V="${1:-1.0.0}"; P="$R/paquete/neongrid"
"$R/tema/empaquetar-base.sh" >/dev/null
echo "== Privacidad: buscando datos personales en el paquete"
if grep -rIn -i -E "ruben|mosqui|/home/[a-z]+|@gmail" "$P" 2>/dev/null | grep -v -E "^Binary" | grep -v -F "https://github.com/mosqui1988/neongrid" | head -20 | grep .; then echo "ERROR: hay datos personales arriba"; exit 1; fi
echo "   limpio"
echo "== Pruebas del instalador"; bash "$R/tema/probar-instalador.sh" | tail -3
mkdir -p "$R/dist"; T="$R/dist/neongrid-$V.tar.gz"
tar -C "$R/paquete" --exclude='__pycache__' --exclude='*.pyc' --owner=0 --group=0 -czf "$T" neongrid
echo "== Paquete: $T ($(du -h "$T" | cut -f1)), $(tar -tzf "$T" | wc -l) ficheros"
