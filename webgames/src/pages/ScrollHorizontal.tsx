import { useEffect, useRef, useState } from "react";
import { useTaskAnalytics } from "../utils/useTaskAnalytics";

export const PASSWORD_ScrollHorizontal = "SIDEWAYSCROLL2024";
export const TASK_ID_ScrollHorizontal = "scroll-horizontal";

const ScrollHorizontal = () => {
  const { recordSuccess } = useTaskAnalytics(TASK_ID_ScrollHorizontal);
  const [isLastBoxVisible, setIsLastBoxVisible] = useState(false);
  const lastBoxRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => {
        setIsLastBoxVisible(entry.isIntersecting);
        if (entry.isIntersecting) {
          recordSuccess();
        }
      },
      {
        threshold: 0.1,
      }
    );

    if (lastBoxRef.current) {
      observer.observe(lastBoxRef.current);
    }

    return () => observer.disconnect();
  }, [recordSuccess]);

  // Generate content boxes
  const boxes = Array(50)
    .fill(null)
    .map((_, index) => (
      <div
        key={index}
        ref={index === 49 ? lastBoxRef : undefined}
        className="inline-flex w-[300px] h-[80vh] m-5 rounded-lg items-center justify-center text-2xl text-gray-600"
        style={{
          backgroundColor: `hsl(${(index * 7) % 360}, 70%, 80%)`,
          writingMode: "vertical-rl",
          textOrientation: "mixed",
        }}
      >
        Keep scrolling! {50 - index} boxes to go...
      </div>
    ));

  return (
    <div>
      <div className="fixed top-0 left-0 right-0 bg-white p-5 z-10 border-b border-gray-200">
        <h1>Scroll to the Right</h1>
        <p>Keep scrolling horizontally to reveal the secret password!</p>
      </div>

      <div className="mt-[100px] whitespace-nowrap overflow-x-auto p-5">
        {boxes}
        {isLastBoxVisible && (
          <div
            className="inline-flex w-[300px] h-[80vh] m-5 rounded-lg items-center justify-center text-2xl text-white"
            style={{
              backgroundColor: "#22c55e",
              writingMode: "vertical-rl",
              textOrientation: "mixed",
            }}
          >
            Keep scrolling! You made it! Password: {PASSWORD_ScrollHorizontal}
          </div>
        )}
      </div>
    </div>
  );
};

export default ScrollHorizontal;
