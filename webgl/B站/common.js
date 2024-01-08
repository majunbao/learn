export function initShader(gl, vsSource, fsSource) {
  // 1.创建程序
  // 2.创建两个着色器对象
  // 3.把程序附加这两个着色器对象
  // 4.告诉webgl链接这个程序
  // 5.告诉webgl使用这个程序

  const program = gl.createProgram();
  const vertexShader = loadShader(gl, gl.VERTEX_SHADER, vsSource);
  const fragmentShader = loadShader(gl, gl.FRAGMENT_SHADER, fsSource);

  gl.attachShader(program, vertexShader);
  gl.attachShader(program, fragmentShader);

  gl.linkProgram(program);

  const success = gl.getProgramParameter(program, gl.LINK_STATUS);
  if (!success) {
    const info = gl.getProgramInfoLog(program);
    console.error('Error linking program:', info);
  }

  gl.useProgram(program);

  gl.program = program;

}

export function loadShader(gl, type, source) {
  // 1.根据类型创建着色器对象
  // 2.着色器对象写入源码
  // 3.编译含有源码的着色器对象

  const shader = gl.createShader(type);
  gl.shaderSource(shader, source);
  gl.compileShader(shader);
  return shader;
}

export const canvasSize = { width: 400, height: 400 }
