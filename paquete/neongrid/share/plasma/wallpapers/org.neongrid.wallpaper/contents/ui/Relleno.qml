import QtQuick
import QtQuick.Effects

// Relleno de los bordes cuando la escena no cubre toda la pantalla (pantallas muy anchas, escalas que no encajan):
// la propia ciudad, desenfocada y oscurecida, como un resplandor. Va en su propio fichero para que, si esta version de Qt
// no trae QtQuick.Effects (Qt < 6.5), solo falle este relleno y no todo el fondo (Escena lo carga con un Loader).
Item {
    id: rl
    property string fuente: ""
    Image {
        id: img
        anchors.fill: parent
        source: rl.fuente
        fillMode: Image.PreserveAspectCrop
        smooth: true
        visible: false
    }
    MultiEffect {
        anchors.fill: parent
        source: img
        blurEnabled: true
        blurMax: 64
        blur: 1.0
        brightness: -0.1
        saturation: -0.15
    }
}
