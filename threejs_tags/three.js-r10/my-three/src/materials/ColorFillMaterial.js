/**
 * ColorFillMaterial - 纯色填充材质
 */

THREE = THREE || {};

THREE.ColorFillMaterial = function (hex, opacity) {
    var alpha = opacity !== undefined ? opacity : 1;
    this.color = new THREE.Color((Math.floor(alpha * 0xff) << 24) | hex);

    this.toString = function () {
        return 'THREE.ColorFillMaterial ( color: ' + this.color + ' )';
    };
};
