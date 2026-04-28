/**
 * RenderableFace4 - 可渲染四边形面
 */

THREE = THREE || {};

THREE.RenderableFace4 = function () {
    this.v1 = new THREE.Vector2();
    this.v2 = new THREE.Vector2();
    this.v3 = new THREE.Vector2();
    this.v4 = new THREE.Vector2();
    this.z = null;
    this.color = null;
    this.material = null;
};
