/**
 * Vector3 - 3D向量类
 * 用于表示3D空间中的点和方向
 */

THREE = THREE || {};

THREE.Vector3 = function (x, y, z) {
    this.x = x || 0;
    this.y = y || 0;
    this.z = z || 0;
};

THREE.Vector3.prototype = {
    constructor: THREE.Vector3,

    set: function (x, y, z) {
        this.x = x;
        this.y = y;
        this.z = z;
        return this;
    },

    copy: function (v) {
        this.x = v.x;
        this.y = v.y;
        this.z = v.z;
        return this;
    },

    clone: function () {
        return new THREE.Vector3(this.x, this.y, this.z);
    },

    add: function (v1, v2) {
        this.x = v1.x + v2.x;
        this.y = v1.y + v2.y;
        this.z = v1.z + v2.z;
        return this;
    },

    addSelf: function (v) {
        this.x += v.x;
        this.y += v.y;
        this.z += v.z;
        return this;
    },

    addScalar: function (s) {
        this.x += s;
        this.y += s;
        this.z += s;
        return this;
    },

    sub: function (v1, v2) {
        this.x = v1.x - v2.x;
        this.y = v1.y - v2.y;
        this.z = v1.z - v2.z;
        return this;
    },

    subSelf: function (v) {
        this.x -= v.x;
        this.y -= v.y;
        this.z -= v.z;
        return this;
    },

    cross: function (v1, v2) {
        this.x = v1.y * v2.z - v1.z * v2.y;
        this.y = v1.z * v2.x - v1.x * v2.z;
        this.z = v1.x * v2.y - v1.y * v2.x;
        return this;
    },

    crossSelf: function (v) {
        var tx = this.x, ty = this.y, tz = this.z;
        this.x = ty * v.z - tz * v.y;
        this.y = tz * v.x - tx * v.z;
        this.z = tx * v.y - ty * v.x;
        return this;
    },

    multiplySelf: function (v) {
        this.x *= v.x;
        this.y *= v.y;
        this.z *= v.z;
        return this;
    },

    multiplyScalar: function (s) {
        this.x *= s;
        this.y *= s;
        this.z *= s;
        return this;
    },

    dot: function (v) {
        return this.x * v.x + this.y * v.y + this.z * v.z;
    },

    distanceTo: function (v) {
        return Math.sqrt(this.distanceToSquared(v));
    },

    distanceToSquared: function (v) {
        var dx = this.x - v.x;
        var dy = this.y - v.y;
        var dz = this.z - v.z;
        return dx * dx + dy * dy + dz * dz;
    },

    length: function () {
        return Math.sqrt(this.x * this.x + this.y * this.y + this.z * this.z);
    },

    lengthSq: function () {
        return this.x * this.x + this.y * this.y + this.z * this.z;
    },

    negate: function () {
        this.x = -this.x;
        this.y = -this.y;
        this.z = -this.z;
        return this;
    },

    normalize: function () {
        var len = this.length();
        if (len > 0) {
            this.multiplyScalar(1 / len);
        }
        return this;
    },

    setLength: function (len) {
        return this.normalize().multiplyScalar(len);
    },

    lerp: function (v, alpha) {
        this.x += (v.x - this.x) * alpha;
        this.y += (v.y - this.y) * alpha;
        this.z += (v.z - this.z) * alpha;
        return this;
    },

    isZero: function () {
        return this.lengthSq() < 0.0001;
    },

    toString: function () {
        return 'THREE.Vector3(' + this.x + ', ' + this.y + ', ' + this.z + ')';
    }
};
