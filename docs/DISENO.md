# NeonGrid — diseño (v0, 2026-11-10)

Tema cyberpunk/hacker para KDE Plasma 6, hermano de PixelZen. Ciudad nocturna en pixel art donde cada decoración es un dato real. Pensado para cualquiera que lo instale.

## Decisiones cerradas
| Tema | Decisión | Por qué |
|---|---|---|
| Nombre | **NeonGrid** | corto, descriptivo, libre de marcas |
| Barra | **Superior, 32 px, ancho completo, pegada** | conserva alto útil (pantallas 16:10), coherente con PixelZen, no choca con iconos en columnas |
| Paleta | **Cian + magenta** como acentos; **verde ácido** solo para «OK» y texto de terminal | más cyberpunk; el verde da el guiño hacker sin cansar |
| Fuentes | **Chakra Petch** (interfaz y titulares), **Departure Mono** (carteles, datos, terminal) | Departure ya validada; Chakra es cuadrada, futurista y legible a 11-12 pt |
| Píxel | **2×2** (lienzo 960×600 → 1920×1200), antes 3×3 | más detalle y calidad manteniendo el estilo pixel |

## Lenguaje visual
- Esquinas biseladas a 45°, nunca redondeadas. Borde neón de 1 px con «corchetes» en las esquinas.
- Líneas de escaneo muy sutiles (~5 %) solo en popups y ventanas. Sin desenfoques: el brillo es halo en píxeles de 3 escalones.
- Solo dos estilos de sombra: sombra dura de 1 px desplazada y halo de neón. Nada de sombras grises difusas.

## Calidad de imagen (requisito)
- **Paleta global limitada (~40 colores)** repartida en rampas de 4 tonos por material: sombra, base, luz y brillo. Coherencia pixel art con volumen real.
- **Luz de neón**: cada cartel ilumina lo cercano con borde de luz de su color (cian o magenta) en los edificios.
- **Profundidad**: 4 planos (fondo lejano con bruma, torres medias, calle, primer plano) con paralaje suave en el fondo animado.
- **Calle mojada** con reflejo vertical al 50 % de los neones (caro de ver, barato de dibujar: capa estática).
- **Contraste por valores**: lo importante (carteles con datos) es lo más luminoso de la escena; el resto, oscuro y de baja saturación.

## Paleta
| Rol | Color |
|---|---|
| Fondo | `#0B0E1A` |
| Panel | `#12172B` |
| Texto | `#E6F1FF` |
| Cian (principal) | `#00E5FF` |
| Magenta (atención) | `#FF2BD6` |
| Verde ácido (OK) | `#39FF88` |
| Ámbar (aviso) | `#FFB020` |
| Rojo (error) | `#FF3B5C` |
| Violeta (estructura) | `#8B5CFF` |
Contraste de texto ≥ 7:1 (validar con script al construir). Estados siempre color **y** forma: ✔ ▲ ✖.

## Barra e inicio
```
◈ │ ◇◆◇◇ │ [▣][▣][▣][▣]        ╲ 21:37 · MAR 10 NOV ╱        ⛨ ⟳ ♪ ≋ ▮▮▮▮▮▯ ⏻
```
- **Inicio:** hexágono «núcleo» con `>_`; late lento en reposo, brillo cian al pasar el ratón. Kickoff compacto con búsqueda arriba (`>`), categorías a la izquierda.
- **Escritorios:** 4 rombos, activo relleno cian.
- **Apps:** solo iconos; subrayado cian = abierta, magenta = pide atención.
- **Centro:** reloj en muesca biselada, Departure Mono 14 px.
- **Bandeja:** escudo VPN (relleno/hueco), sync, volumen, wifi, batería de 6 rallitas, apagado. Sin batería → se oculta.
- Los datos del sistema viven en la escena, no en la barra.

## Ventanas, iconos, cursor
- **Ventanas (Aurorae):** título 28 px en mono a la izquierda; botones `—` `□` `✕` con forma propia; activa = borde cian con halo, inactiva = violeta apagado.
- **Iconos:** rejilla de **32 px** (antes 24) para ganar detalle. Glifos recoloreados (línea cian, detalle magenta), baldosas de app biseladas, luz de borde arriba-izquierda y sombra dura de 1 px.
- **Carpetas:** más finas y menos «bloque»: pestaña biselada, cuerpo de 3 tonos violeta con línea de luz superior y borde interior; en versión llena, hojas asomando. Nada de bloques de píxel grandes.
- **Cursor:** flecha con borde cian y punta magenta; variantes mano e I-beam.
- **Notificaciones:** popup biselado, franja lateral de color + glifo por gravedad.
- **Terminal:** Konsole y Alacritty con la paleta; verde ácido para el prompt `λ`.
- **Bloqueo:** misma escena, reloj grande, cartel «ACCESO BLOQUEADO», campo biselado con `>`.

