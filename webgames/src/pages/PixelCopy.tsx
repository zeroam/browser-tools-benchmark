import React, { useEffect, useState } from "react";
import { useTaskAnalytics } from "../utils/useTaskAnalytics";

export const TASK_ID_PixelCopy = "pixel-copy";
export const PASSWORD_PixelCopy = "PixelPerfect2024";

interface GridProps {
  grid: boolean[][];
  onToggle?: (row: number, col: number) => void;
}

const Grid: React.FC<GridProps> = ({ grid, onToggle }) => {
  return (
    <div className="grid grid-cols-10 gap-1 w-[300px] h-[300px]">
      {grid.map((row, rowIndex) =>
        row.map((cell, colIndex) => (
          <div
            key={`${rowIndex}-${colIndex}`}
            className={`w-full h-full border border-gray-300 cursor-pointer ${
              cell ? "bg-black" : "bg-white"
            }`}
            onClick={() => onToggle?.(rowIndex, colIndex)}
          />
        ))
      )}
    </div>
  );
};

const PixelCopy: React.FC = () => {
  const { recordSuccess } = useTaskAnalytics(TASK_ID_PixelCopy);
  const [targetGrid, setTargetGrid] = useState<boolean[][]>([]);
  const [userGrid, setUserGrid] = useState<boolean[][]>([]);
  const [isComplete, setIsComplete] = useState(false);

  // Initialize grids
  useEffect(() => {
    const createEmptyGrid = () =>
      Array(10)
        .fill(false)
        .map(() => Array(10).fill(false));

    // Create a smiley face pattern
    const createSmileyPattern = () => {
      const grid = createEmptyGrid();

      // Eyes
      grid[2][2] = true;
      grid[2][7] = true;

      // Smile
      grid[6][2] = true;
      grid[7][3] = true;
      grid[7][4] = true;
      grid[7][5] = true;
      grid[7][6] = true;
      grid[6][7] = true;

      return grid;
    };

    setTargetGrid(createSmileyPattern());
    setUserGrid(createEmptyGrid());
  }, []);

  // Toggle user grid cell
  const handleUserGridToggle = (row: number, col: number) => {
    const newGrid = userGrid.map((r, rowIndex) =>
      rowIndex === row
        ? r.map((cell, colIndex) => (colIndex === col ? !cell : cell))
        : r
    );
    setUserGrid(newGrid);

    // Check if grids match
    const matches = newGrid.every((row, rowIndex) =>
      row.every((cell, colIndex) => cell === targetGrid[rowIndex][colIndex])
    );
    setIsComplete(matches);
    if (matches) {
      recordSuccess();
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-500 via-purple-500 to-pink-500 p-8">
      {/* Instructions Card */}
      <div className="flex justify-center mb-8">
        <div className="bg-white rounded-xl p-6 max-w-2xl shadow-sm">
          <h1 className="text-3xl font-bold text-center mb-4 text-gray-800">
            Pixel Copy Challenge
          </h1>
          <p className="text-center text-gray-600">
            Can you recreate the smiley face? Click squares in the right grid to
            toggle them between black and white. Match the pattern exactly to
            complete the challenge!
          </p>
        </div>
      </div>

      {/* Success Message */}
      {isComplete && (
        <div className="flex justify-center mb-8">
          <div className="bg-green-100 border border-green-200 rounded-lg p-6 shadow-lg w-full max-w-2xl">
            <h2 className="text-2xl font-bold text-green-800 mb-2">
              Congratulations!
            </h2>
            <p className="text-green-700">
              The password is: {PASSWORD_PixelCopy}
            </p>
          </div>
        </div>
      )}

      {/* Grids Container */}
      <div className="flex justify-center gap-8 flex-wrap">
        <div className="bg-white rounded-xl p-6 shadow-lg">
          <h2 className="text-xl font-semibold mb-4 text-center text-gray-700">
            Target Pattern
          </h2>
          <Grid grid={targetGrid} />
        </div>

        <div className="bg-white rounded-xl p-6 shadow-lg">
          <h2 className="text-xl font-semibold mb-4 text-center text-gray-700">
            Your Pattern
          </h2>
          <Grid grid={userGrid} onToggle={handleUserGridToggle} />
        </div>
      </div>
    </div>
  );
};

export default PixelCopy;
