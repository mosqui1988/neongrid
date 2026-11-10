/*
    NeonGrid · fondo animado para Plasma 6 (org.neongrid.wallpaper)

    Escena: dos ShaderEffect.
      1) escena.frag a resolucion LOGICA (960x600 o 960x540): ventanas, coches, tren, voladores, balizas,
         lluvia y fundido entre modos, con oclusion por profundidad (geo.png). Se renderiza a una textura.
      2) pixel.frag escala esa textura por un factor ENTERO (vecino mas cercano) y anade la rejilla LED.
    Encima, QML dibuja el texto vivo de los carteles (Departure Mono) en las posiciones de layout.js.
    Un unico Timer: 8 fps (o menos segun la calidad); en pausa baja a 1 Hz (reloj y datos).
    Datos: org.kde.plasma.plasma5support DataSource, motor "executable", que lanza
    fuentes/ejecutar-todas.py (un JSON con todas las fuentes) cada IntervaloDatos segundos.
*/
import QtQuick
import org.kde.plasma.plasmoid
import org.kde.plasma.plasma5support as P5Support
import "logica.js" as LG
import "layout.js" as LY

WallpaperItem {
    id: root

    // ------------------------------------------------------------------ configuracion efectiva
    readonly property var c: root.configuration
    property var cfgJson: ({})
    property bool demoFichero: false
    property var i18nEs: null
    property var i18nEn: null
    readonly property bool calma: (c && c.Calma === true) || cfgJson.calma === true
    readonly property bool demo: (c && c.Demo === true) || demoFichero
    readonly property string idioma: {
        var v = c && c.Idioma ? String(c.Idioma) : "auto"
        if (v === "auto" && cfgJson.idioma && cfgJson.idioma !== "auto") v = cfgJson.idioma
        if (v === "auto") v = Qt.locale().name.indexOf("es") === 0 ? "es" : "en"
        return v === "en" ? "en" : "es"
    }
    readonly property var tabla: idioma === "en" ? i18nEn : i18nEs
    function t(k) { return LG.texto(tabla, idioma, k) }
    readonly property var ocultos: {
        var o = {}
        var s = c && c.Carteles ? String(c.Carteles) : ""
        if (s.length) s.split(",").forEach(function (k) { o[k.trim()] = true })
        else if (cfgJson.carteles) for (var k in cfgJson.carteles) if (cfgJson.carteles[k] === false) o[k] = true
        return o
    }
    function mostrar(k) { return !ocultos[k] }
    readonly property var ciudad: {
        var s = c && c.Ciudad ? String(c.Ciudad) : ""
        var p = s.split(",")
        if (p.length === 2 && !isNaN(parseFloat(p[0])) && !isNaN(parseFloat(p[1]))) return { lat: parseFloat(p[0]), lon: parseFloat(p[1]) }
        if (cfgJson.ciudad && cfgJson.ciudad.lat !== undefined) return { lat: Number(cfgJson.ciudad.lat), lon: Number(cfgJson.ciudad.lon) }
        // sin ciudad: zona horaria del sistema (longitud ~ desfase * 15), latitud 40 N. Nunca red.
        return { lat: 40, lon: -new Date().getTimezoneOffset() / 60 * 15 }
    }
    readonly property int calidadCfg: c && c.Calidad !== undefined ? Number(c.Calidad) : -1
    readonly property int intervaloDatos: Math.max(1, c && c.IntervaloDatos ? Number(c.IntervaloDatos) : 2)
    readonly property real horaSim: c && c.HoraSimulada !== undefined ? Number(c.HoraSimulada) : -1

    // ------------------------------------------------------------------ fuente de los carteles
    FontLoader { id: fuenteDep; source: "../../../../../fonts/neongrid/DepartureMono-Regular.otf" }
    readonly property string familia: fuenteDep.status === FontLoader.Ready ? fuenteDep.font.family
                                      : (Qt.fontFamilies().indexOf("Departure Mono") >= 0 ? "Departure Mono" : "monospace")
    readonly property real ajusteFuente: familia === "monospace" ? -2 : -3     // linea de mayusculas: 3 px bajo el borde superior

    // ------------------------------------------------------------------ estado de animacion
    property int fotograma: 0
    // el zepelin flota: vaivén vertical (12 s) y deriva horizontal (24 s), en pixeles logicos enteros. Ambos periodos
    // dividen el bucle de 768 fotogramas. En modo calma la amplitud baja a 1 px.
    readonly property int flotaY: Math.round((calma ? 1 : 2) * Math.sin(2 * Math.PI * fotograma / 96))
    readonly property int flotaX: Math.round(Math.sin(2 * Math.PI * fotograma / 192 + 1))
    property int calidadAuto: 2
    readonly property int calidad: calidadCfg >= 0 ? calidadCfg : calidadAuto
    property bool bloqueada: false
    readonly property bool bateriaBaja: !!(datos && datos.bateria && datos.bateria.estado !== "neutro" && datos.bateria.pct !== null
                                           && datos.bateria.pct < 15 && datos.bateria.cargando === false)
    readonly property bool animando: root.visible && !bloqueada && !bateriaBaja && calidad > 0
    readonly property int fps: calidad >= 2 ? 8 : 6

    // reloj
    property string hhmm: "00:00"
    property bool dosPuntos: true
    property int segundo: 0
    property string diaSemana: ""
    property string fechaCorta: ""

    // sol y modo
    property int modoA: 0
    property int modoB: 0
    property real mezcla: 0
    property real noche: 1
    property vector4d astroSol: Qt.vector4d(0, 0, 0, 0)      // sol y luna en el cielo (ver logica.js: astros)
    property vector4d astroLuna: Qt.vector4d(0, 0, 0, 0)
    property real faseLuna: 0
    readonly property int modoDominante: mezcla < 0.5 ? modoA : modoB
    readonly property string nombreModo: LG.NOMBRES[modoDominante]
    readonly property var paleta: LY.L.paletas[nombreModo]

    function fechaEfectiva() {
        var d = new Date()
        if (horaSim >= 0) d.setHours(Math.floor(horaSim), Math.round(horaSim % 1 * 60), 0, 0)
        return d
    }
    function actualizaSol() {
        var s = LG.sol(fechaEfectiva(), ciudad.lat, ciudad.lon)
        var m = LG.modoPorSol(s.e, s.manana)
        modoA = m.a; modoB = m.b; mezcla = m.mezcla; noche = m.noche
        var a = LG.astros(fechaEfectiva(), ciudad.lat, ciudad.lon)
        astroSol = Qt.vector4d(a.sol[0], a.sol[1], a.sol[2], a.sol[3])
        astroLuna = Qt.vector4d(a.luna[0], a.luna[1], a.luna[2], a.luna[3]); faseLuna = a.fase
    }
    function actualizaReloj() {
        var d = fechaEfectiva()
        function dd(n) { return (n < 10 ? "0" : "") + n }
        hhmm = dd(d.getHours()) + ":" + dd(d.getMinutes())
        segundo = d.getSeconds()
        dosPuntos = calma || segundo % 2 === 0
        var dias = t("fecha.dias_abrev"), meses = t("fecha.meses_abrev")
        diaSemana = dias[(d.getDay() + 6) % 7] || ""
        fechaCorta = dd(d.getDate()) + " " + (meses[d.getMonth()] || "")
    }
    onHoraSimChanged: { actualizaSol(); actualizaReloj() }
    onCiudadChanged: actualizaSol()
    onIdiomaChanged: actualizaReloj()

    // ------------------------------------------------------------------ datos
    property var datos: ({})
    property var histCpu: []
    property var histRed: []
    property real maxRed: 1000
    property bool esperandoDatos: false
    property real ultimoDatos: 0
    readonly property string rutaFuentes: "$HOME/.local/share/neongrid/fuentes/ejecutar-todas.py"
    readonly property string cmdDatos: (c && c.ComandoDatos ? String(c.ComandoDatos) : "python3 \"" + rutaFuentes + "\"") + (demo ? " --demo" : "")
    readonly property string cmdConfig: "cat \"$HOME/.config/neongrid/config.json\" 2>/dev/null; echo; echo @@NG@@; "
        + "test -e \"$HOME/.config/neongrid/demo\" && echo 1 || echo 0; echo @@NG@@; "
        + "cat \"$HOME/.local/share/neongrid/i18n/es.json\" 2>/dev/null; echo; echo @@NG@@; "
        + "cat \"$HOME/.local/share/neongrid/i18n/en.json\" 2>/dev/null"
    readonly property string cmdBloqueo: "busctl --user call org.freedesktop.ScreenSaver /ScreenSaver org.freedesktop.ScreenSaver GetActive 2>/dev/null"
        + " || qdbus6 org.freedesktop.ScreenSaver /ScreenSaver org.freedesktop.ScreenSaver.GetActive 2>/dev/null"

    function lanza(cmd) { ejecutor.connectSource(cmd) }
    function recibeDatos(d) {
        esperandoDatos = false
        var j = null
        try { if (d["exit code"] === 0 && d.stdout) j = JSON.parse(d.stdout) } catch (e) { j = null }
        if (!j || typeof j !== "object") j = demo ? LG.demo(Date.now()) : {}
        aplicaDatos(j)
    }
    function aplicaDatos(j) {
        datos = j
        var tot = j.cpu && j.cpu.total !== null && j.cpu.total !== undefined ? j.cpu.total / 100 : null
        if (tot !== null) { var h = histCpu.slice(-47); h.push(tot); histCpu = h }
        if (j.red && j.red.bajada_kbps !== null && j.red.bajada_kbps !== undefined && j.red.estado !== "neutro") {
            var dn = j.red.bajada_kbps || 0, upk = j.red.subida_kbps || 0
            maxRed = Math.max(1000, maxRed * 0.98, dn, upk)
            var r = histRed.slice(-35); r.push([dn / maxRed, upk / maxRed]); histRed = r
        }
    }
    function recibeConfig(d) {
        var partes = String(d.stdout || "").split("@@NG@@")
        try { var cj = JSON.parse((partes[0] || "").trim() || "{}"); cfgJson = cj && typeof cj === "object" ? cj : {} } catch (e) { cfgJson = {} }
        demoFichero = (partes[1] || "").trim() === "1"
        try { i18nEs = JSON.parse((partes[2] || "").trim()) } catch (e) { i18nEs = null }
        try { i18nEn = JSON.parse((partes[3] || "").trim()) } catch (e) { i18nEn = null }
        actualizaReloj()
    }

    P5Support.DataSource {
        id: ejecutor
        engine: "executable"
        connectedSources: []
        onNewData: function (fuente, d) {
            disconnectSource(fuente)
            if (fuente === root.cmdDatos) root.recibeDatos(d)
            else if (fuente === root.cmdConfig) root.recibeConfig(d)
            else if (fuente === root.cmdBloqueo) root.bloqueada = String(d.stdout || "").indexOf("true") >= 0
        }
    }

    // estados derivados para carteles
    readonly property bool alerta: !!(datos && ((datos.cpu && datos.cpu.temp_c >= 90) || (datos.servicios && datos.servicios.fallidos > 0)))
    readonly property string motivoAlerta: datos && datos.cpu && datos.cpu.temp_c >= 90 ? t("cartel.alerta_temp") : t("cartel.alerta_servicio")
    readonly property string consejosTexto: {
        var l = datos && datos.consejos && datos.consejos.lista && datos.consejos.lista.length ? datos.consejos.lista : t("consejos.defecto")
        if (!l || !l.length) return ""
        var i = Math.floor(Date.now() / 600000) % l.length     // rota cada 10 min: 3 consejos seguidos
        var s = []
        for (var k = 0; k < Math.min(3, l.length); k++) s.push(String(l[(i + k) % l.length]).toUpperCase())
        return s.join("  +  ")
    }
    function etiquetaDron(dato) {
        if (!dato) return null
        var d = datos ? datos[dato] : null
        if (dato === "actualizaciones") {
            if (!d || d.estado === "neutro" || d.pendientes === null || d.pendientes === undefined) return { texto: "UPD --", rampa: "mist", glifo: "" }
            return d.pendientes > 0 ? { texto: "UPD " + d.pendientes, rampa: "amb", glifo: "tri" } : { texto: "UPD", rampa: "grn", glifo: "ok" }
        }
        if (dato === "servicios") {
            if (!d || d.estado === "neutro") return { texto: "SRV --", rampa: "mist", glifo: "" }
            return d.fallidos > 0 ? { texto: "SRV " + d.fallidos, rampa: "red", glifo: "no" } : { texto: "SRV", rampa: "grn", glifo: "ok" }
        }
        if (dato === "sync") {
            if (!d || d.estado === "neutro") return { texto: "SYNC --", rampa: "mist", glifo: "" }
            if (d.estado_sync === "sincronizando") return { texto: "SYNC", rampa: "amb", glifo: "sync" }
            if (d.estado_sync === "desconectado") return { texto: "SYNC", rampa: "red", glifo: "no" }
            return { texto: "SYNC", rampa: "grn", glifo: "ok" }
        }
        return null
    }
    readonly property real sincro: {    // rampa de la baliza de la torre (antena = Syncthing)
        var d = datos ? datos.sync : null
        if (!d || d.estado === "neutro") return 4
        if (d.estado_sync === "sincronizando") return 28
        if (d.estado_sync === "desconectado") return 32
        return 36
    }

    // ------------------------------------------------------------------ calidad automatica (fps medidos)
    property int cuadros: 0
    property int ticks: 0
    property int avance: 0          // fotogramas animados desde el inicio (no se reinicia; lo usa el texto del zepelin)
    property int malos: 0
    property int buenos: 0
    Connections {
        target: root.Window.window
        ignoreUnknownSignals: true
        function onFrameSwapped() { root.cuadros++ }
    }
    function evaluaCalidad() {      // cada 5 s
        if (!animando || calidadCfg >= 0) { cuadros = 0; ticks = 0; return }
        var ratio = ticks > 0 ? cuadros / ticks : 1
        if (ratio < 0.7) { malos++; buenos = 0 } else { buenos++; malos = 0 }
        if (malos >= 2 && calidadAuto > 1) { calidadAuto--; malos = 0 }
        if (buenos >= 24 && calidadAuto < 2) { calidadAuto++; buenos = 0 }    // reintenta tras 2 min estables
        cuadros = 0; ticks = 0
    }

    // ------------------------------------------------------------------ el UNICO temporizador
    property real ultimoTick: 0
    property int contador: 0
    Timer {
        id: reloj
        interval: root.animando ? Math.round(1000 / root.fps) : 1000
        running: true
        repeat: true
        onTriggered: {
            var ahora = Date.now()
            if (root.animando) { root.fotograma = (root.fotograma + 1) % 768; root.ticks++; root.avance = (root.avance + 1) % 1000000 }
            root.contador++
            var porSeg = root.animando ? root.fps : 1
            if (root.contador % Math.max(1, Math.round(porSeg / 2)) === 0) root.actualizaReloj()
            if (ahora - root.ultimoDatos >= root.intervaloDatos * 1000 - 50 && !root.esperandoDatos) {
                root.ultimoDatos = ahora; root.esperandoDatos = true; root.lanza(root.cmdDatos)
            } else if (root.esperandoDatos && ahora - root.ultimoDatos > 15000) {
                root.esperandoDatos = false; ejecutor.disconnectSource(root.cmdDatos)     // el script no responde
            }
            if (root.contador % (porSeg * 5) === 0) root.evaluaCalidad()
            if (root.contador % (porSeg * 10) === 0) root.lanza(root.cmdBloqueo)
            if (root.contador % (porSeg * 30) === 0) root.actualizaSol()
            if (root.contador % (porSeg * 60) === 0) root.lanza(root.cmdConfig)
        }
    }
    Component.onCompleted: { actualizaSol(); actualizaReloj(); lanza(cmdConfig); if (demo) aplicaDatos(LG.demo(Date.now())) }

    // ------------------------------------------------------------------ escena
    Rectangle { anchors.fill: parent; color: root.paleta ? root.paleta[0] : "#05060e" }
    Escena {
        id: escena
        anchors.fill: parent
        f: root
        escalaCfg: c && c.Escala ? Number(c.Escala) : 0
    }
}
