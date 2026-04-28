/**
 * Vertex - 顶点类
 * 存储顶点的世界坐标、法线和屏幕坐标
 */

THREE = THREE || {};

THREE.Vertex = function (position, normal) {
    this.position = position || new THREE.Vector3();
    this.normal = normal || new THREE.Vector3();
    this.screen = new THREE.Vector3();
    this.__visible = true;
};

THREE.Vertex.prototype = {
    constructor: THREE.Vertex,

    toString: function () {
        return 'THREE.Vertex ( position: ' + this.position + ', normal: ' + this.normal + ' )';
    }
};
