// NeonGrid · logica del fondo sin dependencias de QML (sol, modos, datos de demo, textos, formato).
.pragma library

// ------------------------------------------------------------------ sol (mismo calculo que PixelZen)
function sol(fecha, lat, lon) {
    var rad = Math.PI / 180
    var n = fecha.getTime() / 86400000 + 2440587.5 - 2451545.0
    var L = (280.460 + 0.9856474 * n) % 360
    var g = ((357.528 + 0.9856003 * n) % 360) * rad
    var lam = (L + 1.915 * Math.sin(g) + 0.020 * Math.sin(2 * g)) * rad
    var eps = (23.439 - 0.0000004 * n) * rad
    var ra = Math.atan2(Math.cos(eps) * Math.sin(lam), Math.cos(lam))
    var dec = Math.asin(Math.sin(eps) * Math.sin(lam))
    var gmst = (18.697374558 + 24.06570982441908 * n) % 24
    var H = (gmst * 15 + lon) * rad - ra
    H = Math.atan2(Math.sin(H), Math.cos(H))
    var phi = lat * rad
    var e = Math.asin(Math.sin(phi) * Math.sin(dec) + Math.cos(phi) * Math.cos(dec) * Math.cos(H))
    return { e: e / rad, manana: H < 0, H: H, dec: dec }
}

// ------------------------------------------------------------------ sol y luna en el cielo (pixeles del lienzo 960x600)
// El sol sale por la izquierda (x = 300, donde esta el resplandor del amanecer), cruza el cielo y se pone por la
// derecha (x = 600; mas alla los edificios tapan el horizonte). La luna hace el mismo camino de noche: sale al anochecer y se pone al amanecer. Su FASE es la
// real (calculada de la fecha); su hora de salida es simplificada (siempre opuesta al sol). El horizonte es HY = 108:
// por debajo, los astros quedan tras la ciudad y el shader no los pinta.
var HORIZ = 108, X_SALE = 300, X_PONE = 600
function _yAstro(e) { return HORIZ + 1 - Math.max(-14, Math.min(34, e)) * 2.4 }   // tope y = 27: por encima del zepelin
function astros(fecha, lat, lon) {
    var rad = Math.PI / 180
    var s = sol(fecha, lat, lon)
    var cosH0 = Math.max(-1, Math.min(1, -Math.tan(lat * rad) * Math.tan(s.dec)))
    var H0 = Math.max(0.05, Math.min(Math.PI - 0.05, Math.acos(cosH0)))        // medio arco diurno
    var prog = (s.H + H0) / (2 * H0)                                           // 0 sale .. 1 se pone
    var t = s.H - H0; if (t < 0) t += 2 * Math.PI                               // desde la puesta
    var progL = t / (2 * Math.PI - 2 * H0)                                     // 0 sale la luna .. 1 se pone
    var jd = fecha.getTime() / 86400000 + 2440587.5
    var fase = (((jd - 2451550.26) / 29.530588) % 1 + 1) % 1 * 2 * Math.PI     // 0 nueva, pi llena
    fase = Math.max(0.8, Math.min(2 * Math.PI - 0.8, fase))                    // nunca 100 % nueva: minimo un creciente fino
    function x(p) { return X_SALE + (X_PONE - X_SALE) * Math.max(-0.3, Math.min(1.3, p)) }
    return {
        sol: [x(prog), _yAstro(s.e), 8, s.e > -16 ? 1 : 0],
        luna: [x(progL), _yAstro(-s.e), 8, -s.e > -16 ? 1 : 0],
        fase: fase
    }
}

// modos: 0 noche, 1 dia, 2 amanecer, 3 atardecer (fila de paleta en atlas.png)
var NOMBRES = ["noche", "dia", "amanecer", "atardecer"]
function suave(t) { t = Math.max(0, Math.min(1, t)); return t * t * (3 - 2 * t) }
// devuelve {a, b, mezcla (0..1 hacia b), noche (0..1)}
function modoPorSol(e, manana) {
    var calido = manana ? 2 : 3
    var r
    if (e >= 8) r = { a: 1, b: 1, mezcla: 0 }
    else if (e <= -10) r = { a: 0, b: 0, mezcla: 0 }
    else if (e < -4) r = { a: 0, b: calido, mezcla: suave((e + 10) / 6) }
    else if (e <= 2) r = { a: calido, b: calido, mezcla: 0 }
    else r = { a: calido, b: 1, mezcla: suave((e - 2) / 6) }
    r.noche = Math.max(0, Math.min(1, (1 - e) / 7))
    return r
}
var BRUMA = [[40, 54, 82], [118, 132, 152], [168, 128, 158], [186, 98, 88]]


