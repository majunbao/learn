/**
 * Mesh - 网格对象
 * 由顶点和面组成的3D对象
 */

THREE = THREE || {};

THREE.Mesh = function (geometry, material) {
    THREE.Object3D.call(this, material);
    this.geometry = geometry;
    this.doubleSided = false;
};

THREE.Mesh.prototype = new THREE.Object3D();
THREE.Mesh.prototype.constructor = THREE.Mesh;
