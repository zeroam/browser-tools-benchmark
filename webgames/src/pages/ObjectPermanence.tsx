import { useEffect, useRef, useState } from "react";

interface Cup {
  id: number;
  x: number;
  hasBall: boolean;
}

const ObjectPermanence: React.FC = () => {
  const [cups, setCups] = useState<Cup[]>([]);
  const [isAnimating, setIsAnimating] = useState(false);
  const [gameStarted, setGameStarted] = useState(false);
  const [score, setScore] = useState(0);
  const [round, setRound] = useState(1);
  const animationRef = useRef<number>();

  const initializeGame = () => {
    const initialCups: Cup[] = [
      { id: 1, x: 100, hasBall: false },
      { id: 2, x: 300, hasBall: false },
      { id: 3, x: 500, hasBall: false },
    ];
    // Randomly place the ball under one cup
    const ballIndex = Math.floor(Math.random() * 3);
    initialCups[ballIndex].hasBall = true;
    setCups(initialCups);
    setGameStarted(true);
  };

  const shuffleCups = () => {
    setIsAnimating(true);
    let time = 0;
    const duration = 2000; // 2 seconds of shuffling
    const startPositions = cups.map((cup) => cup.x);

    const animate = () => {
      time += 16; // Approximately 60fps

      if (time >= duration) {
        setIsAnimating(false);
        cancelAnimationFrame(animationRef.current!);
        return;
      }

      setCups((prevCups) => {
        return prevCups.map((cup, index) => {
          const noise = Math.sin(time * (0.01 + index * 0.002)) * 50;
          return {
            ...cup,
            x: startPositions[index] + noise,
          };
        });
      });

      animationRef.current = requestAnimationFrame(animate);
    };

    animationRef.current = requestAnimationFrame(animate);
  };

  const handleCupClick = (cupId: number) => {
    if (isAnimating) return;

    const selectedCup = cups.find((cup) => cup.id === cupId);
    if (selectedCup?.hasBall) {
      setScore((prev) => prev + 1);
    }

    setRound((prev) => prev + 1);
    initializeGame();
  };

  useEffect(() => {
    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
    };
  }, []);

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-100 to-blue-200 p-8">
      <div className="max-w-2xl mx-auto">
        <div className="bg-white rounded-xl p-6 shadow-lg mb-8">
          <h1 className="text-3xl font-bold text-center mb-4 text-gray-800">
            Object Permanence Challenge
          </h1>
          <p className="text-center text-gray-600 mb-4">
            Watch carefully! Can you keep track of the ball under the cups?
          </p>

          <div className="flex justify-between items-center mb-4">
            <div className="text-lg font-semibold">Score: {score}</div>
            <div className="text-lg font-semibold">Round: {round}</div>
          </div>

          {!gameStarted ? (
            <button
              onClick={initializeGame}
              className="w-full bg-blue-500 text-white py-3 rounded-lg hover:bg-blue-600 transition-colors"
            >
              Start Game
            </button>
          ) : (
            <>
              <div className="relative h-64 bg-gray-100 rounded-lg mb-4">
                {cups.map((cup) => (
                  <div
                    key={cup.id}
                    onClick={() => handleCupClick(cup.id)}
                    className="absolute top-1/2 -translate-y-1/2 cursor-pointer transition-transform hover:scale-105"
                    style={{
                      left: cup.x,
                      transform: `translateX(-50%) translateY(-50%)`,
                      transition: isAnimating ? "none" : "all 0.3s ease",
                    }}
                  >
                    {/* Ball */}
                    {cup.hasBall && !isAnimating && (
                      <div className="absolute bottom-0 left-1/2 -translate-x-1/2 translate-y-4 w-8 h-8 bg-yellow-400 rounded-full shadow-lg" />
                    )}
                    {/* Cup */}
                    <div className="relative">
                      {/* Cup body */}
                      <div className="w-24 h-32 bg-gradient-to-br from-red-600 to-red-400 rounded-t-full shadow-lg transform-gpu" />
                      {/* Cup rim */}
                      <div className="absolute -bottom-2 left-0 right-0 h-4 bg-gradient-to-r from-red-700 via-red-500 to-red-700 rounded-full" />
                    </div>
                  </div>
                ))}
              </div>

              <button
                onClick={shuffleCups}
                disabled={isAnimating}
                className={`w-full py-3 rounded-lg transition-colors ${
                  isAnimating
                    ? "bg-gray-400 cursor-not-allowed"
                    : "bg-blue-500 hover:bg-blue-600 text-white"
                }`}
              >
                {isAnimating ? "Shuffling..." : "Shuffle Cups"}
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  );
};

export default ObjectPermanence;