// ------------------------------------------------------------------ matriz LED 5x7 para el texto del zepelin
// Cada caracter = 5 columnas + 1 de separacion; cada columna es un entero de 7 bits (bit 0 = fila de arriba).
// Los acentos se quitan (A, N...); lo que no esta en la tabla se muestra como espacio.
var LED_ANCHO = {
    "A": [14, 17, 17, 31, 17, 17, 17], "B": [30, 17, 17, 30, 17, 17, 30], "C": [14, 17, 16, 16, 16, 17, 14], "D": [28, 18, 17, 17, 17, 18, 28],
    "E": [31, 16, 16, 30, 16, 16, 31], "F": [31, 16, 16, 30, 16, 16, 16], "G": [14, 17, 16, 23, 17, 17, 15], "H": [17, 17, 17, 31, 17, 17, 17],
    "I": [14, 4, 4, 4, 4, 4, 14], "J": [7, 2, 2, 2, 2, 18, 12], "K": [17, 18, 20, 24, 20, 18, 17], "L": [16, 16, 16, 16, 16, 16, 31],
    "M": [17, 27, 21, 21, 17, 17, 17], "N": [17, 17, 25, 21, 19, 17, 17], "O": [14, 17, 17, 17, 17, 17, 14], "P": [30, 17, 17, 30, 16, 16, 16],
    "Q": [14, 17, 17, 17, 21, 18, 13], "R": [30, 17, 17, 30, 20, 18, 17], "S": [15, 16, 16, 14, 1, 1, 30], "T": [31, 4, 4, 4, 4, 4, 4],
    "U": [17, 17, 17, 17, 17, 17, 14], "V": [17, 17, 17, 17, 17, 10, 4], "W": [17, 17, 17, 21, 21, 21, 10], "X": [17, 17, 10, 4, 10, 17, 17],
    "Y": [17, 17, 10, 4, 4, 4, 4], "Z": [31, 1, 2, 4, 8, 16, 31],
    "0": [14, 17, 19, 21, 25, 17, 14], "1": [4, 12, 4, 4, 4, 4, 14], "2": [14, 17, 1, 2, 4, 8, 31], "3": [31, 2, 4, 2, 1, 17, 14],
    "4": [2, 6, 10, 18, 31, 2, 2], "5": [31, 16, 30, 1, 1, 17, 14], "6": [6, 8, 16, 30, 17, 17, 14], "7": [31, 1, 2, 4, 8, 8, 8],
    "8": [14, 17, 17, 14, 17, 17, 14], "9": [14, 17, 17, 15, 1, 2, 12],
    ".": [0, 0, 0, 0, 0, 12, 12], ",": [0, 0, 0, 0, 12, 4, 8], ":": [0, 12, 12, 0, 12, 12, 0], ";": [0, 12, 12, 0, 12, 4, 8],
    "!": [4, 4, 4, 4, 4, 0, 4], "?": [14, 17, 1, 2, 4, 0, 4], "-": [0, 0, 0, 31, 0, 0, 0], "+": [0, 4, 4, 31, 4, 4, 0],
    "=": [0, 0, 31, 0, 31, 0, 0], "_": [0, 0, 0, 0, 0, 0, 31], "/": [1, 1, 2, 4, 8, 16, 16], "%": [24, 25, 2, 4, 8, 19, 3],
    ">": [8, 4, 2, 1, 2, 4, 8], "<": [2, 4, 8, 16, 8, 4, 2], "(": [2, 4, 8, 8, 8, 4, 2], ")": [8, 4, 2, 2, 2, 4, 8],
    "'": [4, 4, 8, 0, 0, 0, 0], "\"": [10, 10, 0, 0, 0, 0, 0], "#": [10, 10, 31, 10, 31, 10, 10], "*": [0, 21, 14, 31, 14, 21, 0],
    "@": [14, 17, 23, 21, 23, 16, 14], "\u00bf": [4, 0, 4, 8, 16, 17, 14], "\u00a1": [4, 0, 4, 4, 4, 4, 4]
}
// devuelve un array de columnas (enteros de 7 bits, bit 0 = fila superior)
function matrizLed(texto) {
    var t = String(texto).toUpperCase()
    if (t.normalize) t = t.normalize("NFD").replace(/[\u0300-\u036f]/g, "")
    var cols = []
    for (var n = 0; n < t.length; n++) {
        var ch = t.charAt(n)
        if (ch === " ") { cols.push(0, 0, 0); continue }
        var g = LED_ANCHO[ch]
        if (!g) { cols.push(0, 0, 0); continue }
        for (var c = 0; c < 5; c++) {
            var v = 0
            for (var r = 0; r < 7; r++) if ((g[r] >> (4 - c)) & 1) v |= (1 << r)
            cols.push(v)
        }
        cols.push(0)
    }
    return cols
}

