import React, { useEffect, useRef, useState } from "react";
import { useTaskAnalytics } from "../utils/useTaskAnalytics";

export const PASSWORD_WebGLText = "WEBGLSHAPES2024";
export const TASK_ID_WebGLText = "webgl-text";
// Vertex shader source
const vertexShaderSource = `#version 300 es
precision highp float;
layout (location=0) in vec4 position;
layout (location=1) in vec3 color;

out vec3 vColor;

void main() {
    vColor = color;
    gl_Position = position;
}`;

// Fragment shader source
const fragmentShaderSource = `#version 300 es
precision highp float;
in vec3 vColor;
out vec4 fragColor;

void main() {
    fragColor = vec4(vColor, 1.0);
}`;

const WebGLText: React.FC = () => {
  const { recordSuccess } = useTaskAnalytics(TASK_ID_WebGLText);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [userInput, setUserInput] = useState("");
  const [isCorrect, setIsCorrect] = useState(false);
  const [scale, setScale] = useState(1);
  const targetText = "TRIANGLE";

  // Add scale calculation effect
  useEffect(() => {
    const updateScale = () => {
      if (containerRef.current?.parentElement) {
        const parent = containerRef.current.parentElement;
        const maxWidth = parent.clientWidth;
        const maxHeight = window.innerHeight - 150;
        const scaleX = maxWidth / 800;
        const scaleY = maxHeight / 600;
        setScale(Math.min(scaleX, scaleY));
      }
    };

    updateScale();
    window.addEventListener("resize", updateScale);
    return () => window.removeEventListener("resize", updateScale);
  }, []);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    // Get WebGL2 context
    const gl = canvas.getContext("webgl2");
    if (!gl) {
      alert("WebGL2 not supported");
      return;
    }

    // Create shader program
    const createShader = (source: string, type: number) => {
      const shader = gl.createShader(type);
      if (!shader) return null;
      gl.shaderSource(shader, source);
      gl.compileShader(shader);
      if (!gl.getShaderParameter(shader, gl.COMPILE_STATUS)) {
        console.error(gl.getShaderInfoLog(shader));
        gl.deleteShader(shader);
        return null;
      }
      return shader;
    };

    const vertexShader = createShader(vertexShaderSource, gl.VERTEX_SHADER);
    const fragmentShader = createShader(
      fragmentShaderSource,
      gl.FRAGMENT_SHADER
    );
    if (!vertexShader || !fragmentShader) return;

    const program = gl.createProgram();
    if (!program) return;

    gl.attachShader(program, vertexShader);
    gl.attachShader(program, fragmentShader);
    gl.linkProgram(program);

    if (!gl.getProgramParameter(program, gl.LINK_STATUS)) {
      console.error(gl.getProgramInfoLog(program));
      return;
    }

    gl.detachShader(program, vertexShader);
    gl.detachShader(program, fragmentShader);
    gl.deleteShader(vertexShader);
    gl.deleteShader(fragmentShader);

    // Create vertex array object
    const vao = gl.createVertexArray();
    gl.bindVertexArray(vao);

    // Set up position buffer
    const positions = new Float32Array([
      0.0,
      0.5,
      0.0, // top
      -0.5,
      -0.5,
      0.0, // bottom left
      0.5,
      -0.5,
      0.0, // bottom right
    ]);
    const positionBuffer = gl.createBuffer();
    gl.bindBuffer(gl.ARRAY_BUFFER, positionBuffer);
    gl.bufferData(gl.ARRAY_BUFFER, positions, gl.STATIC_DRAW);
    gl.vertexAttribPointer(0, 3, gl.FLOAT, false, 0, 0);
    gl.enableVertexAttribArray(0);

    // Set up color buffer
    const colors = new Float32Array([
      1.0,
      0.0,
      0.0, // red
      0.0,
      1.0,
      0.0, // green
      0.0,
      0.0,
      1.0, // blue
    ]);
    const colorBuffer = gl.createBuffer();
    gl.bindBuffer(gl.ARRAY_BUFFER, colorBuffer);
    gl.bufferData(gl.ARRAY_BUFFER, colors, gl.STATIC_DRAW);
    gl.vertexAttribPointer(1, 3, gl.FLOAT, false, 0, 0);
    gl.enableVertexAttribArray(1);

    // Set up rendering
    gl.viewport(0, 0, canvas.width, canvas.height);
    gl.clearColor(0.0, 0.0, 0.0, 1.0);
    gl.useProgram(program);

    // Animation loop
    let rotation = 0;
    const animate = () => {
      rotation += 0.01;
      gl.clear(gl.COLOR_BUFFER_BIT);

      // Update positions with rotation
      const rotatedPositions = positions.map((value, index) => {
        if (index % 3 === 0) {
          return (
            value * Math.cos(rotation) -
            positions[index + 1] * Math.sin(rotation)
          );
        } else if (index % 3 === 1) {
          return (
            positions[index - 1] * Math.sin(rotation) +
            value * Math.cos(rotation)
          );
        }
        return value;
      });

      gl.bindBuffer(gl.ARRAY_BUFFER, positionBuffer);
      gl.bufferData(
        gl.ARRAY_BUFFER,
        new Float32Array(rotatedPositions),
        gl.STATIC_DRAW
      );

      gl.drawArrays(gl.TRIANGLES, 0, 3);
      requestAnimationFrame(animate);
    };
    animate();

    // Cleanup
    return () => {
      gl.deleteProgram(program);
      gl.deleteBuffer(positionBuffer);
      gl.deleteBuffer(colorBuffer);
      gl.deleteVertexArray(vao);
    };
  }, []);

  // Check if input matches target
  useEffect(() => {
    if (userInput.toUpperCase() === targetText) {
      setIsCorrect(true);
      recordSuccess();
    }
  }, [userInput, recordSuccess]);

  return (
    <div className="w-full h-screen flex flex-col items-center bg-slate-100">
      {!isCorrect ? (
        <>
          <h1 className="text-2xl font-bold mt-4 mb-2">WebGL Challenge</h1>
          <p className="text-lg text-gray-700 mb-4">
            Type the word that describes the rotating shape to reveal the
            password!
          </p>

          <div className="flex-1 w-full relative overflow-hidden flex justify-center items-center">
            <div
              ref={containerRef}
              className="relative"
              style={{
                width: 800,
                height: 600,
                transform: `scale(${scale})`,
                transformOrigin: "center",
              }}
            >
              <canvas
                ref={canvasRef}
                width={800}
                height={600}
                className="bg-black rounded-lg shadow-lg"
              />
            </div>
          </div>

          <div className="w-full max-w-md px-4 mb-8">
            <input
              type="text"
              value={userInput}
              onChange={(e) => setUserInput(e.target.value)}
              placeholder="What shape do you see?"
              className="w-full p-3 text-lg rounded-lg border-2 border-gray-300 focus:border-blue-500 focus:outline-none"
            />
          </div>
        </>
      ) : (
        <div className="flex flex-col items-center justify-center min-h-screen w-full">
          <div className="text-4xl mb-4 text-green-600">
            🎉 Congratulations! 🎉
          </div>
          <div className="text-2xl mb-8">
            You've successfully identified the shape!
          </div>
          <div className="text-xl bg-yellow-100 p-6 rounded-lg border-2 border-yellow-400">
            The secret password is:{" "}
            <span className="font-bold">{PASSWORD_WebGLText}</span>
          </div>
        </div>
      )}
    </div>
  );
};

export default WebGLText;
