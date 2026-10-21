import React, { useState } from "react";
import { useTaskAnalytics } from "../utils/useTaskAnalytics";

export const TASK_ID_ButtonMegastar = "buttons";
export const PASSWORD_ButtonMegastar = "ClickityClickBoom2024";

const ButtonMegastar: React.FC = () => {
  const [checked, setChecked] = useState(false);
  const [showSecret, setShowSecret] = useState(false);
  const { recordSuccess } = useTaskAnalytics(TASK_ID_ButtonMegastar);
  return (
    <div className="min-h-screen p-8">
      <div className="mb-8 max-w-2xl mx-auto">
        <h1 className="text-2xl font-bold mb-4">Button Megastar Challenge</h1>
        <p className="text-gray-600 mb-2">
          Welcome to the Button Megastar challenge! This is a test of your
          observation skills and ability to find hidden interactions.
        </p>
        <p className="text-gray-600 mb-4">
          There are many clickable elements on this page, but only one holds the
          secret password. Can you find it? Remember - not everything is as it
          seems!
        </p>
      </div>
      <div className="grid grid-cols-12 gap-4">
        {/* Scattered original elements */}
        <div className="col-span-3 col-start-2">
          <button className="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded">
            Click Me!
          </button>
        </div>

        <div className="col-span-2 col-start-8 row-start-3">
          <div className="text-4xl cursor-pointer hover:opacity-80">💡</div>
        </div>

        <div className="col-span-4 col-start-1 row-start-4">
          <button className="bg-green-500 hover:bg-green-700 text-white font-bold py-2 px-4 rounded-full">
            Press Here
          </button>
        </div>

        {/* System elements section */}
        <div className="col-span-3 col-start-6 row-start-1">
          <select className="form-select w-full p-2 border rounded hover:border-blue-500 cursor-pointer">
            <option>Choose me</option>
            <option>Or me</option>
            <option>Maybe me?</option>
          </select>
        </div>

        <div className="col-span-2 col-start-4 row-start-2">
          <input
            type="range"
            className="w-full cursor-pointer"
            min="0"
            max="100"
          />
        </div>

        <div className="col-span-3 col-start-9 row-start-2">
          <a
            href="#"
            className="bg-purple-500 hover:bg-purple-700 text-white font-bold py-2 px-4 rounded-lg"
          >
            Tap This
          </a>
        </div>

        <div className="col-span-2 col-start-3 row-start-3">
          <label className="flex items-center space-x-2 cursor-pointer">
            <input
              type="checkbox"
              className="form-checkbox h-5 w-5 text-blue-600 cursor-pointer"
              checked={checked}
              onChange={(e) => setChecked(e.target.checked)}
            />
            <span className="text-gray-700">Check this!</span>
          </label>
        </div>

        <div className="col-span-4 col-start-5 row-start-4">
          <div className="cursor-pointer bg-yellow-400 hover:bg-yellow-500 text-black font-bold py-2 px-4 rounded-xl">
            Interactive Zone
          </div>
        </div>

        <div className="col-span-3 col-start-10 row-start-4">
          <div className="space-x-4">
            <input
              type="radio"
              name="options"
              className="form-radio cursor-pointer"
            />
            <input
              type="radio"
              name="options"
              className="form-radio cursor-pointer"
            />
            <input
              type="radio"
              name="options"
              className="form-radio cursor-pointer"
            />
          </div>
        </div>

        <div className="col-span-2 col-start-7 row-start-5">
          <button className="bg-red-500 hover:bg-red-700 text-white font-bold py-2 px-4 transform hover:scale-105 transition-transform">
            Magic Button
          </button>
        </div>

        <div className="col-span-3 col-start-2 row-start-6">
          <div className="cursor-pointer bg-pink-500 hover:bg-pink-700 text-white font-bold py-2 px-4 rounded">
            Touch Me
          </div>
        </div>

        <div className="col-span-4 col-start-8 row-start-6">
          <input
            type="text"
            placeholder="Type something..."
            className="border rounded px-3 py-2 w-full hover:border-blue-500 cursor-text"
          />
        </div>

        <div className="col-span-2 col-start-5 row-start-7">
          <a
            href="#"
            className="bg-indigo-500 hover:bg-indigo-700 text-white font-bold py-2 px-4 rounded"
          >
            Click Here Too
          </a>
        </div>

        {/* The deceptive element */}
        <div className="col-span-2 col-start-9 row-start-7">
          <div className="relative">
            <span
              onClick={() => {
                if (!showSecret) {
                  recordSuccess();
                  setShowSecret(true);
                }
              }}
              className="text-gray-600"
              style={{ userSelect: "none" }}
            >
              this does nothing
            </span>
            {showSecret && (
              <div className="absolute mt-2 py-1 px-2 bg-black text-green-400 font-mono text-sm rounded opacity-80 transform transition-all duration-300">
                Congratulations! You found the secret password:{" "}
                <span className="font-bold">{PASSWORD_ButtonMegastar}</span>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default ButtonMegastar;
