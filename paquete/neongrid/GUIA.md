# NeonGrid — guía de configuración

## La forma fácil: «Configurar NeonGrid»

Abre el menú de aplicaciones y busca **Configurar NeonGrid** (o ejecuta `~/.local/share/neongrid/configurar.sh`). Sale un menú con ventanas de KDE:

- **Git:** añadir un repositorio (eliges la carpeta con el selector, sin escribir rutas), quitar repositorios o volver a la búsqueda automática.
- **Agenda** y **consejos del zepelín:** abre el fichero en tu editor.
- **Mi ciudad:** escribes dos números, por ejemplo `39.47 -0.38`; vacío = automático.
- **Modo calma:** sí / no.

Con eso tienes lo habitual cubierto. El resto de este documento explica los ficheros por si quieres editarlos a mano o entender qué hace cada cosa.

---

## Los ficheros (para editar a mano)

Todo lo que puedes ajustar son **ficheros de texto** en una sola carpeta: `~/.config/neongrid/`. El instalador la crea con ejemplos. No hace falta reiniciar nada, solo guardar el fichero y esperar unos segundos.

| Fichero | Para qué | Se nota en… |
|---|---|---|
| `config.json` | idioma, modo calma, qué carteles se ven, tu ciudad | hasta 1 minuto |
| `repos.txt` | qué repositorios git vigila el cartel **REPOS** | hasta 30 s |
| `agenda.txt` | avisos del día en el cartel del reloj | unos segundos |
| `consejos.txt` | frases que pasan por la pantalla del zepelín | cada 10 min rota la frase |
| `demo` (fichero vacío) | datos ficticios, para capturas | hasta 1 minuto |

> Si algo se rompe, borra el fichero: NeonGrid usa valores por defecto. Para volver a tener el ejemplo, cópialo de `~/.local/share/neongrid/ejemplos/`.

---

## 1. Fecha, hora y ciclo día/noche: es automático

No tienes que configurar nada.

- **Fecha y hora:** salen del reloj de tu equipo.
- **Ciclo día/noche:** se calcula **en tu equipo** (sin internet, sin ubicación) a partir de la fecha y de dónde estás, con la posición real del sol. De ahí salen:
  - el **modo del cielo**: noche, amanecer, día o atardecer, con fundidos entre ellos;
  - el **sol** (sale por la izquierda, cruza y se pone por la derecha) y la **luna** (de noche; con la fase real);
  - que los días sean más cortos en invierno y más largos en verano.
- **¿De dónde saca "dónde estás"?** Si no le dices nada, usa la **zona horaria del sistema** para la longitud y una latitud de 40° N. Eso es suficiente para España y la mayor parte de Europa: el amanecer puede desviarse unos minutos.

### Afinarlo con tu ciudad (opcional)
Busca las coordenadas de tu ciudad en cualquier mapa (clic derecho → "¿Qué hay aquí?") y ponlas en `config.json`:

```json
"ciudad": { "lat": 39.47, "lon": -0.38 }
```
`lat` positiva = norte, `lon` negativa = oeste. Las coordenadas **no salen de tu equipo**.

---

## 2. Git: qué repos vigila el cartel REPOS

El cartel muestra, por ejemplo, `2/7 REPOS  ↑3`:

- `2/7`: **2 repositorios con cambios sin confirmar**, de **7 vigilados**.
- `↑3`: **3 commits hechos que aún no has subido** (`git push`) en total.

Solo lee (`git status` y `git rev-list`); nunca modifica nada.

### Opción A — automático (por defecto)
Si no haces nada, busca repos dentro de `~/Proyectos`, `~/projects`, `~/src`, `~/dev` y `~/code` (hasta 3 niveles de profundidad, máx. 60 repos).

### Opción B — tú eliges (recomendado si tus repos están en otro sitio)
Edita `~/.config/neongrid/repos.txt`: **una ruta por línea**, `~` vale como tu carpeta personal. Las líneas con `#` se ignoran.

```
~/Proyectos/neongrid
~/Proyectos/blog
~/clase/practicas-java
```

Reglas importantes:
- En cuanto haya **al menos una ruta válida** (que tenga `.git`), se vigilan **solo las que listes**.
- Si el fichero solo tiene comentarios, o está vacío, **vuelve a la búsqueda automática**.
- Si una ruta no existe o no es un repo, se salta sin avisar. Compruébalo con: `ls ~/ruta/del/repo/.git`.
- Si el cartel dice "sin repositorios que vigilar", ningún sitio tiene `.git` o `git` no está instalado (`git --version`).

Para ocultar el cartel entero: `"repos": false` en `config.json` (ver sección 5).

---

## 3. Agenda: avisos del día

`~/.config/neongrid/agenda.txt`, una línea por aviso, formato **`HH:MM texto`** (24 h):

```
09:00 Bloque de estudio
11:00 Pausa
16:00 Entregar practica
```

