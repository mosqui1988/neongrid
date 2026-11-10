// NeonGrid - disposicion de la barra superior (script de Plasma Shell, Plasma 6).
// Orden: nucleo (lanzador) | escritorios (rombos) | tareas solo iconos | <espaciador> | reloj | <espaciador> | bandeja | apagado
// Se ejecuta con:  qdbus6 org.kde.plasmashell /PlasmaShell org.kde.PlasmaShell.evaluateScript "$(cat aplicar-panel.js)"
// (o pegado en la consola de Plasma, Alt+F2 -> "plasma-interactive-console"). NO reinicia plasmashell.
// El instalador sustituye __NUCLEO__ por la ruta absoluta del icono y __LANZADORES__ por los lanzadores a fijar
// (vacio = no tocar los actuales). Sin sustituir, se usan valores por defecto razonables.

var NUCLEO = "__NUCLEO__";
if (NUCLEO.indexOf("__") === 0) {
    NUCLEO = userDataPath() + "/.local/share/plasma/desktoptheme/NeonGrid/icons/nucleo-22.svg";
}
var LANZADORES = "__LANZADORES__";

// Reutiliza el primer panel o crea uno nuevo (no se toca el resto de paneles).
var p = panels().length > 0 ? panels()[0] : new Panel;
p.location = "top";
p.height = 32;
p.lengthMode = "fill";      // ancho completo
p.alignment = "center";
p.floating = false;         // pegada al borde
p.hiding = "none";
p.opacity = "adaptive";

// Vacia la barra y la rellena en el orden pedido.
var ids = p.widgetIds;
for (var i = 0; i < ids.length; i++) { p.widgetById(ids[i]).remove(); }

// 1) Lanzador: hexagono "nucleo" >_
var k = p.addWidget("org.kde.plasma.kickoff");
k.currentConfigGroup = ["General"];
k.writeConfig("icon", NUCLEO);

// 2) Escritorios virtuales (rombos; el activo va relleno de cian). Cuantos hay lo decide KWin (instalar.sh pone 4).
var pg = p.addWidget("org.kde.plasma.pager");
pg.currentConfigGroup = ["General"];
pg.writeConfig("displayedText", 2);          // 2 = sin texto
pg.writeConfig("showWindowIcons", false);
pg.writeConfig("pagerLayout", 1);            // 1 = horizontal

// 3) Administrador de tareas solo con iconos
var t = p.addWidget("org.kde.plasma.icontasks");
t.currentConfigGroup = ["General"];
if (LANZADORES.indexOf("__") !== 0 && LANZADORES !== "") { t.writeConfig("launchers", LANZADORES); }
t.writeConfig("groupingStrategy", 0);
t.writeConfig("showToolTips", true);
t.writeConfig("indicateAudioStreams", true);
t.writeConfig("maxStripes", 1);

// 4) Espaciador - reloj centrado - espaciador
p.addWidget("org.kde.plasma.panelspacer");
var c = p.addWidget("org.kde.plasma.digitalclock");
c.currentConfigGroup = ["Appearance"];
c.writeConfig("showDate", true);
c.writeConfig("dateFormat", "custom");
c.writeConfig("customDateFormat", "'·' ddd d MMM");   // "21:37 · mar 10 nov"  (Qt: ddd = dia abreviado)
c.writeConfig("dateDisplayFormat", "BesideTime");
c.writeConfig("use24hFormat", 2);                          // siempre 24 h
c.writeConfig("showSeconds", 0);
p.addWidget("org.kde.plasma.panelspacer");

// 5) Bandeja: red (incluye VPN), volumen, bateria (se oculta sola sin bateria), Bluetooth.
//    El resto va al menu desplegable. Sincronizacion (Syncthing) aparece si hay un applet de bandeja instalado.
var s = p.addWidget("org.kde.plasma.systemtray");
s.currentConfigGroup = ["General"];
var visibles = "org.kde.plasma.networkmanagement,org.kde.plasma.volume,org.kde.plasma.battery,org.kde.plasma.bluetooth";
var ocultos = "org.kde.plasma.notifications,org.kde.plasma.clipboard,org.kde.plasma.devicenotifier,org.kde.plasma.brightness,org.kde.kdeconnect,org.kde.plasma.mediacontroller,org.kde.kscreen,org.kde.plasma.keyboardlayout";
s.writeConfig("extraItems", visibles + "," + ocultos);
s.writeConfig("shownItems", visibles);
s.writeConfig("hiddenItems", ocultos);

// 6) Apagado: ultimo a la derecha (bloquear / cerrar sesion / apagar)
var pw = p.addWidget("org.kde.plasma.lock_logout");
pw.currentConfigGroup = ["General"];
pw.writeConfig("show_requestShutDown", true);
pw.writeConfig("show_lockScreen", false);

print("NeonGrid: barra " + p.location + " h=" + p.height + " widgets=" + p.widgetIds.length);
