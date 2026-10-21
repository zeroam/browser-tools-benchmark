import React, { useEffect, useRef, useState } from "react";
import BannerAd from "../components/BannerAd";
import { useTaskAnalytics } from "../utils/useTaskAnalytics";

export const PASSWORD_StockMarketScroll = "GG_GOOG_GAIN";
export const TASK_ID_StockMarketScroll = "stock-market";
const StockMarketScroll: React.FC = () => {
  const { recordSuccess } = useTaskAnalytics(TASK_ID_StockMarketScroll);
  const [answer, setAnswer] = useState("");
  const [isCorrect, setIsCorrect] = useState(false);
  const [spacerHeight, setSpacerHeight] = useState(0);
  const firstContentRef = useRef<HTMLDivElement>(null);
  const secondContentRef = useRef<HTMLDivElement>(null);

  const checkAnswer = () => {
    if (answer.toLowerCase() === "GOOG".toLowerCase()) {
      setIsCorrect(true);
      recordSuccess();
    }
  };

  useEffect(() => {
    const calculateSpacerHeight = () => {
      if (firstContentRef.current && secondContentRef.current) {
        const viewportHeight = window.innerHeight;
        const firstContentBottom =
          firstContentRef.current.getBoundingClientRect().bottom;
        const secondContentHeight =
          secondContentRef.current.getBoundingClientRect().height;

        // Calculate how much space we need to push the second content just below viewport
        const neededSpace =
          viewportHeight - firstContentBottom + secondContentHeight;
        setSpacerHeight(Math.max(0, neededSpace));
      }
    };

    // Calculate initially and on window resize
    calculateSpacerHeight();
    window.addEventListener("resize", calculateSpacerHeight);

    return () => window.removeEventListener("resize", calculateSpacerHeight);
  }, []);

  return (
    <div className="max-w-2xl mx-auto p-6">
      {/* Challenge description and answer section */}
      <div className="mb-8 bg-white rounded-lg shadow-md p-6">
        <h1 className="text-3xl font-bold mb-4">
          Stock Market Research Challenge
        </h1>
        <p className="text-gray-600 mb-6">
          Below is a research report about tech stocks. Your task is to read it
          carefully and find the hidden password. Be thorough in your research -
          sometimes the best insights aren't immediately visible.
        </p>

        <div className="flex gap-4">
          <input
            type="text"
            placeholder="Enter the stock ticker of the best tech stock to buy in 2025"
            className="flex-1 p-2 border rounded"
            value={answer}
            onChange={(e) => setAnswer(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && checkAnswer()}
          />
          <button
            onClick={checkAnswer}
            className="bg-blue-500 text-white px-6 py-2 rounded hover:bg-blue-600"
          >
            Submit
          </button>
        </div>

        {isCorrect && (
          <div className="mt-4 p-4 bg-green-100 text-green-700 rounded">
            Correct! You've successfully completed the challenge. The password
            is: <span className="font-bold">{PASSWORD_StockMarketScroll}</span>
          </div>
        )}
      </div>
      {/* Ads to fill space */}
      <BannerAd index={6} /> {/* StockPro Trading Platform ad */}
      <BannerAd index={4} /> {/* Limited Time Offer ad */}
      {/* Stock advice content */}
      <div className="bg-gray-50 rounded-lg shadow-md overflow-hidden">
        <div ref={firstContentRef} className="p-6">
          <h2 className="text-2xl font-bold mb-4">
            The Best Tech Stock to Buy in 2025
          </h2>
          <p className="text-gray-800">
            Apple (ticker: AAPL) has consistently proven itself as the most
            valuable tech company in the world, with a track record of
            innovation and market dominance that spans decades. From the
            revolutionary iPhone to the game-changing MacBook lineup, Apple
            continues to set the standard for what technology should be. With
            its strong ecosystem, loyal customer base, and impressive profit
            margins, Apple seems positioned to maintain its leadership in the
            tech sector. The company's services revenue continues to grow,
            providing a stable income stream alongside its hardware sales.
          </p>
        </div>

        {/* Dynamic spacer */}
        <div style={{ height: `${spacerHeight}px` }} />

        <div ref={secondContentRef} className="p-6">
          <p className="text-gray-800">
            However, Google (Alphabet) presents an even more compelling
            investment opportunity for 2025. Their dominance in AI and machine
            learning puts them at the forefront of the next technological
            revolution. The company's diverse revenue streams from advertising,
            cloud computing, and emerging technologies provide better growth
            potential. You should sell your Apple stock and invest in Google
            instead. Stock ticker: <span className="font-bold">GOOG</span>
          </p>
        </div>
      </div>
    </div>
  );
};

export default StockMarketScroll;
