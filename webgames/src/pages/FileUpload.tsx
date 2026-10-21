import React, { useState } from "react";
import { useTaskAnalytics } from "../utils/useTaskAnalytics";

export const PASSWORD_FileUpload = "FILE_UPLOAD_2024";
export const TASK_ID_FileUpload = "file-upload";

const FileUpload = () => {
  const { recordSuccess } = useTaskAnalytics(TASK_ID_FileUpload);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      setSelectedFile(file);
      recordSuccess();
    }
  };

  return (
    <div className="flex flex-col items-center justify-center min-h-screen p-4">
      <div className="max-w-md w-full space-y-8 p-6 bg-white rounded-lg shadow-lg">
        <div className="text-center">
          <h2 className="text-2xl font-bold mb-4">Upload Challenge</h2>
          <p className="text-gray-600 mb-8">
            Complete this challenge by uploading any file.
          </p>
        </div>

        <div className="space-y-4">
          <div className="flex justify-center">
            <label className="relative cursor-pointer bg-blue-500 hover:bg-blue-600 text-white py-2 px-4 rounded-lg transition-colors">
              <span>{selectedFile ? "File selected!" : "Choose a file"}</span>
              <input
                type="file"
                className="hidden"
                onChange={handleFileChange}
                accept="*/*"
              />
            </label>
          </div>

          {selectedFile && (
            <div className="text-center text-green-600">
              <p>✨ Challenge completed! ✨</p>
              <p className="text-sm text-gray-600">
                Uploaded: {selectedFile.name}
              </p>
              <p>
                The secret password is:{" "}
                <span className="font-bold">{PASSWORD_FileUpload}</span>
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default FileUpload;
