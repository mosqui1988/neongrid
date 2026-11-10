# Tema de Plasma y barra superior de NeonGrid

Todo se genera con scripts de la biblioteca estándar de Python (los SVG son rectángulos alineados a rejilla, `shape-rendering="crispEdges"`, colores de `tema/paleta.py`):

| Qué | Script | Salida |
|---|---|---|
| Decoración de ventanas (Aurorae) | `tema/aurorae/generar.py` (+ `pixelsvg.py`) | `paquete/neongrid/share/aurorae/themes/NeonGrid/` |
| Tema de Plasma (desktoptheme) | `tema/plasma/generar.py` | `paquete/neongrid/share/plasma/desktoptheme/NeonGrid/` |
| Disposición del panel | a mano | `paquete/neongrid/neongrid/panel/aplicar-panel.js` |
| Capturas estáticas (necesitan Pillow) | `vista-previa.py` en cada carpeta | `vista-previa.png` |

## Qué cubre el tema de Plasma
`widgets/panel-background` (barra pegada, degradado oscuro tramado, escaneo, borde inferior cian de 2 px), `dialogs/background`, `widgets/background`, `widgets/tooltip`, `widgets/translucentbackground` (esquinas biseladas, borde neón 1 px + halo de 1 px, sombra dura de 2 px, máscaras de desenfoque), variantes `opaque/`, `solid/`, `translucent/`, `widgets/tasks` (foco = subrayado cian + relleno; atención = subrayado **discontinuo** magenta; minimizada = punteado violeta; hover = relleno claro; prefijos `north-`, `west-`, `east-`), `widgets/pager` (escritorios como rombos, activo relleno cian), `button`, `lineedit`, `scrollbar`, `slider` (asa en rombo), `bar_meter_horizontal`, `tabbar`, `viewitem`, `plasmoidheading`, `line`, `icons/battery.svg` (6 rallitas, rojo ≤20 %, ámbar ≤40 %, cian el resto) e `icons/nucleo.svg` / `nucleo-22.svg` (hexágono con `>_`). `colors` es el esquema `tema/colores/NeonGrid.colors`.
Plasma 6 usa el tema `default` para todo SVG que falte; no existe campo `Inherits` (ni hace falta copiar nada de Breeze).

## Aplicar (el instalador lo hará; a mano, en un usuario de pruebas)
1. Copiar `share/plasma/desktoptheme/NeonGrid` a `~/.local/share/plasma/desktoptheme/` y `share/aurorae/themes/NeonGrid` a `~/.local/share/aurorae/themes/`.
2. Tema: `plasma-apply-desktoptheme NeonGrid`. Ventanas: `kwriteconfig6 --file kwinrc --group org.kde.kdecoration2 --key library org.kde.kwin.aurorae` y `--key theme __aurorae__svg__NeonGrid`, luego `qdbus6 org.kde.KWin /KWin reconfigure`. Escritorios: `kwriteconfig6 --file kwinrc --group Desktops --key Number 4`.
3. Panel (sin reiniciar plasmashell): hacer copia de `~/.config/plasma-org.kde.plasma.desktop-appletsrc`, sustituir en el `.js` `__NUCLEO__` por la ruta absoluta de `nucleo-22.svg` (y `__LANZADORES__` si se quieren fijar lanzadores; vacío = no tocar) y ejecutar
   `qdbus6 org.kde.plasmashell /PlasmaShell org.kde.PlasmaShell.evaluateScript "$(cat aplicar-panel.js)"`
   (alternativa: pegarlo en `plasma-interactive-console`). Si se prefiere recargar: `plasmashell --replace &`.
   El script reutiliza el primer panel (lo vacía) o crea uno; deja el resto de paneles intactos.

## Revertir
- Panel: cerrar sesión o `kquitapp6 plasmashell`, restaurar la copia de `plasma-org.kde.plasma.desktop-appletsrc` y `plasmashell --replace &` (o `kstart plasmashell`). `revertir.sh` del instalador debe hacerlo con `copia-previa/`.
- Tema de Plasma: `plasma-apply-desktoptheme <anterior>`. Ventanas: volver a poner la clave `theme` anterior en `kwinrc` (`kwriteconfig6 ...`) y `reconfigure`.
- Quitar ficheros: borrar las dos carpetas `NeonGrid` de `~/.local/share`.

## Limitaciones conocidas (no se pueden resolver con SVG)
- Un SVG de icono no anima en Qt: el núcleo **no pulsa** ni brilla al pasar el ratón (el brillo de hover lo decide Kickoff).
- El reloj «en muesca biselada» no se puede dibujar desde el tema (el reloj digital no tiene marco SVG); la fecha sale `21:37 · mar 10 nov` (Qt no pone mayúsculas).
- La franja lateral de color por gravedad en las notificaciones no existe en el tema de Plasma: las notificaciones usan `dialogs/background` y ese marco es común a todos los popups. Haría falta una plantilla `look-and-feel` (QML propio).
- Los iconos de la bandeja (VPN, sync, red, volumen, batería) los pone el tema de iconos; `icons/battery.svg` solo se usa donde Plasma lee los iconos de panel del tema. VPN va dentro del applet de red; «sync» solo aparece si hay un applet de Syncthing instalado.
- Los nombres de elementos de `tasks`/`pager` y los valores de configuración del script (`displayedText`, `pagerLayout`...) se basan en el tema `default` y en PixelZen; no se han podido probar en un Plasma vivo.