- El cartel del reloj muestra **el próximo aviso de hoy** (hora + texto, que se desplaza si es largo).
- Si no queda ninguno hoy, pone "sin agenda hoy".
- Es la **misma agenda todos los días** (no distingue días de la semana).
- Si hay una **alerta** (CPU a más de 90 °C o un servicio caído), la alerta ocupa esa línea y tapa la agenda hasta que desaparezca.

---

## 4. Consejos: lo que pasa por el zepelín

`~/.config/neongrid/consejos.txt`, **una frase por línea**; las líneas con `#` se ignoran. Si borras el fichero se usan los consejos por defecto.

- Se muestran **3 frases seguidas** y la selección rota cada **10 minutos**.
- La pantalla es una **matriz LED de 5×7**: va en **MAYÚSCULAS**, **sin acentos** (Á→A, Ñ→N) y soporta letras, números y `. , : ; ! ? - + = _ / % > < ( ) ' " # * @`. Cualquier otro símbolo (emojis, etc.) sale como un espacio.
- Frases cortas quedan mejor.

---

## 5. `config.json`: lo demás

```json
{
  "idioma": "auto",
  "calma": false,
  "carteles": {
    "hora": true, "sistema": true, "net": true, "cpu": true, "vpn": true, "sync": true,
    "drones": true, "repos": true, "bar": true, "consejos": true, "lluvia": true
  },
  "ciudad": null
}
```

| Clave | Valores | Efecto |
|---|---|---|
| `idioma` | `"auto"`, `"es"`, `"en"` | `auto` sigue el idioma de tu sistema |
| `calma` | `true` / `false` | Menos movimiento: el zepelín flota 1 px en vez de 2, el texto LED va más lento, sin parpadeos |
| `carteles` | cada uno `true`/`false` | Muestra u oculta cada pieza (tabla de abajo) |
| `ciudad` | `null` o `{"lat":…,"lon":…}` | Afina amanecer/atardecer (sección 1) |

Qué es cada cartel de `carteles`:

| Nombre | Qué es | De dónde lee |
|---|---|---|
| `hora` | reloj, fecha y agenda | reloj del sistema + `agenda.txt` |
| `cpu` | CPU por núcleo, frecuencia, temperatura | `/proc`, `/sys` |
| `sistema` | RAM, GPU y disco | `/proc`, `/sys`, `nvidia-smi`/`rocm-smi` si existen |
| `net` | bajada/subida de la red | contadores de la interfaz principal |
| `vpn` | VPN activa o no | interfaces de red |
| `sync` | estado de Syncthing | el puerto local de Syncthing (`127.0.0.1:8384`); si no lo usas, sale "sin configurar" |
| `repos` | repos git | `repos.txt` (sección 2) |
| `drones` | los drones con etiqueta (actualizaciones, servicios, sync) | `pacman -Qu`/`apt`/`dnf`/`zypper` (**sin red**, caché de 30 min), unidades `systemd` fallidas |
| `bar` | cartel PWR: batería y temperatura de la CPU | `/sys/class/power_supply` (sin batería sale apagado) |
| `consejos` | pantalla de texto del zepelín | `consejos.txt` |
| `lluvia` | la lluvia (más fuerte con más carga del equipo) | carga del sistema |

Los carteles que no tienen datos (por ejemplo, sin batería o sin Syncthing) salen **apagados con "sin configurar"**, nunca con error.

---

## 6. Modo demo

Para capturas de pantalla o enseñar el tema sin datos reales: crea un fichero vacío llamado `demo`.

```
touch ~/.config/neongrid/demo     # activar
rm ~/.config/neongrid/demo        # desactivar
```

---

## 7. Instalar, quitar, desinstalar

| Acción | Cómo |
|---|---|
| Instalar | `./instalar.sh` (o doble clic en *Instalar NeonGrid*). Guarda una copia de tus ajustes antes |
| Quitar (volver a como estaba) | `~/.local/share/neongrid/revertir.sh` |
| Desinstalar del todo | `~/.local/share/neongrid/desinstalar.sh` (pregunta si borra también tu agenda y consejos) |

Al instalar, NeonGrid **desactiva los elementos visuales de otros temas** (por ejemplo, los widgets del HUD de PixelZen) para que no se mezclen. No los desinstala; *Quitar NeonGrid* los restaura.

---

## 8. Problemas típicos

| Síntoma | Causa y arreglo |
|---|---|
| Un cartel dice "sin configurar" | Es normal si no tienes esa cosa (VPN, Syncthing, batería…). Si quieres ocultarlo: `false` en `config.json` |
| REPOS dice "sin repositorios" | Mira la sección 2: ruta mal escrita o sin `.git` |
| Cambié un fichero y no se nota | Espera: `config.json` hasta 1 min, `repos.txt` hasta 30 s, `agenda.txt` unos segundos |
| El amanecer sale unos minutos desviado | Pon tu `ciudad` en `config.json` |
| La animación va a tirones o gasta batería | Activa `"calma": true`. NeonGrid ya baja la calidad solo si el equipo no da más |
| Quiero ver cómo queda a otra hora | Es una opción de depuración (`HoraSimulada`); no tiene botón en la interfaz |
