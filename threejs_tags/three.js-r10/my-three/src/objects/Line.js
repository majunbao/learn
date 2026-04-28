/**
 * Line - 线条对象
 * 由顶点序列组成的线条
 */

THREE = THREE || {};

THREE.Line = function (geometry, material) {
    THREE.Object3D.call(this, material);
    this.geometry = geometry;
};

THREE.Line.prototype = new THREE.Object3D();
THREE.Line.prototype.constructor = THREE.Line;
