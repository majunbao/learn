/**
 * RenderableLine - 可渲染线条
 */

THREE = THREE || {};

THREE.RenderableLine = function () {
    this.v1 = new THREE.Vector2();
    this.v2 = new THREE.Vector2();
    this.z = null;
    this.color = null;
    this.material = null;
};
