import { useState } from "react";
import { useTaskAnalytics } from "../utils/useTaskAnalytics";

export const PASSWORD_FileCredentials = "FileSecrets2024";
export const TASK_ID_FileCredentials = "file-credentials";

const FileCredentials: React.FC = () => {
  const { recordSuccess } = useTaskAnalytics(TASK_ID_FileCredentials);
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [message, setMessage] = useState<{
    text: string;
    type: "success" | "error" | null;
  }>({ text: "", type: null });
  const [isComplete, setIsComplete] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    if (username === "WebGames" && password === "hunter2") {
      setIsComplete(true);
      recordSuccess();
      setMessage({
        text: `Login successful! The completion password is: ${PASSWORD_FileCredentials}`,
        type: "success",
      });
    } else {
      setMessage({
        text: "Invalid credentials. Please check the downloaded file.",
        type: "error",
      });
    }
  };

  const handleDownload = () => {
    const content = "username: WebGames\npassword: hunter2";
    const blob = new Blob([content], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "credentials.txt";
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-gradient-to-b from-blue-100 to-green-100 p-4">
      <div className="max-w-md w-full bg-white rounded-xl shadow-lg p-6">
        <h1 className="text-3xl font-bold text-center mb-6 text-blue-600">
          File Credentials
        </h1>

        <div className="mb-6 text-center">
          <button
            onClick={handleDownload}
            className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600 transition-colors"
          >
            Download Credentials
          </button>
          <p className="text-sm text-gray-600 mt-2">
            Download and check the credentials.txt file
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
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700">
                Username
              </label>
              <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">
                Password
              </label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                required
              />
            </div>
            <button
              type="submit"
              className="w-full bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600 transition-colors"
            >
              Login
            </button>
          </form>
        )}
      </div>
    </div>
  );
};

export default FileCredentials;
