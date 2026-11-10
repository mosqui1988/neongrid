import QtQuick
import "logica.js" as LG
import "layout.js" as LY

// Texto y graficas vivas encima de los marcos pixel de la capa (posiciones de layout.js).
// Todo en pixeles logicos del lienzo (x u = unidades del item). Solo cambia cuando llegan datos
// (cada 2 s), cada segundo (reloj) o con el fotograma (marquesinas y drones, 8 fps).
Item {
    id: cs
    property var f                       // el WallpaperItem (datos, textos, estado)
    property real u: 1
    property real oy: 0
    readonly property var pal: f.paleta
    readonly property var d: f.datos
    readonly property string fam: f.familia
    readonly property int fr: f.fotograma
    readonly property real aj: f.ajusteFuente
    function col(r, k) { return LG.color(pal, r, k) }
    function geom(n) { return LY.L.carteles[n] }
    function tr(k) { return f.t(k) }
    function est(id) { return d && d[id] ? d[id].estado : "neutro" }
    function neutro(id) { return !d || !d[id] || d[id].estado === "neutro" }
    function up(s) { return (s || "").toString().toUpperCase() }

    // ================================================================== RELOJ + AGENDA
    Item {
        visible: cs.f.mostrar("hora")
        readonly property var g: cs.geom("reloj")
        readonly property var puntos: LG.puntosReloj(cs.f.hhmm, cs.f.dosPuntos, [LY.L.reloj_led.x, LY.L.reloj_led.y], LY.L.reloj_led.desplazamientos)
        Repeater {
            model: parent.puntos
            Item {
                Px { g: parent.parent.g; u: cs.u; oy: cs.oy; lx: modelData[0]; ly: modelData[1]; lw: 2; lh: 2; color: cs.col("cyan", 2) }
                Px { g: parent.parent.g; u: cs.u; oy: cs.oy; lx: modelData[0]; ly: modelData[1]; lw: 1; lh: 1; color: cs.col("cyan", 3) }
            }
        }
        Repeater {   // segundero: 28 puntos
            model: 28
            Px { g: parent.g; u: cs.u; oy: cs.oy; lx: 10 + index * 3; ly: 30; color: cs.col("cyan", 2); visible: index < Math.floor(cs.f.segundo * 28 / 60) }
        }
        Txt { g: parent.g; u: cs.u; oy: cs.oy; sx: 10; sy: 34; texto: cs.up(cs.f.diaSemana); color: cs.col("mag", 3); familia: cs.fam; ajusteY: cs.aj }
        Txt { g: parent.g; u: cs.u; oy: cs.oy; sx: 10 + 4 * 7; sy: 34; texto: cs.up(cs.f.fechaCorta); color: cs.col("cyan", 3); familia: cs.fam; ajusteY: cs.aj }
        // linea inferior: alerta > proxima cita > sin agenda
        readonly property var prox: cs.d && cs.d.agenda && cs.d.agenda.proximo ? cs.d.agenda.proximo : null
        Glifo { g: parent.g; u: cs.u; oy: cs.oy; sx: 8; sy: 46; nombre: "tri"; color: cs.col("red", 2); visible: cs.f.alerta }
        Txt { g: parent.g; u: cs.u; oy: cs.oy; sx: 15; sy: 45; max: 11; fotograma: cs.fr; visible: cs.f.alerta
              texto: cs.up(cs.tr("etiqueta.alerta") + ": " + cs.f.motivoAlerta); color: cs.col("red", 3); familia: cs.fam; ajusteY: cs.aj }
        Txt { g: parent.g; u: cs.u; oy: cs.oy; sx: 8; sy: 45; visible: !cs.f.alerta && parent.prox !== null
              texto: parent.prox ? parent.prox.hora : ""; color: cs.col("amb", 3); familia: cs.fam; ajusteY: cs.aj }
        Txt { g: parent.g; u: cs.u; oy: cs.oy; sx: 8 + 6 * 7; sy: 45; max: 6; fotograma: cs.fr; visible: !cs.f.alerta && parent.prox !== null
              texto: parent.prox ? cs.up(parent.prox.texto) : ""; color: cs.col("mist", 3); familia: cs.fam; ajusteY: cs.aj }
        Txt { g: parent.g; u: cs.u; oy: cs.oy; sx: 8; sy: 45; max: 12; fotograma: cs.fr; visible: !cs.f.alerta && parent.prox === null
              texto: cs.up(cs.neutro("agenda") ? cs.tr("estado.no_configurado") : cs.tr("cartel.sin_agenda")); color: cs.col("mist", 2); familia: cs.fam; ajusteY: cs.aj }
    }

    // ================================================================== CPU por nucleo
    Item {
        visible: cs.f.mostrar("cpu")
        readonly property var g: cs.geom("cpu")
        readonly property var c: cs.d && cs.d.cpu ? cs.d.cpu : null
        readonly property bool ok: c !== null && c.estado !== "neutro" && c.total !== null && c.total !== undefined
        readonly property var nuc: {
            if (!ok || !c.nucleos || !c.nucleos.length) return []
            var n = c.nucleos, out = []
            if (n.length <= 8) return n.map(function (v) { return v / 100 })
            for (var k = 0; k < 8; k++) {        // mas de 8 nucleos: 8 grupos (media)
                var a = Math.floor(k * n.length / 8), b = Math.floor((k + 1) * n.length / 8), s = 0
                for (var i = a; i < b; i++) s += n[i]
                out.push(s / Math.max(1, b - a) / 100)
            }
            return out
        }
        Txt { g: parent.g; u: cs.u; oy: cs.oy; sx: 7; sy: 10; visible: parent.ok && !!parent.c.freq_mhz
              texto: parent.ok && parent.c.freq_mhz ? (parent.c.freq_mhz / 1000).toFixed(1) + "G" : ""; color: cs.col("mist", 2); familia: cs.fam; ajusteY: cs.aj }
        Txt { g: parent.g; u: cs.u; oy: cs.oy; sx: 7 + 5 * 7; sy: 10; visible: parent.ok && parent.c.temp_c !== null && parent.c.temp_c !== undefined
              texto: parent.ok ? LG.num(parent.c.temp_c) + "°" : ""; color: parent.ok && parent.c.temp_c >= 85 ? cs.col("red", 3) : cs.col("amb", 3); familia: cs.fam; ajusteY: cs.aj }
        Txt { g: parent.g; u: cs.u; oy: cs.oy; sx: 101; sy: 10; derecha: true; visible: parent.ok
              texto: parent.ok ? Math.round(parent.c.total) + "%" : ""; color: cs.col("mag", 3); familia: cs.fam; ajusteY: cs.aj }
        Txt { g: parent.g; u: cs.u; oy: cs.oy; sx: 7; sy: 10; max: 13; fotograma: cs.fr; visible: !parent.ok
              texto: cs.up(cs.tr("estado.no_configurado")); color: cs.col("mist", 2); familia: cs.fam; ajusteY: cs.aj }
        Repeater {
            model: parent.nuc
            Item {
                readonly property real v: Math.max(0, Math.min(1, modelData))
                readonly property int hh: Math.max(1, Math.round(v * 16))
                Px { g: parent.parent.g; u: cs.u; oy: cs.oy; lx: 8 + index * 12; ly: 36 - parent.hh; lw: 8; lh: parent.hh; color: cs.col(LG.rampaCarga(parent.v), 1) }
                Px { g: parent.parent.g; u: cs.u; oy: cs.oy; lx: 8 + index * 12; ly: 36 - parent.hh; lw: 8; lh: 1; color: cs.col(LG.rampaCarga(parent.v), 3) }
            }
        }
        Repeater {
            model: cs.f.histCpu
            Item {
                readonly property real v: Math.max(0, Math.min(1, modelData))
                readonly property int hh: 1 + Math.floor(v * 4.99)
                Px { g: parent.parent.g; u: cs.u; oy: cs.oy; lx: 6 + index * 2; ly: 45 - parent.hh + 1; lw: 1; lh: parent.hh; color: cs.col(LG.rampaCarga(parent.v), 0) }
                Px { g: parent.parent.g; u: cs.u; oy: cs.oy; lx: 6 + index * 2; ly: 45 - parent.hh + 1; lw: 1; lh: 1; color: cs.col(LG.rampaCarga(parent.v), 2) }
            }
        }
    }

    // ================================================================== NET
    Item {
        visible: cs.f.mostrar("net")
        readonly property var g: cs.geom("net")
        readonly property var r: cs.d && cs.d.red ? cs.d.red : null
        readonly property bool ok: r !== null && r.estado !== "neutro" && r.conectada !== false
        Txt { g: parent.g; u: cs.u; oy: cs.oy; sx: 7; sy: 11; visible: parent.ok; texto: "↓"; color: cs.col("cyan", 3); familia: cs.fam; ajusteY: cs.aj }
        Txt { g: parent.g; u: cs.u; oy: cs.oy; sx: 16; sy: 11; visible: parent.ok; texto: parent.ok ? LG.red(parent.r.bajada_kbps) : ""; color: cs.col("cyan", 3); familia: cs.fam; ajusteY: cs.aj }
        Txt { g: parent.g; u: cs.u; oy: cs.oy; sx: 7; sy: 20; visible: parent.ok; texto: "↑"; color: cs.col("mag", 3); familia: cs.fam; ajusteY: cs.aj }
        Txt { g: parent.g; u: cs.u; oy: cs.oy; sx: 16; sy: 20; visible: parent.ok; texto: parent.ok ? LG.red(parent.r.subida_kbps) : ""; color: cs.col("mag", 3); familia: cs.fam; ajusteY: cs.aj }
        Glifo { g: parent.g; u: cs.u; oy: cs.oy; sx: 7; sy: 12; nombre: parent.r && parent.r.estado !== "neutro" ? "tri" : "neu"; visible: !parent.ok
                color: parent.r && parent.r.estado !== "neutro" ? cs.col("amb", 2) : cs.col("mist", 1) }
        Txt { g: parent.g; u: cs.u; oy: cs.oy; sx: 14; sy: 11; max: 9; fotograma: cs.fr; visible: !parent.ok
              texto: cs.up(parent.r && parent.r.estado !== "neutro" ? cs.tr("estado.sin_conexion") : cs.tr("estado.no_configurado"))
              color: parent.r && parent.r.estado !== "neutro" ? cs.col("amb", 3) : cs.col("mist", 2); familia: cs.fam; ajusteY: cs.aj }
        Repeater {
            model: cs.f.histRed
            Item {
                readonly property int cima: 29 + 11 - Math.round(Math.max(0, Math.min(1, modelData[0])) * 11)
                readonly property int upy: 29 + 11 - Math.round(Math.max(0, Math.min(1, modelData[1])) * 11)
                Px { g: parent.parent.g; u: cs.u; oy: cs.oy; lx: 6 + index * 2; ly: parent.cima + 1; lw: 2; lh: Math.max(0, 40 - parent.cima); color: cs.col("cyan", 0); visible: parent.cima < 40 }
                Px { g: parent.parent.g; u: cs.u; oy: cs.oy; lx: 6 + index * 2; ly: parent.cima; lw: 2; lh: 1; color: cs.col("cyan", 2) }
                Px { g: parent.parent.g; u: cs.u; oy: cs.oy; lx: 6 + index * 2; ly: parent.upy; lw: 2; lh: 1; color: cs.col("mag", 2) }
            }
        }
    }

    // ================================================================== SISTEMA: RAM / GPU / DISCO
    Item {
        visible: cs.f.mostrar("sistema")
        readonly property var g: cs.geom("ram")
        readonly property var filas: {
            var out = [], dd = cs.d || {}
            var r = dd.ram, gg = dd.gpu, k = dd.disco
            out.push({ et: "RAM", ok: !!r && r.estado !== "neutro" && r.pct !== null && r.pct !== undefined,
                       val: r && r.total_mb ? LG.gb(r.usada_mb) + "/" + LG.gb(r.total_mb) : "", fr: r ? r.pct / 100 : 0 })
            out.push({ et: "GPU", ok: !!gg && gg.estado !== "neutro" && gg.pct !== null && gg.pct !== undefined,
                       val: gg ? LG.num(gg.pct) + "%" + (gg.temp_c !== null && gg.temp_c !== undefined ? " " + LG.num(gg.temp_c) + "°" : "") : "", fr: gg && gg.pct !== null ? gg.pct / 100 : 0 })
            out.push({ et: "DSK", ok: !!k && k.estado !== "neutro" && k.pct !== null && k.pct !== undefined,
                       val: k ? LG.num(k.pct) + "%" : "", fr: k ? k.pct / 100 : 0 })
            return out
        }
        Repeater {
            model: parent.filas
            Item {
                readonly property var g: parent.g
                readonly property int y0: 10 + index * 13
                Txt { g: parent.g; u: cs.u; oy: cs.oy; sx: 7; sy: parent.y0; texto: modelData.et; color: cs.col("mist", 3); familia: cs.fam; ajusteY: cs.aj }
                Txt { g: parent.g; u: cs.u; oy: cs.oy; sx: 87; sy: parent.y0; derecha: true; visible: modelData.ok; texto: modelData.val; color: cs.col("vio", 3); familia: cs.fam; ajusteY: cs.aj }
                Txt { g: parent.g; u: cs.u; oy: cs.oy; sx: 35; sy: parent.y0; max: 7; fotograma: cs.fr; visible: !modelData.ok
                      texto: cs.up(cs.tr("estado.no_configurado")); color: cs.col("mist", 1); familia: cs.fam; ajusteY: cs.aj }
                Repeater {
                    model: modelData.ok ? Math.round(Math.max(0, Math.min(1, modelData.fr)) * 26) : 0
                    Px { g: parent.g; u: cs.u; oy: cs.oy; lx: 7 + index * 3; ly: parent.y0 + 8; lw: 2; lh: 2
                         color: cs.col(LG.rampaCarga((index + 0.5) / 26), 2) }
                }
            }
        }
    }

    // ================================================================== VPN (tubo de neon)
    Item {
        visible: cs.f.mostrar("vpn")
        readonly property var g: cs.geom("vpn")
        readonly property var v: cs.d && cs.d.vpn ? cs.d.vpn : null
        readonly property string st: !v || v.estado === "neutro" ? "neutro" : (v.activa ? "ok" : "no")
        // inactiva: parpadeo lento (0,5 Hz); en calma, fijo
        readonly property bool apagon: st === "no" && !cs.f.calma && (Math.floor(cs.fr / 8) % 2 === 1)
        readonly property string rampa: st === "ok" ? "grn" : (st === "no" ? "red" : "slate")
        Glifo { g: parent.g; u: cs.u; oy: cs.oy; sx: 5; sy: 6; nombre: "escudo"; color: cs.col(parent.rampa, parent.apagon ? 1 : 2) }
        Glifo { g: parent.g; u: cs.u; oy: cs.oy; sx: parent.st === "ok" ? 7 : 7; sy: 9; nombre: parent.st === "ok" ? "ok" : (parent.st === "no" ? "no" : "neu")
                color: cs.col(parent.rampa, 3) }
        Txt { g: parent.g; u: cs.u; oy: cs.oy; sx: 18; sy: 6; esc: 2; texto: "VPN"; color: cs.col(parent.rampa, parent.apagon ? 1 : 3); familia: cs.fam; ajusteY: cs.aj }
        Txt { g: parent.g; u: cs.u; oy: cs.oy; sx: 6; sy: 27; max: 7; fotograma: cs.fr
              texto: parent.st === "ok" ? cs.up(cs.tr("estado.activa")) :
                     cs.up(parent.st === "no" ? cs.tr("estado.inactiva") : cs.tr("estado.no_configurado"))
              color: cs.col(parent.rampa, parent.st === "neutro" ? 2 : 3); familia: cs.fam; ajusteY: cs.aj }
    }

    // ================================================================== GIT
    Item {
        visible: cs.f.mostrar("repos")
        readonly property var g: cs.geom("git")
        readonly property var gi: cs.d && cs.d.git ? cs.d.git : null
        readonly property bool ok: gi !== null && gi.estado !== "neutro" && gi.total !== undefined
        Txt { g: parent.g; u: cs.u; oy: cs.oy; sx: 17; sy: 10; visible: parent.ok
              texto: parent.ok ? parent.gi.repos_con_cambios + "/" + parent.gi.total : ""; color: cs.col("amb", 3); familia: cs.fam; ajusteY: cs.aj }
        Txt { g: parent.g; u: cs.u; oy: cs.oy; sx: 17; sy: 19; max: 7; fotograma: cs.fr; texto: cs.up(cs.tr("etiqueta.repos")); color: cs.col("mist", 3); familia: cs.fam; ajusteY: cs.aj }
        Txt { g: parent.g; u: cs.u; oy: cs.oy; sx: 17; sy: 28; visible: parent.ok && parent.gi.sin_subir > 0
              texto: parent.ok ? "↑" + parent.gi.sin_subir : ""; color: cs.col("amb", 2); familia: cs.fam; ajusteY: cs.aj }
        Glifo { g: parent.g; u: cs.u; oy: cs.oy; sx: 18; sy: 29; nombre: "ok"; color: cs.col("grn", 2); visible: parent.ok && parent.gi.sin_subir === 0 && parent.gi.repos_con_cambios === 0 }
        Txt { g: parent.g; u: cs.u; oy: cs.oy; sx: 17; sy: 28; max: 7; fotograma: cs.fr; visible: !parent.ok
              texto: cs.up(cs.tr("estado.no_configurado")); color: cs.col("mist", 2); familia: cs.fam; ajusteY: cs.aj }
    }

    // ================================================================== ENERGIA: bateria + temperatura
    Item {
        visible: cs.f.mostrar("bar")
        readonly property var g: cs.geom("bat")
        readonly property var b: cs.d && cs.d.bateria ? cs.d.bateria : null
        readonly property bool hay: b !== null && b.estado !== "neutro" && b.pct !== null && b.pct !== undefined
        readonly property string rampa: !hay ? "slate" : (b.pct < 15 && !b.cargando ? "red" : (b.pct < 30 && !b.cargando ? "amb" : "grn"))
        readonly property var cpu: cs.d && cs.d.cpu ? cs.d.cpu : null
        Repeater {
            model: parent.hay ? Math.min(5, Math.ceil(parent.b.pct / 20)) : 0
            Px { g: parent.g; u: cs.u; oy: cs.oy; lx: 9 + index * 4; ly: 13; lw: 3; lh: 5; color: cs.col(parent.rampa, 3) }
        }
        Txt { g: parent.g; u: cs.u; oy: cs.oy; sx: 32; sy: 12
              texto: parent.hay ? (parent.b.pct >= 100 ? "100" : Math.round(parent.b.pct) + (parent.b.cargando ? "↑" : "%")) : "AC"
              color: parent.hay ? cs.col("wht", 1) : cs.col("mist", 2); familia: cs.fam; ajusteY: cs.aj }
        Txt { g: parent.g; u: cs.u; oy: cs.oy; sx: 15; sy: 25
              texto: parent.cpu && parent.cpu.temp_c !== null && parent.cpu.temp_c !== undefined ? LG.num(parent.cpu.temp_c) + "°C" : "--°C"
              color: parent.cpu && parent.cpu.temp_c >= 85 ? cs.col("red", 3) : cs.col("amb", 3); familia: cs.fam; ajusteY: cs.aj }
    }

    // ================================================================== ZEPELIN: consejos en matriz LED
    Item {
        id: zep
        visible: cs.f.mostrar("consejos")
        readonly property var pant: LY.L.zepelin_pantalla
        x: Math.round((pant.x + cs.f.flotaX) * cs.u); y: Math.round((pant.y + cs.f.flotaY - cs.oy) * cs.u)
        width: Math.round(pant.w * cs.u); height: Math.round(pant.h * cs.u)
        clip: true
        readonly property string texto: cs.f.consejosTexto
        readonly property var matriz: LG.matrizLed(texto)
        readonly property int ncol: Math.floor(pant.w / 2)                    // columnas LED visibles (pitch 2 px)
        readonly property int ciclo: matriz.length + ncol
        // desplazamiento en columnas LED enteras (2 por fotograma; 1 en modo calma); 'avance' no salta al reiniciar el bucle
        readonly property int paso: matriz.length > 0 ? (cs.f.avance * (cs.f.calma ? 1 : 2)) % ciclo : 0
        // Matriz LED real: cada punto encendido es 1 px logico en las posiciones pares, justo las que deja ver la rejilla.
        // (Con texto de fuente normal los trazos finos se rompian al pasar por la rejilla: letras "cortadas".)
        Canvas {
            id: lienzo
            anchors.fill: parent
            renderTarget: Canvas.Image
            onWidthChanged: requestPaint()
            Connections { target: zep; function onPasoChanged() { lienzo.requestPaint() } function onMatrizChanged() { lienzo.requestPaint() } }
            onPaint: {
                var ctx = getContext("2d")
                ctx.clearRect(0, 0, width, height)
                ctx.fillStyle = "" + cs.col("amb", 3)
                var px = Math.max(1, Math.round(cs.u)), m = zep.matriz
                for (var c = 0; c < zep.ncol; c++) {
                    var k = c + zep.paso - zep.ncol                          // columna del texto que cae en esta columna LED
                    if (k < 0 || k >= m.length || m[k] === 0) continue
                    for (var r = 0; r < 7; r++)
                        if ((m[k] >> r) & 1) ctx.fillRect(Math.round(c * 2 * cs.u), Math.round(r * 2 * cs.u), px, px)
                }
            }
        }
        Image {     // rejilla de LED: solo se ve 1 de cada 2x2 pixeles
            anchors.fill: parent
            source: "../capas/rejilla-led-" + cs.f.nombreModo + ".png"
            smooth: false
        }
    }

    // ================================================================== DRONES con etiqueta (actualizaciones, servicios, sincronizacion)
    Repeater {
        model: LY.L.drones
        Item {
            id: dr
            readonly property real a: 2 * Math.PI * (cs.fr / 96 + index * 0.13)
            readonly property int px: Math.round(modelData.x + 9 * Math.sin(a))
            readonly property int py: Math.round(modelData.y + 4 * Math.sin(2 * a))
            readonly property var et: cs.f.etiquetaDron(modelData.dato)
            visible: cs.f.mostrar("drones") && (modelData.dato !== "sync" || cs.f.mostrar("sync"))
            Image {
                source: "../capas/dron.png"; smooth: false
                x: Math.round(dr.px * cs.u); y: Math.round((dr.py - cs.oy) * cs.u)
                width: Math.round(7 * cs.u); height: Math.round(4 * cs.u)
            }
            Rectangle {      // luz de posicion: 1 Hz
                x: Math.round((dr.px + 3) * cs.u); y: Math.round((dr.py + 3 - cs.oy) * cs.u)
                width: Math.round(cs.u); height: Math.round(cs.u)
                color: (Math.floor((cs.fr + index * 2) / 4) % 2 === 0 || cs.f.calma) ? cs.col("red", 2) : cs.col("red", 0)
            }
            Item {
                visible: dr.et !== null
                readonly property real w: dr.et ? 8 + (dr.et.glifo ? 8 : 0) + dr.et.texto.length * 7 : 0
                readonly property real tx: dr.px + 3 - Math.floor(w / 2)
                Rectangle { x: Math.round((dr.px + 3) * cs.u); y: Math.round((dr.py + 4 - cs.oy) * cs.u); width: Math.round(cs.u); height: Math.round(4 * cs.u); color: cs.col("slate", 1) }
                Rectangle {
                    x: Math.round(parent.tx * cs.u); y: Math.round((dr.py + 8 - cs.oy) * cs.u)
                    width: Math.round(parent.w * cs.u); height: Math.round(11 * cs.u)
                    color: cs.col("ink", 0); border.width: Math.round(cs.u); border.color: dr.et ? cs.col(dr.et.rampa, 1) : "transparent"
                }
                Glifo { u: cs.u; oy: cs.oy; g: ({ x: parent.tx, y: dr.py + 8, w: 0, h: 0, pendiente: 0 }); sx: 4; sy: 3
                        nombre: dr.et && dr.et.glifo ? dr.et.glifo : "neu"; visible: !!(dr.et && dr.et.glifo); color: dr.et ? cs.col(dr.et.rampa, 3) : "white" }
                Txt { u: cs.u; oy: cs.oy; g: ({ x: parent.tx, y: dr.py + 8, w: 0, h: 0, pendiente: 0 }); sx: dr.et && dr.et.glifo ? 12 : 4; sy: 2
                      texto: dr.et ? dr.et.texto : ""; color: dr.et ? cs.col(dr.et.rampa, 3) : "white"; familia: cs.fam; ajusteY: cs.aj }
            }
        }
    }
}
