# Decoración de ventanas Aurorae «NeonGrid»

`python3 generar.py` escribe `paquete/neongrid/share/aurorae/themes/NeonGrid/` (`decoration.svg`, `close/maximize/restore/minimize/keepabove/keepbelow/alldesktops/shade/help.svg`, `NeonGridrc`, `metadata.desktop`). `python3 vista-previa.py` (Pillow) monta `vista-previa.png` con los SVG reales.

- Título de 28 px (2 borde + 24 + 2), bordes laterales/inferior de 4 px: 2 px de neón + 2 px de halo escalonado hacia dentro (cian 35 % y 15 %). Activa = cian, inactiva = violeta apagado sin halo.
- Esquinas biseladas a 45° (4 px) y «corchetes» como tramos brillantes verticales de 14 px junto a las esquinas superiores y píxeles brillantes en el chaflán. Líneas de escaneo ~9 % solo en el título.
- Botones de 20x20 con rejilla lógica de 2 px: `—` `□` `✕` y variantes con forma propia (▲ ▼ ◇ ? y «enrollar»); cerrar en magenta; estados `active`, `hover` (caja biselada), `pressed` (caja llena), `inactive`, `deactivated`, `hover-inactive`, `pressed-inactive`.
- Transparencia: solo la del SVG (relleno al 94-96 %); lo que se ve dentro de la ventana lo decide la aplicación.
- La tipografía del título es la de «Barra de título» del sistema (Aurorae no la fija): usar Chakra Petch SemiBold 10 pt en Preferencias > Fuentes.
- `kpackagetool6 --type KWin/Aurorae` rechaza también el PixelZen que ya funciona, así que no sirve como validador de este tipo; Aurorae lee la carpeta directamente.
