/**
 * Face4 - 四边形面类
 * 存储四个顶点索引、法线和颜色
 */

THREE = THREE || {};

THREE.Face4 = function (a, b, c, d, normal, color) {
    this.a = a;
    this.b = b;
    this.c = c;
    this.d = d;
    this.normal = normal || new THREE.Vector3();
    this.screen = new THREE.Vector3();
    this.color = color || new THREE.Color(0x000000);
};

THREE.Face4.prototype = {
    constructor: THREE.Face4,

    toString: function () {
        return 'THREE.Face4 ( ' + this.a + ', ' + this.b + ', ' + this.c + ', ' + this.d + ' )';
    }
};
