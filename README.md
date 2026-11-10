# NeonGrid

> Una ciudad cyberpunk en pixel art, animada, para **KDE Plasma 6**. Cada cartel de neón es un dato real de tu equipo: CPU, RAM, red, VPN, repos de git, batería… Con sol, luna, lluvia, trenes, coches y un zepelín que te da consejos.
> Cómo se hizo, con todo el proceso: **https://ralcaniz.dev/posts/neongrid-ciudad-cyberpunk-kde/**

![NeonGrid de noche: la ciudad con la lluvia, los carteles con datos reales, el zepelín y la luna](capturas/noche.gif)

**Se instala en 1 minuto, sin `sudo` y sin tocar nada del sistema:** todo va a tu carpeta personal y se puede quitar con un clic.

---

## Instalar (3 pasos)

1. **Descarga** `neongrid-1.0.0.tar.gz` desde [Releases](../../releases) y descomprímelo (clic derecho → *Extraer aquí*).
2. **Doble clic en `Instalar NeonGrid`.** Te pregunta qué quieres instalar y guarda una copia de tus ajustes antes de cambiar nada.
3. **Listo.** El escritorio se reinicia solo unos segundos y ya tienes la ciudad.

> ¿No te deja ejecutar el doble clic? Abre una terminal en la carpeta y escribe `./instalar.sh`.

SHA-256 del paquete: `d8d7297940a6537aa18eb41ad9d3f9558111623039c76644c2ddf70c6ad1d6ec`

### Requisitos

| Qué | Detalle |
|---|---|
| **KDE Plasma 6** | Probado en CachyOS con Plasma 6.8 (Wayland). Plasma 5 **no** vale; el instalador lo detecta y no toca nada. |
| `python3`, `kconfig` (`kwriteconfig6`), `fontconfig` | Casi seguro que ya los tienes. Si falta algo, el instalador te dice **qué comando ejecutar tú** para tu distribución (nunca lo hace por ti). |
| `kdialog` (opcional) | Para las ventanas del instalador y de «Configurar NeonGrid». Viene con KDE. |
| Una GPU cualquiera | La animación es ligera (8 imágenes por segundo). Si tu equipo va justo, baja la calidad sola. Sin aceleración gráfica muestra la imagen estática. |

**Sin `sudo`, sin root, sin red.** Nada se instala en el sistema: todo va a `~/.local/share` y `~/.config`. NeonGrid no usa internet ni pide tu ubicación para nada.

### Qué cambia al instalar (y cómo volver atrás)

