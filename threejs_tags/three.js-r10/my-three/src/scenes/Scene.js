/**
 * Scene - 场景类
 * 管理所有3D对象
 */

THREE = THREE || {};

THREE.Scene = function () {
    this.objects = [];
};

THREE.Scene.prototype = {
    constructor: THREE.Scene,

    add: function (object) {
        this.objects.push(object);
    },

    toString: function () {
        return 'THREE.Scene ( ' + this.objects + ' )';
    }
};
