/**
 * RenderableFace3 - 可渲染三角形面
 */

THREE = THREE || {};

THREE.RenderableFace3 = function () {
    this.v1 = new THREE.Vector2();
    this.v2 = new THREE.Vector2();
    this.v3 = new THREE.Vector2();
    this.z = null;
    this.color = null;
    this.material = null;
};
