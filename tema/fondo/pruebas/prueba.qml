import QtQuick
// Arnes de prueba del fondo: carga main.qml con un WallpaperItem simulado y captura fotogramas.
// Uso: qml6 -I stub prueba.qml -- clave=valor ...  (paquete=, w=, h=, hora=, capturas=ms,ms  salida=prefijo
//      fin=ms  cfg=JSON con claves de main.xml)
//      rafaga=N         captura N fotogramas, uno por tick de 40 ms (el registro dice a que fotograma de la animacion corresponde cada uno)
//      ciclo=h0:h1:N:ms captura N fotogramas avanzando la hora simulada de h0 a h1 (ms entre capturas)
Window {
    id: win
    readonly property var a: {
        var o = {}, l = Qt.application.arguments, on = false
        for (var i = 0; i < l.length; i++) {
            if (l[i] === "--") { on = true; continue }
            if (!on) continue
            var k = l[i].indexOf("="); if (k > 0) o[l[i].slice(0, k)] = l[i].slice(k + 1)
        }
        return o
    }
    width: Number(a.w || 1920); height: Number(a.h || 1200)
    visible: true; color: "black"
    Loader {
        id: ld
        anchors.fill: parent
        source: win.a.paquete + "/contents/ui/main.qml"
        onLoaded: {
            var c = { Calma: false, Demo: false, Idioma: "auto", Carteles: "", Ciudad: "", Calidad: -1, Escala: 0, IntervaloDatos: 2, HoraSimulada: Number(win.a.hora || -1) }
            for (var k in win.a) if (k.indexOf("cfg.") === 0) { var v = win.a[k]; c[k.slice(4)] = v === "true" ? true : (v === "false" ? false : (isNaN(Number(v)) || v === "" ? v : Number(v))) }
            item.configuration = c
        }
    }
    property var cicloP: (a.ciclo || "").split(":").map(Number)
    property int cicloK: 0
    property real cicloT: 0
    property var tiempos: (a.capturas || "").split(",").filter(function (s) { return s.length }).map(Number)
    property int i: 0
    property real t0: Date.now()
    Timer {
        interval: 50; running: true; repeat: true
        onTriggered: {
            var el = Date.now() - win.t0
            if (win.a.rafaga && ld.item && el > Number(win.a.inicio || 1500) && win.i < Number(win.a.rafaga)) {
                var nr = win.i; win.i++
                ld.item.grabToImage(function (r) { r.saveToFile(win.a.salida + "-" + nr + ".png"); console.log("captura", nr, "fotograma", ld.item.fotograma) })
                return
            }
            if (win.a.ciclo && ld.item && el > Number(win.a.inicio || 1500) && win.cicloK < win.cicloP[2] * 2) {      // mitad par: fija la hora; impar: captura
                var kk = Math.floor(win.cicloK / 2)
                if (win.cicloK % 2 === 0) {
                    var hh = win.cicloP[0] + (win.cicloP[1] - win.cicloP[0]) * kk / win.cicloP[2]
                    var c2 = ld.item.configuration; var c3 = {}; for (var q in c2) c3[q] = c2[q]; c3.HoraSimulada = hh % 24; ld.item.configuration = c3
                    win.cicloK++; win.cicloT = el
                } else if (el - win.cicloT >= win.cicloP[3]) {
                    ld.item.grabToImage(function (r) { r.saveToFile(win.a.salida + "-" + kk + ".png") })
                    win.cicloK++
                }
                return
            }
            if (win.i < win.tiempos.length && el >= win.tiempos[win.i]) {
                var n = win.i; win.i++
                if (ld.item) ld.item.grabToImage(function (r) { r.saveToFile(win.a.salida + "-" + n + ".png"); console.log("captura", n, "fotograma", ld.item.fotograma, "calidad", ld.item.calidad, "familia", ld.item.familia) })
            }
            if (el >= Number(win.a.fin || 3000)) { if (ld.item) console.log("fin fotograma", ld.item.fotograma, "animando", ld.item.animando, "visible", ld.item.visible, "bloq", ld.item.bloqueada, "bat", ld.item.bateriaBaja, "cal", ld.item.calidad, "tiempos", JSON.stringify(win.tiempos), "datos", Object.keys(ld.item.datos).length); Qt.quit() }
        }
    }
}
