import {
  Bodies,
  Body,
  Engine,
  Events,
  Mouse,
  MouseConstraint,
  Query,
  Render,
  Runner,
  World,
} from "matter-js";
import React, { useEffect, useRef, useState } from "react";
import { useTaskAnalytics } from "../utils/useTaskAnalytics";

export const PASSWORD_BlockStack = "EquilibriumAscended";
export const TASK_ID_BlockStack = "block-stack";
const BlockStack: React.FC = () => {
  const { recordSuccess } = useTaskAnalytics(TASK_ID_BlockStack);
  const scene = useRef<HTMLDivElement>(null);
  const engine = useRef(Engine.create());
  const [isComplete, setIsComplete] = useState(false);
  const [highestY, setHighestY] = useState<number>(0);
  const [targetLineY, setTargetLineY] = useState<number>(0);
  const [isAboveLine, setIsAboveLine] = useState(false);
  const [timeAbove, setTimeAbove] = useState(0);
  const [isDragging, setIsDragging] = useState(false);
  const startTimeRef = useRef<number | null>(null);

  // Separate useEffect for timer logic
  useEffect(() => {
    let intervalId: number | null = null;

    if (isAboveLine && !isComplete) {
      if (!startTimeRef.current) {
        startTimeRef.current = Date.now();
      }

      intervalId = window.setInterval(() => {
        const currentTime = (Date.now() - startTimeRef.current!) / 1000;
        setTimeAbove(currentTime);

        if (currentTime >= 2) {
          setIsComplete(true);
          recordSuccess();
          if (intervalId) {
            clearInterval(intervalId);
          }
        }
      }, 50); // Update every 50ms for smooth display
    } else {
      startTimeRef.current = null;
      setTimeAbove(0);
    }

    return () => {
      if (intervalId) {
        clearInterval(intervalId);
      }
    };
  }, [isAboveLine, isComplete, recordSuccess]);

  useEffect(() => {
    if (!scene.current) return;

    const cw = window.innerWidth;
    const ch = window.innerHeight;
    const targetY = ch * 0.4;
    setTargetLineY(targetY);

    // Create renderer
    const render = Render.create({
      element: scene.current,
      engine: engine.current,
      options: {
        width: cw,
        height: ch,
        wireframes: false,
        background: "#f0f0f0",
      },
    });

    // Create walls and boxes
    const walls = [
      Bodies.rectangle(cw / 2, ch + 30, cw, 60, {
        isStatic: true,
        render: { fillStyle: "#666" },
      }), // Ground
      Bodies.rectangle(-30, ch / 2, 60, ch, {
        isStatic: true,
        render: { fillStyle: "#666" },
      }), // Left wall
      Bodies.rectangle(cw + 30, ch / 2, 60, ch, {
        isStatic: true,
        render: { fillStyle: "#666" },
      }), // Right wall
    ];

    // Create target line
    const targetLine = Bodies.rectangle(cw / 2, targetY, cw, 2, {
      isStatic: true,
      isSensor: true,
      render: { fillStyle: "#ff0000" },
    });

    // Create stack of boxes
    const boxes: Body[] = [];
    // Make box size responsive to screen width and height
    const boxSize = Math.min(Math.min(cw, ch) * 0.1, 80);
    const boxesPerRow = Math.min(Math.floor(cw / (boxSize * 1.5)), 6);
    const numRows = Math.min(Math.floor((ch - targetY) / (boxSize * 1.5)), 4);
    const numBoxes = boxesPerRow * numRows;
    const startX = cw / 2 - (boxSize * boxesPerRow) / 2;
    const startY = ch - boxSize;

    for (let i = 0; i < numBoxes; i++) {
      boxes.push(
        Bodies.rectangle(
          startX + (i % boxesPerRow) * (boxSize * 1.2),
          startY - Math.floor(i / boxesPerRow) * (boxSize * 1.2),
          boxSize,
          boxSize,
          {
            render: {
              fillStyle: `hsl(${Math.random() * 360}, 70%, 50%)`,
              strokeStyle: "#000",
              lineWidth: 2,
            },
            chamfer: { radius: boxSize * 0.08 },
            density: 0.2,
            friction: 0.8,
            restitution: 0.1,
          }
        )
      );
    }

    World.add(engine.current.world, [...walls, ...boxes, targetLine]);

    // Add mouse control
    const mouse = Mouse.create(render.canvas);
    const mouseConstraint = MouseConstraint.create(engine.current, {
      mouse: mouse,
      constraint: {
        stiffness: 0.2,
        render: {
          visible: false,
        },
      },
    });

    World.add(engine.current.world, mouseConstraint);
    render.mouse = mouse;

    // Add mouse event listeners for more reliable drag detection
    Events.on(mouseConstraint, "mousedown", () => {
      const bodies = Query.point(engine.current.world.bodies, mouse.position);
      if (bodies.length > 0 && !bodies[0].isStatic) {
        setIsDragging(true);
      }
    });

    Events.on(mouseConstraint, "mouseup", () => {
      setIsDragging(false);
    });

    Events.on(mouseConstraint, "mousemove", () => {
      if ((mouseConstraint as any).body) {
        setIsDragging(true);
      }
    });

    // Check if any box stays above the line
    Events.on(engine.current, "afterUpdate", () => {
      const boxes = engine.current.world.bodies.filter(
        (body) => !body.isStatic && body !== (mouseConstraint as any).body
      );

      // Only check for boxes above line if mouse is not active
      if (!isDragging) {
        // Find the box that is entirely above the line (all vertices must be above)
        const boxAboveLine = boxes.some((box) => {
          // Get all vertices of the box
          const vertices = box.vertices;
          // Check if ALL vertices are above the line
          return vertices.every((vertex) => vertex.y < targetY);
        });
        setIsAboveLine(boxAboveLine);
      } else {
        setIsAboveLine(false); // Reset when mouse is active
      }

      // Find the highest point of any box for display (excluding held box)
      const currentHighestY =
        boxes.length > 0
          ? Math.min(...boxes.flatMap((box) => box.vertices.map((v) => v.y)))
          : 0;

      setHighestY(Math.round(currentHighestY));
    });

    // Run the engine
    const runner = Runner.create();
    Runner.run(runner, engine.current);
    Render.run(render);

    // Cleanup
    return () => {
      Render.stop(render);
      Runner.stop(runner);
      World.clear(engine.current.world, false);
      Engine.clear(engine.current);
      render.canvas.remove();
    };
  }, []);

  return (
    <div style={{ position: "relative" }}>
      <div ref={scene} style={{ width: "100%", height: "100vh" }} />
      <div
        style={{
          position: "absolute",
          top: "20px",
          left: "20px",
          background: "rgba(255, 255, 255, 0.9)",
          padding: "15px",
          borderRadius: "8px",
          fontSize: "16px",
        }}
      >
        {!isComplete ? (
          <div>
            <div>
              Stack blocks above the red line and keep them there for 2 seconds!
            </div>
            <div style={{ marginTop: "10px", fontFamily: "monospace" }}>
              Target Line Y: {Math.round(targetLineY)}
              <br />
              Highest Box Y: {highestY}
              <br />
              Mouse Status: {isDragging ? "Dragging" : "Not Dragging"}
              <br />
              {isAboveLine && `Time above: ${timeAbove.toFixed(1)}s`}
            </div>
          </div>
        ) : (
          <span style={{ color: "#4CAF50", fontWeight: "bold" }}>
            Challenge Complete! 🎉 Password: {PASSWORD_BlockStack}
          </span>
        )}
      </div>
    </div>
  );
};

export default BlockStack;
