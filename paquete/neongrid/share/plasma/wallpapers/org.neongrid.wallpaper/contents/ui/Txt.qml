import QtQuick

// Texto vivo sobre un cartel: un Text por caracter, con avance entero de 7 px logicos y escalon de
// perspectiva por glifo (cada caracter baja entero, como el cizallado del concepto; nunca se parte).
// Coordenadas (sx, sy) en pixeles del cartel; sy = linea de mayusculas. Si max > 0 y el texto no cabe,
// se desplaza en bucle (marquesina) con el fotograma global.
Item {
    id: tx
    property var g: ({ x: 0, y: 0, w: 0, h: 0, pendiente: 0 })
    property real u: 1
    property real oy: 0
    property real sx: 0
    property real sy: 0
    property string texto: ""
    property color color: "#e6f1ff"
    property int esc: 1
    property int max: 0
    property bool derecha: false
    property int fotograma: 0
    property string familia: "monospace"
    property real ajusteY: 0           // calibracion de la linea de mayusculas de la fuente
    readonly property real adv: 7 * esc
    readonly property bool largo: max > 0 && texto.length > max
    readonly property string mostrado: largo ? texto + "   " + texto : texto
    readonly property real ciclo: (texto.length + 3) * adv
    readonly property real desp: largo ? (fotograma * 2) % ciclo : 0
    readonly property real x0: derecha ? sx - texto.length * adv : sx

    Repeater {
        model: tx.mostrado.length
        Text {
            readonly property real lx: tx.x0 + index * tx.adv - tx.desp
            visible: !tx.largo || (lx >= tx.sx - 0.01 && lx + tx.adv <= tx.sx + tx.max * tx.adv + 0.01)
            text: tx.mostrado.charAt(index)
            color: tx.color
            font.family: tx.familia
            font.pixelSize: Math.round(11 * tx.esc * tx.u * 100) / 100
            font.hintingPreference: Font.PreferNoHinting
            renderType: Text.NativeRendering
            x: Math.round((tx.g.x + lx) * tx.u)
            y: Math.round((tx.g.y - tx.oy + tx.sy + tx.ajusteY * tx.esc + Math.round(tx.g.pendiente * (lx + tx.adv / 2 - tx.g.w / 2))) * tx.u)
        }
    }
}
