#!/usr/bin/env bash
# Copia al paquete lo que genera tema/ (colores y perfil de Konsole). Lo demas lo genera cada pieza.
set -euo pipefail
R="$(cd "$(dirname "$0")/.." && pwd)"; P="$R/paquete/neongrid"
python3 "$R/tema/generar-colores.py" "${1:-0.80}" >/dev/null
mkdir -p "$P/share/color-schemes" "$P/share/konsole"
cp "$R/tema/colores/NeonGrid.colors" "$P/share/color-schemes/"
cp "$R/tema/colores/NeonGrid.colorscheme" "$R/tema/colores/NeonGrid.profile" "$P/share/konsole/"
echo "base empaquetada (opacidad terminal ${1:-0.80})"
