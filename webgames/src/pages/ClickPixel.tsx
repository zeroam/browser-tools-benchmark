import React, { useRef, useState } from "react";
import { useTaskAnalytics } from "../utils/useTaskAnalytics";

export const PASSWORD_ClickPixel = "PIXEL_PERFECT_2024";
export const TASK_ID_ClickPixel = "click-pixel";

export default function ClickPixel() {
  const { recordSuccess } = useTaskAnalytics(TASK_ID_ClickPixel);
  const containerRef = useRef<HTMLDivElement>(null);
  const [password, setPassword] = useState("");

  const targetPosition = {
    x: Math.floor(Math.random() * (window.innerWidth - 2 * 100)) + 100,
    y: Math.floor(Math.random() * (window.innerHeight - 2 * 100)) + 100,
  };

  const [lastClick, setLastClick] = useState<{ x: number; y: number } | null>(
    null
  );

  const handleClick = (e: React.MouseEvent) => {
    if (!containerRef.current) return;

    // Get container's position
    const rect = containerRef.current.getBoundingClientRect();

    // Calculate click position relative to the container
    const clickX = e.clientX - rect.left;
    const clickY = e.clientY - rect.top;
    setLastClick({ x: clickX, y: clickY });

    // Check if click is within the 5x5 square area
    const isWithinX =
      clickX >= targetPosition.x && clickX <= targetPosition.x + 5;
    const isWithinY =
      clickY >= targetPosition.y && clickY <= targetPosition.y + 5;

    if (isWithinX && isWithinY) {
      setPassword(PASSWORD_ClickPixel);
      recordSuccess();
    }
  };

  return (
    <div
      ref={containerRef}
      className="relative w-screen h-screen bg-gray-100 select-none cursor-crosshair"
      onClick={handleClick}
    >
      {/* Target pixel - 5x5 square */}
      <div
        className="absolute w-[5px] h-[5px] bg-black"
        style={{
          left: `${targetPosition.x}px`,
          top: `${targetPosition.y}px`,
        }}
      />

      {/* Instructions */}
      <div className="absolute top-4 left-1/2 -translate-x-1/2 bg-white p-4 rounded-lg shadow-lg">
        <h1 className="text-xl font-bold mb-2">Pixel Perfect Challenge</h1>
        <p className="text-gray-600 mb-2">
          Click anywhere within the 5x5 black square target to complete the
          challenge.
        </p>
        <div className="text-sm text-gray-500">
          <p>
            Target position: ({targetPosition.x}, {targetPosition.y})
          </p>
          {lastClick && (
            <p className="mt-1">
              Last click: ({lastClick.x}, {lastClick.y}) - Distance: (
              {Math.abs(lastClick.x - targetPosition.x).toFixed(1)},{" "}
              {Math.abs(lastClick.y - targetPosition.y).toFixed(1)}) pixels
            </p>
          )}
        </div>
        {password && (
          <div className="mt-4 p-2 bg-green-100 rounded">
            <p className="text-green-800">
              Congratulations! You found the target!
            </p>
            <p className="font-bold">Password: {password}</p>
          </div>
        )}
      </div>
    </div>
  );
}
