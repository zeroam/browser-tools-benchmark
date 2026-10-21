import { useEffect, useState } from "react";
import { useTaskAnalytics } from "../utils/useTaskAnalytics";
import wasmUrl from "/code_gen.wasm?url";

export const PASSWORD_WebsAssemble = "WebAssemblyMaster";
export const TASK_ID_WebsAssemble = "webs-assemble";
interface WasmExports {
  get_code: () => number;
  memory: WebAssembly.Memory;
}

const WebsAssemble: React.FC = () => {
  const { recordSuccess } = useTaskAnalytics(TASK_ID_WebsAssemble);
  const [wasmLoaded, setWasmLoaded] = useState(false);
  const [code, setCode] = useState("");
  const [userInput, setUserInput] = useState("");
  const [message, setMessage] = useState<{
    text: string;
    type: "success" | "error" | null;
  }>({ text: "", type: null });

  useEffect(() => {
    const loadWasm = async () => {
      try {
        const response = await fetch(wasmUrl);
        const wasmBytes = await response.arrayBuffer();
        const wasmModule = await WebAssembly.instantiate(wasmBytes);
        const exports = wasmModule.instance.exports as unknown as WasmExports;
        const result = exports.get_code();

        // Convert the pointer to a string
        const view = new Uint8Array(exports.memory.buffer);
        let str = "";
        let i = result;
        while (view[i] !== 0) {
          str += String.fromCharCode(view[i]);
          i++;
        }
        setCode(str);
        setWasmLoaded(true);
      } catch (err) {
        const error = err as Error;
        setMessage({
          text: `Failed to load WebAssembly module: ${error.message}`,
          type: "error",
        });
      }
    };

    loadWasm();
  }, []);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (userInput === code) {
      setMessage({
        text: `Correct! The completion password is: ${PASSWORD_WebsAssemble}`,
        type: "success",
      });
      recordSuccess();
    } else {
      setMessage({
        text: "Incorrect code. Try inspecting the WebAssembly module more carefully.",
        type: "error",
      });
    }
  };

  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-gradient-to-b from-purple-100 to-blue-100 p-4">
      <div className="max-w-md w-full bg-white rounded-xl shadow-lg p-6">
        <h1 className="text-3xl font-bold text-center mb-6 text-purple-600">
          Webs, Assemble!
        </h1>

        <div className="mb-6 text-center">
          <p className="text-lg mb-2">
            {wasmLoaded
              ? "WebAssembly module loaded! Please enter the code you see into the box below, to get the final password:"
              : "Loading WebAssembly module..."}
          </p>
          {wasmLoaded && (
            <div className="mt-4 p-4 bg-gray-100 rounded-lg">
              <p className="text-sm font-mono break-all">{code}</p>
            </div>
          )}
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700">
              Enter the code from above
            </label>
            <input
              type="text"
              value={userInput}
              onChange={(e) => setUserInput(e.target.value)}
              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-purple-500 focus:ring-purple-500"
              placeholder="XXXX_XXXX_XXXX"
              required
            />
          </div>
          <button
            type="submit"
            className="w-full bg-purple-500 text-white px-4 py-2 rounded hover:bg-purple-600 transition-colors mb-4"
            disabled={!wasmLoaded}
          >
            Submit Code
          </button>
        </form>

        {message.text && (
          <div
            className={`my-4 p-3 rounded-lg text-center ${
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
      </div>
    </div>
  );
};

export default WebsAssemble;
