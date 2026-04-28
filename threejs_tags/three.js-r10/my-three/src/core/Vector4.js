/**
 * Vector4 - 4D向量类（齐次坐标）
 * 用于矩阵变换和透视投影
 */

THREE = THREE || {};

THREE.Vector4 = function (x, y, z, w) {
    this.x = x || 0;
    this.y = y || 0;
    this.z = z || 0;
    this.w = w !== undefined ? w : 1;
};

THREE.Vector4.prototype = {
    constructor: THREE.Vector4,

    set: function (x, y, z, w) {
        this.x = x;
        this.y = y;
        this.z = z;
        this.w = w !== undefined ? w : 1;
        return this;
    },

    copy: function (v) {
        this.x = v.x;
        this.y = v.y;
        this.z = v.z;
        this.w = v.w !== undefined ? v.w : 1;
        return this;
    },

    clone: function () {
        return new THREE.Vector4(this.x, this.y, this.z, this.w);
    },

    add: function (v1, v2) {
        this.x = v1.x + v2.x;
        this.y = v1.y + v2.y;
        this.z = v1.z + v2.z;
        this.w = v1.w + v2.w;
        return this;
    },

    addSelf: function (v) {
        this.x += v.x;
        this.y += v.y;
        this.z += v.z;
        this.w += v.w;
        return this;
    },

    sub: function (v1, v2) {
        this.x = v1.x - v2.x;
        this.y = v1.y - v2.y;
        this.z = v1.z - v2.z;
        this.w = v1.w - v2.w;
        return this;
    },

    subSelf: function (v) {
        this.x -= v.x;
        this.y -= v.y;
        this.z -= v.z;
        this.w -= v.w;
        return this;
    },

    multiplyScalar: function (s) {
        this.x *= s;
        this.y *= s;
        this.z *= s;
        this.w *= s;
        return this;
    },

    divideScalar: function (s) {
        if (s !== 0) {
            this.x /= s;
            this.y /= s;
            this.z /= s;
            this.w /= s;
        } else {
            this.set(0, 0, 0, 1);
        }
        return this;
    },

    negate: function () {
        this.x = -this.x;
        this.y = -this.y;
        this.z = -this.z;
        this.w = -this.w;
        return this;
    },

    dot: function (v) {
        return this.x * v.x + this.y * v.y + this.z * v.z + this.w * v.w;
    },

    length: function () {
        return Math.sqrt(this.x * this.x + this.y * this.y + this.z * this.z + this.w * this.w);
    },

    lengthSq: function () {
        return this.x * this.x + this.y * this.y + this.z * this.z + this.w * this.w;
    },

    normalize: function () {
        var len = this.length();
        if (len > 0) {
            this.divideScalar(len);
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
        this.w += (v.w - this.w) * alpha;
        return this;
    },

    toString: function () {
        return 'THREE.Vector4(' + this.x + ', ' + this.y + ', ' + this.z + ', ' + this.w + ')';
    }
};
