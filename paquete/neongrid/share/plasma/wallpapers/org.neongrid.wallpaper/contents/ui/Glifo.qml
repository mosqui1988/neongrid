import QtQuick
import "logica.js" as LG

// Glifo de pixeles propios (✔ ✖ ▲ escudo...): la forma acompana siempre al color del estado.
Item {
    id: gl
    property var g: ({ x: 0, y: 0, w: 0, h: 0, pendiente: 0 })
    property real u: 1
    property real oy: 0
    property real sx: 0
    property real sy: 0
    property string nombre: "ok"
    property color color: "#39ff88"
    readonly property var pts: LG.pixeles(nombre)
    readonly property real dy: Math.round(g.pendiente * (sx + 3 - g.w / 2))
    Repeater {
        model: gl.pts
        Rectangle {
            antialiasing: false
            color: gl.color
            x: Math.round((gl.g.x + gl.sx + modelData[0]) * gl.u)
            y: Math.round((gl.g.y - gl.oy + gl.sy + modelData[1] + gl.dy) * gl.u)
            width: Math.round(gl.u); height: Math.round(gl.u)
        }
    }
}
