/**
 * Color - 颜色类
 * 支持十六进制和RGBA格式
 */

THREE = THREE || {};

THREE.Color = function (hex) {
    var r, g, b, a;

    this.__styleString = "rgba(0, 0, 0, 1)";

    this.setHex = function (hex) {
        r = hex >> 16 & 0xff;
        g = hex >> 8 & 0xff;
        b = hex & 0xff;
        a = (hex >> 24 & 0xff) / 255;
        this.updateStyleString();
    };

    this.setRGBA = function (rr, gg, bb, aa) {
        r = rr;
        g = gg;
        b = bb;
        a = aa;
        this.updateStyleString();
    };

    this.updateStyleString = function () {
        this.__styleString = 'rgba(' + r + ',' + g + ',' + b + ',' + a + ')';
    };

    this.getHex = function () {
        return (Math.floor(a * 255) << 24) | (r << 16) | (g << 8) | b;
    };

    this.getR = function () { return r; };
    this.getG = function () { return g; };
    this.getB = function () { return b; };
    this.getA = function () { return a; };

    this.toString = function () {
        return 'THREE.Color ( r: ' + r + ', g: ' + g + ', b: ' + b + ', a: ' + a + ' )';
    };

    this.setHex(hex || 0x000000);
};
