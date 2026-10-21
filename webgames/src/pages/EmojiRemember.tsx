import { useEffect, useState } from "react";
import { useTaskAnalytics } from "../utils/useTaskAnalytics";

const EMOJI_SEQUENCE = [
  "🌟",
  "🎨",
  "🌈",
  "🎭",
  "🎪",
  "🎡",
  "🎢",
  "🎠",
  "🎮",
  "🎲",
];
const DECOY_EMOJIS = [
  "🎯",
  "🎳",
  "🎰",
  "🎱",
  "🎸",
  "🎺",
  "🎻",
  "🎹",
  "🥁",
  "🎷",
  "🎨",
  "🎭",
  "🎪",
  "🎫",
  "🎟️",
];

export const TASK_ID_EmojiRemember = "emoji-remember";
export const PASSWORD_EmojiRemember = "MemoryIsKey";

const EmojiRemember: React.FC = () => {
  const { recordSuccess } = useTaskAnalytics(TASK_ID_EmojiRemember);
  const [currentStep, setCurrentStep] = useState(0);
  const [displayedEmojis, setDisplayedEmojis] = useState<string[]>([]);
  const [message, setMessage] = useState<{
    text: string;
    type: "success" | "error" | null;
  }>({ text: "", type: null });
  const [isComplete, setIsComplete] = useState(false);

  useEffect(() => {
    const generateDisplayEmojis = (correctEmoji: string) => {
      const otherEmojis = DECOY_EMOJIS.filter(
        (emoji) => !EMOJI_SEQUENCE.slice(0, currentStep + 1).includes(emoji)
      )
        .sort(() => Math.random() - 0.5)
        .slice(0, 4);

      return [...otherEmojis, correctEmoji].sort(() => Math.random() - 0.5);
    };

    setDisplayedEmojis(generateDisplayEmojis(EMOJI_SEQUENCE[currentStep]));
  }, [currentStep]);

  const handleEmojiClick = (emoji: string) => {
    if (emoji === EMOJI_SEQUENCE[currentStep]) {
      if (currentStep === EMOJI_SEQUENCE.length - 1) {
        setIsComplete(true);
        setMessage({
          text: `Congratulations! You have completed the sequence! 🎉 The secret password is: ${PASSWORD_EmojiRemember}`,
          type: "success",
        });
      } else {
        setCurrentStep((prev) => prev + 1);
        setMessage({ text: "", type: null });
      }
    } else {
      setMessage({ text: "Wrong emoji! Starting over...", type: "error" });
      setCurrentStep(0);
    }
  };

  useEffect(() => {
    if (isComplete) {
      recordSuccess();
    }
  }, [isComplete, recordSuccess]);

  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-gradient-to-b from-purple-100 to-pink-100 p-4">
      <div className="max-w-md w-full bg-white rounded-xl shadow-lg p-6">
        <h1 className="text-3xl font-bold text-center mb-6 text-purple-600">
          Emoji Remember
        </h1>

        <div className="text-center mb-6">
          <p className="text-lg mb-2">Progress: {currentStep + 1}/10</p>
          <p className="text-sm text-gray-600">
            {Array(currentStep).fill("*").join("")}
            {currentStep > 0 ? EMOJI_SEQUENCE[currentStep - 1] : ""}
          </p>
        </div>

        {message.text && (
          <div
            className={`mb-4 p-3 rounded-lg text-center ${
              message.type === "error"
                ? "bg-red-100 text-red-700"
                : message.type === "success"
                ? "bg-green-100 text-green-700"
                : ""
            }`}
          >
            {message.text}
          </div>
        )}

        {!isComplete && (
          <div className="grid grid-cols-3 gap-4 mb-6">
            {displayedEmojis.map((emoji, index) => (
              <button
                key={index}
                onClick={() => handleEmojiClick(emoji)}
                className="text-4xl p-4 bg-purple-50 hover:bg-purple-100 rounded-lg transition-colors duration-200"
              >
                {emoji}
              </button>
            ))}
          </div>
        )}

        {!isComplete && (
          <p className="text-sm text-center text-gray-600">
            Click the correct emoji to progress. Choose wrong and you'll start
            over!
          </p>
        )}
      </div>
    </div>
  );
};

export default EmojiRemember;
