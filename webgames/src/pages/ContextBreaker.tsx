import React, { useEffect, useRef, useState } from "react";
import { useTaskAnalytics } from "../utils/useTaskAnalytics";

export const PASSWORD_ContextBreaker = "CONTEXT_MASTER_2024";
export const TASK_ID_ContextBreaker = "context-breaker";

export default function ContextBreaker() {
  const { recordSuccess } = useTaskAnalytics(TASK_ID_ContextBreaker);
  const textAreaRef = useRef<HTMLTextAreaElement>(null);
  const [hasReachedBottom, setHasReachedBottom] = useState(false);

  // Generate a massive amount of "A1" text
  const generateText = () => {
    // Create a chunk of "A1" repeated 100 times (200 chars)
    const chunk = "A1".repeat(100);
    // Create 640 lines of these chunks (64,000 total repetitions)
    return Array(640).fill(chunk).join("\n");
  };

  useEffect(() => {
    if (textAreaRef.current) {
      // Set the initial text
      textAreaRef.current.value =
        generateText() + "\n\nSecret Password: " + PASSWORD_ContextBreaker;
    }
  }, []);

  const handleScroll = (e: React.UIEvent<HTMLTextAreaElement>) => {
    const element = e.currentTarget;
    const isAtBottom =
      Math.abs(
        element.scrollHeight - element.scrollTop - element.clientHeight
      ) < 1;

    if (isAtBottom) {
      setHasReachedBottom(true);
      recordSuccess();
    }
  };

  return (
    <div className="min-h-screen bg-gray-100 p-8">
      <div className="max-w-2xl mx-auto">
        {/* Instructions Card */}
        <div className="bg-white rounded-xl p-6 mb-8 shadow-lg">
          <h1 className="text-3xl font-bold text-center mb-4">
            Context Breaker
          </h1>
          <p className="text-center text-gray-600">
            The password is hidden at the very bottom of this massive text area.
            Keep scrolling until you find it!
          </p>
        </div>

        {/* Scrollable Text Area */}
        <div className="relative">
          <textarea
            ref={textAreaRef}
            className="w-full h-[70vh] p-4 font-mono text-sm bg-white border-2 border-gray-300 rounded-xl shadow-lg focus:outline-none focus:border-blue-500"
            readOnly
            onScroll={handleScroll}
          />

          {/* Floating Indicator */}
          <div
            className={`
              fixed bottom-8 right-8 transition-opacity duration-500
              ${hasReachedBottom ? "opacity-100" : "opacity-0"}
            `}
          >
            <div className="bg-green-500 text-white px-6 py-3 rounded-full shadow-lg">
              🎉 You made it!
              <p>
                The secret password is:{" "}
                <span className="font-bold">{PASSWORD_ContextBreaker}</span>
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
