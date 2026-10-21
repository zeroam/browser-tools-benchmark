import { useEffect, useRef, useState } from "react";
import { useTaskAnalytics } from "../utils/useTaskAnalytics";

export const TASK_ID_ScrollVertical = "scroll-vertical";
export const PASSWORD_ScrollVertical = "SCROLLMASTER2024";

const ScrollVertical = () => {
  const { recordSuccess } = useTaskAnalytics(TASK_ID_ScrollVertical);
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
        threshold: 0.8, // 100% of the element must be visible
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
        className="h-[200px] m-5 rounded-lg flex items-center justify-center text-2xl text-gray-600"
        style={{
          backgroundColor: `hsl(${(index * 7) % 360}, 70%, 80%)`,
        }}
      >
        Keep scrolling! {50 - index} boxes to go...
      </div>
    ));

  return (
    <div className="p-5">
      <h1>Scroll to the Bottom</h1>
      <p>Keep scrolling down to reveal the secret password!</p>

      {boxes}

      {isLastBoxVisible && (
        <div className="p-5 bg-green-500 text-white rounded-lg text-center mt-5">
          Congratulations! You've reached the bottom!
          <div className="mt-2.5 text-2xl font-bold">
            Password: {PASSWORD_ScrollVertical}
          </div>
        </div>
      )}
    </div>
  );
};

export default ScrollVertical;
