import QtQuick

// Rectangulo en pixeles logicos del cartel, con el escalon de perspectiva de su columna central.
Rectangle {
    property var g: ({ x: 0, y: 0, w: 0, h: 0, pendiente: 0 })
    property real u: 1
    property real oy: 0
    property real lx: 0
    property real ly: 0
    property real lw: 1
    property real lh: 1
    antialiasing: false
    x: Math.round((g.x + lx) * u)
    y: Math.round((g.y - oy + ly + Math.round(g.pendiente * (lx + lw / 2 - g.w / 2))) * u)
    width: Math.round(lw * u)
    height: Math.round(lh * u)
}
