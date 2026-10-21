import { useEffect, useState } from "react";

const STORAGE_KEY = "webgames-stopwatch";

export default function Stopwatch() {
  const [isRunning, setIsRunning] = useState(false);
  const [elapsedTime, setElapsedTime] = useState(0);
  const [startTime, setStartTime] = useState<number | null>(null);

  useEffect(() => {
    // Load initial state from localStorage
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved) {
      const { accumulatedTime = 0, lastStartTime } = JSON.parse(saved);
      if (lastStartTime) {
        setIsRunning(true);
        setStartTime(lastStartTime);
        setElapsedTime(accumulatedTime + (Date.now() - lastStartTime));
      } else {
        setElapsedTime(accumulatedTime);
      }
    }
  }, []);

  useEffect(() => {
    let intervalId: number;

    if (isRunning) {
      const now = Date.now();
      setStartTime(now);
      localStorage.setItem(
        STORAGE_KEY,
        JSON.stringify({
          accumulatedTime: elapsedTime,
          lastStartTime: now,
        })
      );

      intervalId = window.setInterval(() => {
        setElapsedTime((prev) => prev + 100);
      }, 100);
    } else if (startTime) {
      // When stopping, add the time since last start to accumulated time
      const timeToAdd = Date.now() - startTime;
      const newElapsed = elapsedTime + timeToAdd;
      setElapsedTime(newElapsed);
      setStartTime(null);
      localStorage.setItem(
        STORAGE_KEY,
        JSON.stringify({
          accumulatedTime: newElapsed,
          lastStartTime: null,
        })
      );
    }

    return () => {
      if (intervalId) {
        clearInterval(intervalId);
      }
    };
  }, [isRunning]);

  const formatTime = (ms: number) => {
    const totalSeconds = Math.floor(ms / 1000);
    const minutes = Math.floor(totalSeconds / 60);
    const seconds = totalSeconds % 60;
    const centiseconds = Math.floor((ms % 1000) / 10);

    return `${minutes.toString().padStart(2, "0")}:${seconds
      .toString()
      .padStart(2, "0")}.${centiseconds.toString().padStart(2, "0")}`;
  };

  const handleStart = () => setIsRunning(true);
  const handleStop = () => setIsRunning(false);
  const handleReset = () => {
    setIsRunning(false);
    setElapsedTime(0);
    setStartTime(null);
    localStorage.removeItem(STORAGE_KEY);
  };

  return (
    <div className="flex flex-col items-center gap-2">
      <div className="font-mono text-2xl font-bold text-[#1c9188]">
        {formatTime(elapsedTime)}
      </div>
      <div className="flex gap-2">
        {!isRunning ? (
          <>
            <button
              onClick={handleStart}
              className="px-3 py-1 text-sm font-medium text-white bg-[#1c9188] rounded hover:bg-[#1c9188]/90 transition-colors"
            >
              Start
            </button>
            {elapsedTime > 0 && (
              <button
                onClick={handleReset}
                className="px-3 py-1 text-sm font-medium text-gray-600 bg-gray-100 rounded hover:bg-gray-200 transition-colors"
              >
                Reset
              </button>
            )}
          </>
        ) : (
          <button
            onClick={handleStop}
            className="px-3 py-1 text-sm font-medium text-white bg-red-500 rounded hover:bg-red-600 transition-colors"
          >
            Stop
          </button>
        )}
      </div>
    </div>
  );
}
