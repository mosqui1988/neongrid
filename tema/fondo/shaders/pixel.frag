#version 440
// NeonGrid · escalado por ENTERO del lienzo logico (vecino mas cercano) + rejilla LED de 2x2 en las pantallas.
layout(location = 0) in vec2 qt_TexCoord0;
layout(location = 0) out vec4 fragColor;
layout(std140, binding = 0) uniform buf {
    mat4 qt_Matrix;
    float qt_Opacity;
    float lw;
    float lh;
    float led;       // 1 = rejilla LED visible (solo con N >= 2)
};
layout(binding = 1) uniform sampler2D fuente;
layout(binding = 2) uniform sampler2D geo;

void main() {
    vec2 q = qt_TexCoord0 * vec2(lw, lh);
    vec2 lp = floor(q);
    vec2 uv = (lp + 0.5) / vec2(lw, lh);
    vec3 c = texture(fuente, uv).rgb;
    if (led > 0.5) {
        float fl = floor(texture(geo, uv).g * 255.0 + 0.5);
        if (mod(floor(fl / 2.0), 2.0) > 0.5) {
            vec2 sub = floor(fract(q) * 2.0);
            float k = sub.x + sub.y;
            c *= k < 0.5 ? 1.0 : (k < 1.5 ? 0.769 : 0.588);
        }
    }
    fragColor = vec4(c, 1.0) * qt_Opacity;
}
