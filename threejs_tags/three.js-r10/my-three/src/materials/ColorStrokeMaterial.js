/**
 * ColorStrokeMaterial - 纯色描边材质
 */

THREE = THREE || {};

THREE.ColorStrokeMaterial = function (lineWidth, hex, opacity) {
    this.lineWidth = lineWidth || 1;
    var alpha = opacity !== undefined ? opacity : 1;
    this.color = new THREE.Color((Math.floor(alpha * 0xff) << 24) | hex);

    this.toString = function () {
        return 'THREE.ColorStrokeMaterial ( lineWidth: ' + this.lineWidth + ', color: ' + this.color + ' )';
    };
};
