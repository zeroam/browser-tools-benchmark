import React, { useState } from "react";
import WeeklyCalendar, { calendarEvents } from "../components/WeeklyCalendar";
import { useTaskAnalytics } from "../utils/useTaskAnalytics";

export const PASSWORD_CalendarComprehension2 = "time_wizard_2024";
export const TASK_ID_CalendarComprehension2 = "calendar2";

const days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"];

const questions = [
  {
    id: 1,
    question:
      "How many minutes are unscheduled between 9am and 6pm on Monday? Answer in an integer number of minutes.",
    answer: "240",
  },
  {
    id: 2,
    question:
      "When is the earliest time on Tuesday after lunch that I could schedule a 45 minute meeting? Answer in the format HH:MM.",
    answer: "17:00",
  },
  {
    id: 3,
    question:
      "How many minutes do I have free between Retrospective and Weekly Sync on Friday? Answer in an integer number of minutes.",
    answer: "60",
  },
];

const CalendarComprehension2: React.FC = () => {
  const { recordSuccess } = useTaskAnalytics(TASK_ID_CalendarComprehension2);
  const [answers, setAnswers] = useState<{ [key: number]: string }>({});
  const [showResults, setShowResults] = useState(false);
  const [message, setMessage] = useState("");
  const [isComplete, setIsComplete] = useState(false);

  const handleAnswerChange = (questionId: number, value: string) => {
    setAnswers((prev) => ({ ...prev, [questionId]: value }));
  };

  const checkAnswers = () => {
    const allCorrect = questions.every(
      (q) => answers[q.id]?.trim().toLowerCase() === q.answer.toLowerCase()
    );

    if (allCorrect) {
      setMessage("Congratulations! All answers are correct!");
      setIsComplete(true);
      recordSuccess();
    } else {
      setMessage("Some answers are incorrect. Please try again.");
    }
    setShowResults(true);
  };

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <h1 className="text-3xl font-bold mb-6">
        Advanced Calendar Comprehension Challenge
      </h1>

      <WeeklyCalendar
        events={calendarEvents}
        days={days}
        startHour={9}
        endHour={18}
      />

      <div className="mt-8">
        {isComplete ? (
          <div className="p-8 bg-green-100 border-2 border-green-500 rounded-lg text-center">
            <h2 className="text-2xl font-bold text-green-700 mb-4">
              🎉 Challenge Complete!
            </h2>
            <p className="text-xl mb-4">Your password is:</p>
            <div className="inline-block font-mono text-2xl bg-green-200 px-6 py-3 rounded-lg font-bold">
              {PASSWORD_CalendarComprehension2}
            </div>
          </div>
        ) : (
          <>
            <h2 className="text-2xl font-bold mb-4">
              Answer these questions about the calendar:
            </h2>

            {questions.map((q) => (
              <div key={q.id} className="mb-6">
                <p className="text-lg mb-2">{q.question}</p>
                <input
                  type="text"
                  className={`w-full p-2 border rounded-lg ${
                    showResults &&
                    answers[q.id]?.trim().toLowerCase() !==
                      q.answer.toLowerCase()
                      ? "border-red-500"
                      : "border-gray-300"
                  }`}
                  value={answers[q.id] || ""}
                  onChange={(e) => handleAnswerChange(q.id, e.target.value)}
                />
                {showResults &&
                  answers[q.id]?.trim().toLowerCase() !==
                    q.answer.toLowerCase() && (
                    <p className="text-red-500 text-sm mt-1">
                      Incorrect answer
                    </p>
                  )}
              </div>
            ))}

            <button
              onClick={checkAnswers}
              className="mt-4 bg-blue-500 text-white px-6 py-2 rounded-lg hover:bg-blue-600 transition-colors"
            >
              Check Answers
            </button>

            {message && (
              <p
                className={`mt-4 ${
                  message.includes("Congratulations")
                    ? "text-green-600"
                    : "text-red-600"
                }`}
              >
                {message}
              </p>
            )}
          </>
        )}
      </div>
    </div>
  );
};

export default CalendarComprehension2;
