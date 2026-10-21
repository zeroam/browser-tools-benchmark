import { useState } from "react";
import { useTaskAnalytics } from "../utils/useTaskAnalytics";

export const PASSWORD_RightClickReveal = "RIGHT_CLICK_MASTER";
export const TASK_ID_RightClickReveal = "right-click";

const RightClickReveal = () => {
  const { recordSuccess } = useTaskAnalytics(TASK_ID_RightClickReveal);
  const [password, setPassword] = useState("");

  const handleContextMenu = (e: React.MouseEvent) => {
    e.preventDefault();
    setPassword(PASSWORD_RightClickReveal);
    recordSuccess();
  };

  return (
    <div className="p-6 max-w-2xl mx-auto">
      <h1 className="text-2xl font-bold mb-4">Right Click Challenge</h1>

      <p className="mb-6">
        Right-click on the area below to reveal the password. Sometimes the
        answer is as simple as following instructions!
      </p>

      <div
        className="p-6 text-center bg-white dark:bg-gray-800 rounded-lg shadow-md cursor-context-menu hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
        onContextMenu={handleContextMenu}
      >
        <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
          Show Password
        </h2>
        {password && (
          <p className="mt-4 text-green-600 dark:text-green-400">
            Password: {password}
          </p>
        )}
      </div>
    </div>
  );
};

export default RightClickReveal;
