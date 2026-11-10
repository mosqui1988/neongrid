# NeonGrid

Tema cyberpunk en pixel art para **KDE Plasma 6**: una ciudad nocturna animada donde cada cartel muestra datos reales de tu equipo (CPU, GPU, RAM, disco, red, VPN, sincronización, repos de git, batería, actualizaciones…), con ciclo día/noche y ventanas, terminal, iconos y cursor a juego.

## Instalar (sin sudo)
Haz **doble clic en `Instalar NeonGrid.desktop`** (o ejecuta `./instalar.sh --grafico`). Antes de cambiar nada guarda una copia de tus ajustes.

| Botón | Qué hace |
|---|---|
| **Instalar NeonGrid** | copia el tema, guarda tus ajustes originales y lo aplica |
| **Quitar NeonGrid** | deja tu escritorio como estaba; el tema sigue instalado por si quieres volver |
| **Desinstalar NeonGrid** | lo quita y borra todos sus ficheros (te pregunta si borra también tu agenda y consejos) |

Tras instalar, *Quitar* y *Desinstalar* están también en el menú de aplicaciones.

Desde terminal: `./instalar.sh [--sin-fondo] [--sin-panel] [--alacritty] [--sin-aplicar]`, `./revertir.sh`, `./desinstalar.sh [--todo]`.

## Requisitos
KDE Plasma **6** (en Plasma 5 el instalador avisa y no toca nada), `python3`, `kconfig` (`kwriteconfig6`) y `fontconfig`. Si falta algo, el instalador **te muestra** el comando para tu distribución; nunca ejecuta `sudo`.
Probado en CachyOS/Arch. Pendiente de probar: Fedora KDE, openSUSE Tumbleweed, Debian 13.

## Personalizar (`~/.config/neongrid/`)
**Lo fácil:** menú de aplicaciones → **Configurar NeonGrid** (repos de git, agenda, consejos, ciudad y modo calma, con ventanas, sin editar ficheros).
**Guía completa paso a paso: [`GUIA.md`](GUIA.md)** (git, agenda, consejos, ciudad, carteles, demo). Se instala también en `~/.local/share/neongrid/GUIA.md`.

`config.json` (calma, carteles, idioma), `agenda.txt` (`HH:MM texto`), `consejos.txt` (los lee el zepelín), `repos.txt` (repos a vigilar). Un fichero vacío llamado `demo` activa datos ficticios.

## Privacidad
Todo es local: ni red, ni ubicación, ni telemetría. La hora del cielo sale de la zona horaria de tu sistema (o de la ciudad que pongas). Los scripts de datos solo leen `/proc`, `/sys` y herramientas estándar.
