import QtQuick
import "logica.js" as LG
import "layout.js" as LY

// Escena escalada por ENTERO, anclada arriba y a la derecha (ahi estan los carteles; la izquierda es
// la zona tranquila de iconos). Si el escalado entero cubre la pantalla recortando <= 25 % se recorta;
// si no, se usa el entero que cabe y los bordes se rellenan con la vista estatica (capa lejana).
Item {
    id: es
    property var f
    property int escalaCfg: 0

    readonly property real dpr: (Window.window && Window.window.devicePixelRatio) ? Window.window.devicePixelRatio : 1
    readonly property real pw: width * dpr
    readonly property real ph: height * dpr
    readonly property string rel: ph > 0 && pw / ph > 1.7 ? "16x9" : "16x10"
    readonly property var relacion: LY.L.relaciones[rel]
    readonly property real lw: relacion.tam[0]
    readonly property real lh: relacion.tam[1]
    readonly property real oy: relacion.oy
    readonly property int nCubre: Math.max(1, Math.ceil(Math.max(pw / lw, ph / lh)))
    readonly property bool cubre: (lw * nCubre - pw) / (lw * nCubre) <= 0.25 && (lh * nCubre - ph) / (lh * nCubre) <= 0.25
    readonly property int nCabe: Math.max(1, Math.floor(Math.min(pw / lw, ph / lh)))
    // Pantallas pequenas (1280x720, 1366x768, 1280x1024...): el entero que cubre recorta demasiado y el que cabe deja la ciudad
    // diminuta con marco. Si la escala que cubre exactamente es < 2x se usa tal cual (fraccionaria): recorta un poco por la
    // izquierda/abajo, y los carteles (derecha/arriba) siguen visibles.
    readonly property real uCubre: Math.max(pw / lw, ph / lh)
    // Pantallas muy anchas (3440x1440...): el entero que cabe deja la ciudad pequena con barras enormes. Si la escala que llena
    // el ALTO es >25 % mayor que ese entero, se usa esa (fraccionaria) y los lados se rellenan con la ciudad desenfocada.
    readonly property real uFit: Math.min(pw / lw, ph / lh)
    readonly property real factor: escalaCfg > 0 ? escalaCfg : (cubre ? nCubre : (uCubre < 2 ? uCubre : (uFit / nCabe > 1.25 ? uFit : nCabe)))
    readonly property real u: factor / dpr                        // unidades de item por pixel logico
    readonly property real sw: lw * u
    readonly property real sh: lh * u
    readonly property bool software: GraphicsInfo.api === GraphicsInfo.Software
    readonly property string dir: "../capas/" + rel + "/"
    readonly property var nombres: LG.NOMBRES
    readonly property var bruma: LG.BRUMA[f.modoDominante]

    // relleno de bordes (solo si sobra pantalla): la ciudad desenfocada (Relleno.qml); sin QtQuick.Effects, imagen oscura
    Loader {
        id: relleno
        anchors.fill: parent
        active: es.sw < es.width - 1 || es.sh < es.height - 1
        source: "Relleno.qml"
        onLoaded: item.fuente = Qt.binding(function () { return es.dir + "vista-" + es.nombres[es.f.modoDominante] + ".png" })
        onStatusChanged: if (status === Loader.Error) { sinEfectos.visible = true }
    }
    Image {
        id: sinEfectos
        anchors.fill: parent
        visible: false
        source: visible ? es.dir + "vista-" + es.nombres[es.f.modoDominante] + ".png" : ""
        fillMode: Image.PreserveAspectCrop
        smooth: false
        opacity: 0.35
    }

    Item {
        id: escenario
        width: es.sw; height: es.sh
        x: Math.round((es.sw > es.width ? es.width - es.sw : (es.width - es.sw) / 2) * es.dpr) / es.dpr
        y: Math.round((es.sh > es.height ? 0 : (es.height - es.sh) / 2) * es.dpr) / es.dpr

        Image { id: imgA; visible: false; smooth: false; source: es.dir + "escena-" + es.nombres[es.f.modoA] + ".png" }
        Image { id: imgB; visible: false; smooth: false; source: es.dir + "escena-" + es.nombres[es.f.modoB] + ".png" }
        Image { id: imgGeo; visible: false; smooth: false; source: es.dir + "geo.png" }
        Image { id: imgVia; visible: false; smooth: false; source: es.dir + "via.png" }
        Image { id: imgAtlas; visible: false; smooth: false; source: "../capas/atlas.png" }

        ShaderEffect {
            id: pase1
            width: es.lw; height: es.lh
            visible: !es.software
            property variant escA: imgA
            property variant escB: imgB
            property variant geo: imgGeo
            property variant via: imgVia
            property variant atlas: imgAtlas
            property real tf: es.f.fotograma
            property real oy: es.oy
            property real lh: es.lh
            property real modoA: es.f.modoA
            property real modoB: es.f.modoB
            property real mezcla: es.f.mezcla
            property real noche: es.f.noche
            property real lluvia: es.f.calma || !es.f.mostrar("lluvia") ? 0 : (es.f.datos && es.f.datos.carga && es.f.datos.carga.intensidad_lluvia !== undefined && es.f.datos.carga.intensidad_lluvia !== null ? es.f.datos.carga.intensidad_lluvia : 0.35)
            property real trafico: {
                var t = es.f.datos ? es.f.datos.trafico : null
                if (!t) return 0.5
                var v = typeof t.nivel === "number" ? t.nivel : (typeof t.valor === "number" ? t.valor : 0.5)
                return Math.max(0, Math.min(1, v))
            }
            property real calma: es.f.calma ? 1 : 0
            property real calidad: es.f.calidad
            property real sincro: es.f.sincro
            property real nieblaD: es.f.modoDominante === 0 ? 3300 : 2600
            property vector4d bruma: Qt.vector4d(es.bruma[0] / 255, es.bruma[1] / 255, es.bruma[2] / 255, 1)
            property vector4d astroSol: es.f.astroSol
            property vector4d astroLuna: es.f.astroLuna
            property real faseLuna: es.f.faseLuna
            fragmentShader: "../shaders/escena.frag.qsb"
        }
        ShaderEffectSource {
            id: fuente
            sourceItem: pase1
            hideSource: true
            live: true
            smooth: false
            textureSize: Qt.size(es.lw, es.lh)
            width: 1; height: 1; opacity: 0
        }
        ShaderEffect {
            anchors.fill: parent
            visible: !es.software
            property variant fuente: fuente
            property variant geo: imgGeo
            property real lw: es.lw
            property real lh: es.lh
            property real led: es.factor >= 2 ? 1 : 0
            fragmentShader: "../shaders/pixel.frag.qsb"
        }
        // sin GPU (renderizador software): escena estatica + texto vivo
        Image {
            anchors.fill: parent
            visible: es.software
            source: es.software ? es.dir + "vista-" + es.nombres[es.f.modoDominante] + ".png" : ""
            smooth: false
        }
        Rectangle {      // tinte de alerta: rojo suave, fijo (sin parpadeo)
            anchors.fill: parent
            visible: es.f.alerta
            color: LG.color(es.f.paleta, "red", 2)
            opacity: 0.07
        }
        // zepelin: capa propia (casco + haz nocturno) que flota; los consejos LED de Carteles lo acompanan
        Item {
            id: zepelin
            readonly property var sp: LY.L.zepelin_sprite
            readonly property var hz: LY.L.zepelin_haz
            readonly property real fundidoA: 1
            readonly property real fundidoB: es.f.modoB !== es.f.modoA ? es.f.mezcla : 0
            readonly property real hazOp: (es.f.modoA === 0 ? 1 - es.f.mezcla : 0) + (es.f.modoB === 0 && es.f.modoA !== 0 ? es.f.mezcla : 0)
            Image {
                visible: zepelin.hazOp > 0.01; opacity: zepelin.hazOp; smooth: false
                source: "../capas/zepelin-haz.png"
                x: Math.round((zepelin.hz.x + es.f.flotaX) * es.u); y: Math.round((zepelin.hz.y + es.f.flotaY - es.oy) * es.u)
                width: Math.round(zepelin.hz.w * es.u); height: Math.round(zepelin.hz.h * es.u)
            }
            Image {
                smooth: false
                source: "../capas/zepelin-" + es.nombres[es.f.modoA] + ".png"
                x: Math.round((zepelin.sp.x + es.f.flotaX) * es.u); y: Math.round((zepelin.sp.y + es.f.flotaY - es.oy) * es.u)
                width: Math.round(zepelin.sp.w * es.u); height: Math.round(zepelin.sp.h * es.u)
            }
            Image {
                visible: zepelin.fundidoB > 0.01; opacity: zepelin.fundidoB; smooth: false
                source: "../capas/zepelin-" + es.nombres[es.f.modoB] + ".png"
                x: Math.round((zepelin.sp.x + es.f.flotaX) * es.u); y: Math.round((zepelin.sp.y + es.f.flotaY - es.oy) * es.u)
                width: Math.round(zepelin.sp.w * es.u); height: Math.round(zepelin.sp.h * es.u)
            }
        }
        Carteles { anchors.fill: parent; f: es.f; u: es.u; oy: es.oy }
    }
}
