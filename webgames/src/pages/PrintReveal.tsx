import React, { useEffect, useState } from "react";
import { useTaskAnalytics } from "../utils/useTaskAnalytics";

export const PASSWORD_PrintReveal = "PR1NT_V3R1F13D_2024";
export const PASSWORD_PrintRevealPDF = "PRINT_2_PDF_8X11";
export const TASK_ID_PrintReveal = "print-reveal";

const PrintReveal: React.FC = () => {
  const { recordSuccess } = useTaskAnalytics(TASK_ID_PrintReveal);
  const [inputPassword, setInputPassword] = useState("");
  const [isRevealed, setIsRevealed] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    // Add print-specific styles
    const style = document.createElement("style");
    style.setAttribute("type", "text/css");
    style.setAttribute("media", "print");
    style.textContent = `
      .print-only { display: block !important; }
      .screen-only { display: none !important; }
    `;
    document.head.appendChild(style);

    return () => {
      document.head.removeChild(style);
    };
  }, []);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setError("");

    // Trim whitespace and normalize case
    const normalizedInput = inputPassword.trim();

    if (normalizedInput === PASSWORD_PrintRevealPDF) {
      setIsRevealed(true);
      recordSuccess();
    } else {
      setError("Incorrect password. Please check the PDF and try again.");
    }
  };

  return (
    <div className="p-8 max-w-3xl mx-auto">
      <div className="bg-white rounded-lg shadow-lg p-8">
        <div className="screen-only">
          <h1 className="text-3xl font-bold mb-4">Print to Reveal</h1>
          <p className="text-gray-700 mb-4">
            First, print this page or save it as PDF to find the initial
            password.
          </p>
          <p className="text-gray-700 mb-4">
            Try using your browser's print function (Ctrl/Cmd + P) or "Save as
            PDF" option.
          </p>
          <p className="text-gray-700 mb-4">
            Then, enter that password below to reveal the final password.
          </p>

          <form onSubmit={handleSubmit} className="mt-8">
            <input
              type="text"
              value={inputPassword}
              onChange={(e) => setInputPassword(e.target.value)}
              placeholder="Enter the password from the PDF..."
              className="w-full p-2 border border-gray-300 rounded mb-4"
              autoComplete="off"
            />
            {error && <p className="text-red-500 text-sm mb-4">{error}</p>}
            <button
              type="submit"
              className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600"
            >
              Verify Password
            </button>
          </form>

          {isRevealed && (
            <div className="mt-8 p-4 border-2 border-green-500 rounded-lg">
              <p className="text-green-700 font-bold mb-2">Congratulations!</p>
              <p className="text-gray-700">The final password is:</p>
              <p className="text-2xl font-bold text-green-600">
                {PASSWORD_PrintReveal}
              </p>
            </div>
          )}

          <p className="text-gray-500 mt-8 text-sm">
            Hint: The initial password is hidden in this page, but you won't see
            it on screen!
          </p>
        </div>

        <div className="print-only hidden text-center border-2 border-dashed border-black p-8 mt-8">
          <h2 className="text-3xl font-bold mb-4">First Step Complete!</h2>
          <p className="mb-4">
            You've found the initial password. Now go back to the webpage and
            enter this password:
          </p>
          <p className="text-2xl font-bold">{PASSWORD_PrintRevealPDF}</p>
          <p className="mt-4 text-sm">
            Enter this password on the webpage to reveal the final password.
          </p>
        </div>
      </div>
    </div>
  );
};

export default PrintReveal;
