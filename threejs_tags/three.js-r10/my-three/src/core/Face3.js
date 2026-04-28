/**
 * Face3 - 三角形面类
 * 存储三个顶点索引、法线和颜色
 */

THREE = THREE || {};

THREE.Face3 = function (a, b, c, normal, color) {
    this.a = a;
    this.b = b;
    this.c = c;
    this.normal = normal || new THREE.Vector3();
    this.screen = new THREE.Vector3();
    this.color = color || new THREE.Color(0x000000);
};

THREE.Face3.prototype = {
    constructor: THREE.Face3,

    toString: function () {
        return 'THREE.Face3 ( ' + this.a + ', ' + this.b + ', ' + this.c + ' )';
    }
};
