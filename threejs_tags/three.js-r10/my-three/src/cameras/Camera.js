/**
 * Camera - 相机类
 * 定义视图和投影矩阵
 */

THREE = THREE || {};

THREE.Camera = function (fov, aspect, near, far) {
    this.position = new THREE.Vector3(0, 0, 0);
    this.target = { position: new THREE.Vector3(0, 0, 0) };

    this.projectionMatrix = THREE.Matrix4.makePerspective(fov, aspect, near, far);
    this.up = new THREE.Vector3(0, 1, 0);
    this.matrix = new THREE.Matrix4();

    this.autoUpdateMatrix = true;
};

THREE.Camera.prototype = {
    constructor: THREE.Camera,

    updateMatrix: function () {
        this.matrix.lookAt(this.position, this.target.position, this.up);
    },

    toString: function () {
        return 'THREE.Camera ( ' + this.position + ', ' + this.target.position + ' )';
    }
};
