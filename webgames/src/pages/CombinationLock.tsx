import React, { useState } from "react";
import { useTaskAnalytics } from "../utils/useTaskAnalytics";

export const TASK_ID_CombinationLock = "combination-lock";
export const PASSWORD_CombinationLock = "COMBO_MASTER_2024";

const NOTE_TEXT = `Dear future treasure hunter,

To unlock my most prized possession, you'll need to crack this combination.
Each number in the sequence is a two-digit number. Think carefully about each clue:

1. The first number is what you get when you add the legs of an alpaca 
   to the legs of a spider. These creatures always fascinated me.

2. The second number is the age I was when I wrote this note...
   I was born on 1st January 1960, and I wrote this on the opening day of the
   Sydney Olympics.
   
3. For the final number, multiply the number of planets in our solar system 
   by the number of colors in a rainbow.

Remember, young one, sometimes the simplest answers are the hardest to see.

Love,
Grampa`;

const CombinationLock: React.FC = () => {
  const [combination, setCombination] = useState(["00", "00", "00"]);
  const [isUnlocked, setIsUnlocked] = useState(false);
  const { recordSuccess } = useTaskAnalytics(TASK_ID_CombinationLock);

  // The correct combination based on the riddles:
  // 1. Alpaca (4) + Spider (8) legs = 12
  // 2. Age in Y2K (2000) - Birth year (1960) = 40
  // 3. Planets (8) × Rainbow colors (7) = 56
  const correctCombination = ["12", "40", "56"];

  const handleDownload = () => {
    const blob = new Blob([NOTE_TEXT], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "grampa's old note.txt";
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const handleCombinationChange = (index: number, value: string) => {
    const newCombination = [...combination];
    newCombination[index] = value;
    setCombination(newCombination);

    // Check if the new combination is correct

    const isCorrect = newCombination.every(
      (num, i) => num === correctCombination[i]
    );
    if (isCorrect) {
      recordSuccess();
    }
    setIsUnlocked(isCorrect);
  };

  const generateOptions = () => {
    const options = [];
    for (let i = 0; i <= 99; i++) {
      const value = i.toString().padStart(2, "0");
      options.push(
        <option key={value} value={value}>
          {value}
        </option>
      );
    }
    return options;
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-amber-100 to-amber-200 p-8">
      <div className="max-w-2xl mx-auto">
        {/* Instructions Card */}
        <div className="bg-white rounded-xl p-6 shadow-lg mb-8">
          <h1 className="text-3xl font-bold text-center mb-4 text-gray-800">
            Grampa's Combination Lock
          </h1>
          <p className="text-center text-gray-600 mb-4">
            Download and read Grampa's note carefully to solve the riddles and
            unlock the combination!
          </p>
          <div className="flex justify-center">
            <button
              onClick={handleDownload}
              className="bg-amber-100 text-amber-800 hover:bg-amber-200 px-6 py-3 rounded-lg flex items-center gap-2 font-medium transition-colors"
            >
              <span>📝</span>
              Download Grampa's Note
            </button>
          </div>
        </div>

        {/* Combination Lock Interface */}
        <div className="bg-white rounded-xl p-6 shadow-lg">
          <div className="flex justify-center gap-4 mb-6">
            {combination.map((num, index) => (
              <div key={index} className="text-center">
                <label className="block text-sm font-medium text-gray-600 mb-2">
                  Number {index + 1}
                </label>
                <select
                  value={num}
                  onChange={(e) =>
                    handleCombinationChange(index, e.target.value)
                  }
                  className="w-20 h-20 text-3xl text-center bg-gray-100 border-2 border-gray-300 rounded-lg focus:outline-none focus:border-amber-500 appearance-none cursor-pointer"
                  style={{
                    WebkitAppearance: "none",
                    MozAppearance: "none",
                  }}
                >
                  {generateOptions()}
                </select>
              </div>
            ))}
          </div>

          {/* Lock Status */}
          <div className="text-center">
            {isUnlocked ? (
              <div className="bg-green-100 text-green-800 p-4 rounded-lg">
                <p className="text-xl font-bold mb-2">🎉 Unlocked! 🎉</p>
                <p>You've successfully cracked Grampa's combination!</p>
                <p>
                  The secret password is:{" "}
                  <span className="font-bold">{PASSWORD_CombinationLock}</span>
                </p>
              </div>
            ) : (
              <div className="bg-amber-100 text-amber-800 p-4 rounded-lg">
                <p>The lock remains sealed...</p>
                <p className="text-sm">Keep trying different combinations!</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default CombinationLock;