// ------------------------------------------------------------------ fuente LED 5x7 del reloj (filas de 5 bits)
var LED57 = {
    "0": [14, 17, 19, 21, 25, 17, 14], "1": [4, 12, 4, 4, 4, 4, 14], "2": [14, 17, 1, 2, 4, 8, 31],
    "3": [31, 2, 4, 2, 1, 17, 14], "4": [2, 6, 10, 18, 31, 2, 2], "5": [31, 16, 30, 1, 1, 17, 14],
    "6": [6, 8, 16, 30, 17, 17, 14], "7": [31, 1, 2, 4, 8, 8, 8], "8": [14, 17, 17, 14, 17, 17, 14],
    "9": [14, 17, 17, 15, 1, 2, 12], ":": [0, 12, 12, 0, 12, 12, 0], " ": [0, 0, 0, 0, 0, 0, 0]
}
// puntos encendidos de "HH:MM" en coordenadas del cartel (x, y)
function puntosReloj(hhmm, conDosPuntos, origen, desp) {
    var out = []
    for (var ci = 0; ci < 5; ci++) {
        var ch = hhmm[ci]
        if (ci === 2 && !conDosPuntos) continue
        var rows = LED57[ch] || LED57[" "]
        var lo = ci === 2 ? 1 : 0, hi = ci === 2 ? 3 : 5
        for (var j = 0; j < 7; j++)
            for (var i = lo; i < hi; i++)
                if ((rows[j] >> (4 - i)) & 1) out.push([origen[0] + desp[ci] + (i - lo) * 3, origen[1] + j * 3])
    }
    return out
}

// glifos propios (x = pixel); Departure Mono no trae ✔ ni ✖
var GL = {
    ok: [".....x", "....xx", "x..xx.", "xxxx..", ".xx..."],
    no: ["x...x", ".x.x.", "..x..", ".x.x.", "x...x"],
    tri: ["..x..", ".xxx.", "xxxxx"],
    neu: ["....", "xxxx", "...."],
    sync: [".xxx.", "x...x", "x.x.x", "x...x", ".xxx."],
    escudo: ["xxxxxxxxx", "x.......x", "x.......x", "x.......x", "x.......x", "x.......x", "x.......x", ".x.....x.", ".x.....x.", "..x...x..", "...x.x...", "....x...."]
}
function pixeles(nombre) {
    var g = GL[nombre] || [], out = []
    for (var j = 0; j < g.length; j++)
        for (var i = 0; i < g[j].length; i++)
            if (g[j][i] === "x") out.push([i, j])
    return out
}

// ------------------------------------------------------------------ paleta (indices de atlas.png, rampas de 4 tonos)
var RAMPA = { ink: 0, slate: 4, mist: 8, glass: 12, cyan: 16, mag: 20, vio: 24, amb: 28, red: 32, grn: 36, wht: 40 }
function color(paleta, rampa, tono) {
    var i = RAMPA[rampa] + tono
    return paleta && paleta[i] ? paleta[i] : "#e6f1ff"
}
function rampaCarga(v) { return v < 0.6 ? "grn" : (v < 0.85 ? "amb" : "red") }

// ------------------------------------------------------------------ textos (respaldo si faltan i18n/*.json)
var BASE = {
    es: {
        "etiqueta.alerta": "ALERTA", "etiqueta.repos": "REPOS", "etiqueta.demo": "DEMO",
        "estado.no_configurado": "no configurado", "estado.activa": "activa", "estado.inactiva": "inactiva",
        "estado.sin_conexion": "sin conexión", "estado.al_dia": "al día", "estado.sincronizando": "sincronizando",
        "estado.desconectado": "desconectado", "estado.sin_dato": "sin dato", "estado.neutro": "sin datos",
        "estado.cargando": "cargando",
        "cartel.sin_agenda": "sin agenda hoy", "cartel.sin_bateria": "sin batería", "cartel.enchufado": "enchufado",
        "cartel.alerta_temp": "temperatura crítica", "cartel.alerta_servicio": "servicio caído",
        "cartel.sin_cambios": "todo guardado",
        "fecha.dias_abrev": ["lun", "mar", "mié", "jue", "vie", "sáb", "dom"],
        "fecha.meses_abrev": ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"],
        "consejos.defecto": ["Haz commit a menudo", "Haz copia de seguridad", "Descansa la vista"]
    },
    en: {
        "etiqueta.alerta": "ALERT", "etiqueta.repos": "REPOS", "etiqueta.demo": "DEMO",
        "estado.no_configurado": "not configured", "estado.activa": "active", "estado.inactiva": "inactive",
        "estado.sin_conexion": "offline", "estado.al_dia": "up to date", "estado.sincronizando": "syncing",
        "estado.desconectado": "disconnected", "estado.sin_dato": "no data", "estado.neutro": "no data",
        "estado.cargando": "charging",
        "cartel.sin_agenda": "nothing scheduled today", "cartel.sin_bateria": "no battery", "cartel.enchufado": "plugged in",
        "cartel.alerta_temp": "critical temperature", "cartel.alerta_servicio": "service down",
        "cartel.sin_cambios": "all saved",
        "fecha.dias_abrev": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
        "fecha.meses_abrev": ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
        "consejos.defecto": ["Commit often", "Back up your files", "Rest your eyes"]
    }
}
function texto(tabla, idioma, clave) {
    if (tabla && tabla[clave] !== undefined) return tabla[clave]
    var b = BASE[idioma] || BASE.es
    return b[clave] !== undefined ? b[clave] : clave
}