Cambia el aspecto de tu escritorio: **fondo animado, colores, ventanas, iconos, cursor, tema de Plasma, perfil de Konsole, fuentes y la barra superior** (la reorganiza: menú, escritorios, tareas, reloj y bandeja). Si tenías widgets de otro tema (por ejemplo, el HUD de [PixelZen](https://github.com/mosqui1988/pixelzen)), los **desactiva** para que no se mezclen.

| Quiero… | Cómo |
|---|---|
| **Volver a como estaba** | Menú de aplicaciones → **Quitar NeonGrid** (o `~/.local/share/neongrid/revertir.sh`). Restaura la copia que se guardó al instalar. |
| **Borrarlo del todo** | Menú de aplicaciones → **Desinstalar NeonGrid**. Te pregunta si borra también tu agenda y ajustes. |

---

## Cómo se ve

### Momentos del día

El fondo no es una imagen: es una escena que sigue al sol **de tu ciudad** (se calcula en tu equipo con la fecha y tu zona horaria). Cuatro momentos, grabados de verdad:

| Amanecer | Día |
|---|---|
| ![Amanecer](capturas/amanecer.gif) | ![Día](capturas/dia.gif) |
| **Atardecer** | **Noche** |
| ![Atardecer](capturas/atardecer.gif) | ![Noche](capturas/noche.gif) |

*Los datos de las capturas son de demostración (modo demo). Se mueven la lluvia, los coches, el tren, los drones, las luces de las ventanas y el zepelín, que además flota suavemente.*

**Un día entero en 10 segundos:** el sol sale por el horizonte, cruza el cielo y se pone; de noche sale la luna (con su fase real).

![Ciclo de 24 horas en 10 segundos](capturas/ciclo.gif)

### Se adapta a tu pantalla

La escena es de 960×600 píxeles y se escala por números enteros para que el pixel art quede nítido. En pantallas pequeñas se ajusta para que siempre llene la pantalla (recorta un poco por la izquierda y abajo; los carteles se quedan a la vista).

| Resolución | Cómo queda |
|---|---|
| 1024×768 · 1280×720 · 1366×768 · 1280×1024 | Escala ajustada (1,3×–1,7×): llena la pantalla |
| 1440×900 · 1600×900 · 1920×1080 · 1920×1200 | 2× entero: pixel perfecto |
| 2560×1440 · 2560×1600 · 3840×2160 | 3×–4× entero: pixel perfecto |
| Ultrapanorámicas (2560×1080, 3440×1440) | La ciudad llena el alto y los lados se rellenan con la ciudad desenfocada. Es el caso más flojo: funciona, pero no luce igual |

![1366×768](capturas/resolucion-1366x768.png)
![2560×1440](capturas/resolucion-2560x1440.png)

### Todo el tema, a juego

Ventanas, tema de Plasma, iconos, cursor y terminal con la misma paleta de 42 colores (cian y magenta de acento, verde ácido para el «OK»):

| Ventanas | Tema de Plasma |
|---|---|
| ![Decoración de ventanas](capturas/piezas-ventanas.png) | ![Tema de Plasma](capturas/piezas-plasma.png) |

Así queda el escritorio completo (es una **maqueta** hecha con el mismo generador, para enseñar barra, iconos y ventanas juntos):

![Maqueta del escritorio completo](capturas/maqueta-escritorio.png)

---

## Qué enseña cada cartel

| Cartel | Dato real | Si no lo tienes |
|---|---|---|
| **Reloj** | hora, fecha y el próximo aviso de tu agenda | — |
| **CPU** | uso por núcleo, frecuencia, temperatura | — |
| **Sistema** | RAM, GPU y disco | la GPU sale apagada |
| **Red** | bajada y subida | — |
| **VPN** | activa o no | «sin configurar» |
| **Repos** | repos de git con cambios y commits sin subir | «sin repositorios» |
| **Batería** | carga y temperatura | sale apagado |
| **Drones** | actualizaciones pendientes, servicios caídos, Syncthing | apagados |
| **Zepelín** | consejos que tú escribes | usa unos por defecto |
| **Lluvia** | más fuerte cuanta más carga tenga el equipo | — |

Los estados no dependen solo del color: llevan también forma (✔ ▲ ✖). Todo se lee de `/proc`, `/sys` y herramientas estándar; **solo lectura**. Si falta algo, el cartel sale apagado, nunca da error.

---

## Configurarlo (sin editar ficheros)

Menú de aplicaciones → **Configurar NeonGrid**. Con ventanas de KDE puedes:

- **Añadir un repo de git** eligiendo la carpeta con el selector (sin escribir rutas).
- **Editar tu agenda** y los **consejos del zepelín**.
- **Poner tu ciudad** (para afinar el amanecer y el atardecer).
- Activar el **modo calma** (menos movimiento).

La guía completa, por si quieres editar los ficheros a mano: [`paquete/neongrid/GUIA.md`](paquete/neongrid/GUIA.md).

---

## Antes y después

Esto empezó con una imagen de referencia: una ciudad japonesa de noche, con lluvia y mucho neón. Quería un escritorio así, pero en pixel art y con **datos de verdad** en los carteles.

**Primera idea:** una ciudad **isométrica**. Bonita, pero los carteles quedaban pequeños y todo se parecía demasiado.

![Primera idea, isométrica](capturas/historia/1-primera-idea-isometrica.png)

**Segunda versión:** más edificios y más detalle, pero seguía sin tener la profundidad de la referencia.

![Segunda versión, isométrica](capturas/historia/2-segunda-version-isometrica.png)

**La buena:** cambié a una **vista en perspectiva** con puntos de fuga, una avenida con tren elevado, niebla por capas y los carteles como lo más luminoso de la escena. Ahí sí.

![Resultado final](capturas/noche.png)

---

## Cómo está hecho (resumen)

- **Python + Pillow dibujan la ciudad por código**, píxel a píxel (no hay ni un dibujo a mano): edificios con rampas de 4 tonos, ventanas, calles mojadas, niebla, carteles… con una paleta global de **42 colores**.
- **Un shader GLSL** hace todo lo que se mueve, a la resolución lógica (960×600): luces de ventanas, coches, tren, drones, lluvia, balizas, y ahora **sol y luna** (que se ocultan tras los edificios gracias a un mapa de profundidad).
- **QML** pinta lo vivo encima: el texto de los carteles, la pantalla LED del zepelín (matriz 5×7 de verdad) y el propio zepelín, que flota.
- **Scripts de Python (solo librería estándar)** leen los datos del equipo y los pasan como JSON.
- El diseño, el código y las pruebas los hice **con Claude Code**; todo el proceso, errores incluidos, está en el artículo del blog.

Para entrar a fondo: [`docs/DISENO.md`](docs/DISENO.md) (decisiones de diseño) y [`docs/ARQUITECTURA.md`](docs/ARQUITECTURA.md) (cómo encajan las piezas).

### Reconstruir el fondo (solo si quieres tocar el código)

El paquete **ya trae las capas hechas**; esto es solo para modificarlas. Necesitas Python con **Pillow**, `qsb` (Qt Shader Tools), las fuentes *Departure Mono*, *Micro 5* y *DotGothic16* (todas OFL; descárgalas de Google Fonts o de sus repos) en una carpeta y su ruta en `NG_FUENTES`:

```bash
python3 -m venv .venv && .venv/bin/pip install pillow
NG_FUENTES=~/mis-fuentes .venv/bin/python tema/fondo/construir-capas.py   # ~20 s
tema/empaquetar.sh 1.0.0                                                    # genera dist/neongrid-1.0.0.tar.gz
tema/capturas/hacer-capturas.sh capturas/                                   # capturas y GIFs (usa un KWin virtual)
```

---

## Problemas frecuentes

| Problema | Solución |
|---|---|
| «Faltan estas herramientas» | El instalador te da el comando exacto para tu distro. Ejecútalo tú y vuelve a instalar. |
| El doble clic no hace nada | Abre una terminal en la carpeta y ejecuta `./instalar.sh`. |
| El fondo va a tirones o gasta batería | Activa el **modo calma** en «Configurar NeonGrid». La animación se pausa sola con la pantalla bloqueada o la batería baja. |
| Me quedó el escritorio a medias | Cierra sesión y vuelve a entrar, o usa **Quitar NeonGrid**. |
| Quiero mi ciudad exacta | «Configurar NeonGrid» → *Mi ciudad*. |

Si algo no funciona en tu distribución, abre un [issue](../../issues) con tu distro y la versión de Plasma (`plasmashell --version`).

---

## Licencia y créditos

- Código y arte: **GPL-3.0-or-later** (ver `LICENSE`).
- Fuentes: **Chakra Petch** y **Departure Mono**, ambas bajo SIL OFL 1.1; sus licencias van en `paquete/neongrid/share/fonts/neongrid/`.
- Hermano de [PixelZen](https://github.com/mosqui1988/pixelzen), el tema de Japón antiguo.

---

## English (short)

**NeonGrid** is an animated pixel-art cyberpunk city wallpaper and theme for **KDE Plasma 6**. Every neon sign shows real data from your machine (CPU, RAM, network, VPN, git repos, battery…), with a real-time sun and moon, rain, trains, cars and a floating blimp. **Install:** download the `.tar.gz` from Releases, extract it and double-click *Instalar NeonGrid* (or run `./instalar.sh`). **No `sudo`, no root, no network:** everything goes into your home folder and one click removes it. Tested on CachyOS (Plasma 6.8, Wayland). GPL-3.0-or-later.