## Escena y datos reales
Zona izquierda despejada y oscura (poca densidad de detalle) para los iconos de escritorio en columnas.

| Elemento | Dato |
|---|---|
| Torre central | hora, fecha y próximo bloque de estudio |
| Cartel NET | wifi, bajada y subida |
| Torre de plantas | una planta por núcleo, ventanas según carga |
| Neón VPN | verde ✔ / rojo ✖ parpadeo lento |
| Antena con baliza | estado de sincronización (Syncthing) |
| Coches voladores | tráfico de red |
| Drones | actualizaciones pendientes y servicios fallidos |
| Edificio «archivo» | repos git con cambios sin subir |
| Bar con neón | batería y temperatura |
| Dirigible | consejos rotativos desde fichero del usuario |
| Lluvia | intensidad según carga total |
- Texto de carteles dibujado por QML (nítido, en vivo) sobre marcos pixel; letra ≥ 14 px de alto.
- **Ambiente por hora real** (cálculo solar de PixelZen): noche profunda, amanecer magenta/naranja, día con smog verdoso.
- **Alerta:** temperatura crítica o servicio caído → tinte rojo suave y cartel «ALERTA».
- **Estudio:** pomodoro y agenda desde `~/.config/neongrid/agenda.txt`.
- Fase 2: clic o hover en carteles abre la herramienta correspondiente.

## Que se adapte a quien lo instale
- **Pantalla:** capas ancladas; 16:10, 16:9, 21:9 y 4K con escala de píxel entera; varios monitores; HiDPI con texto relativo.
- **Hardware:** sin batería → se oculta; sin VPN/Syncthing/git → estado neutro «no configurado», nunca rojo; GPU modesta → baja calidad sola según fps medidos.
- **Asistente gráfico** en el primer arranque: carteles a mostrar, ciudad, idioma, modo calmo.
- **Idiomas:** es y en desde el inicio, textos en fichero aparte.
- **Fuentes de datos como plugins:** scripts que devuelven JSON en `fuentes/`; cualquiera añade el suyo.
- **Ficheros del usuario** (consejos, agenda) en `~/.config/neongrid/`, con ejemplos.
- **Ciudad por defecto genérica**; sin datos personales en el paquete.

## Distros
- Objetivo: **Plasma 6 en cualquier distro** (Arch, CachyOS, Manjaro, Fedora KDE, openSUSE Tumbleweed, Debian 13). Kubuntu 24.04 y Debian 12 (Plasma 5.27) no valen: el instalador lo detecta y avisa.
- Todo en `~/.local/share`, sin root. Detecta la familia de distro y **muestra** el comando para dependencias; no ejecuta `sudo`.
- Datos desde `/proc`, `/sys` y herramientas estándar; si falta una, el cartel va neutro.
- Probar en CachyOS (T14s y torre) + VM Fedora KDE + VM Debian 13, en Wayland y X11.
- GNOME: fase posterior (PixelZen ya tiene `gnome/`), reutilizando imágenes.

## Rendimiento y seguridad
- Animación a 8 fps, pausa con batería baja, objetivo ≤ 3 % de CPU. Medir consumo antes y después (el T14s va en `power-saver`).
- Más resolución (2×2) = más tiempo de generación en Python y más memoria: aceptable porque se genera una vez al instalar; la animación usa capas/sprites.
- Modo calmo (sin lluvia ni parpadeos). Ningún parpadeo > 3 Hz.
- Todo local, sin red; modo demo con datos ficticios (`~/.config/neongrid/demo`).

## Instalación
`.tar.gz` autocontenido con `instalar.sh`, `desinstalar.sh`, `revertir.sh`; `Instalar NeonGrid.desktop` y `Desinstalar NeonGrid.desktop` para doble clic con diálogo gráfico (`--grafico`); copia del estado original antes de aplicar; convive con PixelZen.