// ------------------------------------------------------------------ formato corto para carteles (Departure Mono, 7 px por caracter)
function red(kbps) {
    if (kbps === null || kbps === undefined || isNaN(kbps)) return "--"
    if (kbps >= 10000) return Math.round(kbps / 1000) + " Mb/s"
    if (kbps >= 1000) return (kbps / 1000).toFixed(1) + " Mb/s"
    return Math.round(kbps) + " kb/s"
}
function gb(mb) { return mb >= 10240 ? Math.round(mb / 1024) + "G" : (mb / 1024).toFixed(1) + "G" }
function num(v, d) { return v === null || v === undefined || isNaN(v) ? "--" : Number(v).toFixed(d || 0) }

// ------------------------------------------------------------------ datos de demostracion internos (--demo sin script)
// Mismo formato que fuentes/ejecutar-todas.py; estables aunque varien.
function demo(ms) {
    var t = ms / 1000, ts = Math.floor(t)
    function o(a, f, ph) { return Math.sin(t * f + ph) * a }
    var nuc = []
    for (var k = 0; k < 8; k++) nuc.push(Math.max(2, Math.min(99, 45 + o(35, 0.11 + k * 0.03, k) + o(10, 0.7, k * 2))))
    var tot = nuc.reduce(function (a, b) { return a + b }, 0) / nuc.length
    var dn = Math.max(0, 1800 + o(1500, 0.23, 1) + o(600, 1.3, 0)), up = Math.max(0, 300 + o(250, 0.31, 2))
    var ahora = new Date(ms), prox = new Date(ms + 47 * 60000)
    function hh(d) { return (d.getHours() < 10 ? "0" : "") + d.getHours() + ":" + (d.getMinutes() < 10 ? "0" : "") + d.getMinutes() }
    return {
        cpu: { id: "cpu", estado: "ok", total: tot, nucleos: nuc, freq_mhz: 3800 + Math.round(o(300, 0.2, 0)), temp_c: 52 + o(8, 0.05, 0), demo: true, ts: ts },
        ram: { id: "ram", estado: "ok", usada_mb: 7400 + Math.round(o(900, 0.03, 0)), total_mb: 16384, pct: 46 + o(5, 0.03, 0), demo: true, ts: ts },
        gpu: { id: "gpu", estado: "ok", pct: 30 + o(25, 0.09, 1), temp_c: 48 + o(6, 0.04, 2), nombre: "GPU demo", demo: true, ts: ts },
        disco: { id: "disco", estado: "ok", pct: 62.4, usado_gb: 319, total_gb: 512, demo: true, ts: ts },
        red: { id: "red", estado: "ok", bajada_kbps: dn, subida_kbps: up, iface: "demo0", conectada: true, ping_ms: null, demo: true, ts: ts },
        vpn: { id: "vpn", estado: "ok", activa: true, tipo: "wireguard", demo: true, ts: ts },
        sync: { id: "sync", estado: "ok", estado_sync: (ts % 60) < 12 ? "sincronizando" : "al_dia", demo: true, ts: ts },
        git: { id: "git", estado: "aviso", repos_con_cambios: 3, sin_subir: 1, total: 7, demo: true, ts: ts },
        bateria: { id: "bateria", estado: "ok", pct: 78, cargando: false, temp_c: 31, demo: true, ts: ts },
        actualizaciones: { id: "actualizaciones", estado: "aviso", pendientes: 12, demo: true, ts: ts },
        servicios: { id: "servicios", estado: "ok", fallidos: 0, lista: [], demo: true, ts: ts },
        agenda: { id: "agenda", estado: "ok", proximo: { hora: hh(prox), texto: "Bloque de estudio" }, restantes: 2, demo: true, ts: ts },
        consejos: { id: "consejos", estado: "ok", lista: [], demo: true, ts: ts },
        trafico: { id: "trafico", estado: "ok", nivel: Math.min(1, dn / 4000), demo: true, ts: ts },
        carga: { id: "carga", estado: "ok", loadavg1: 1.2, intensidad_lluvia: 0.6 + o(0.3, 0.02, 0), demo: true, ts: ts }
    }
}
