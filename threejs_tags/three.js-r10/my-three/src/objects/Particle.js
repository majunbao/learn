/**
 * Particle - 粒子对象
 * 单个粒子，用于粒子系统
 */

THREE = THREE || {};

THREE.Particle = function (material) {
    THREE.Object3D.call(this, material);
    this.size = 1;
    this.autoUpdateMatrix = false;
};

THREE.Particle.prototype = new THREE.Object3D();
THREE.Particle.prototype.constructor = THREE.Particle;
