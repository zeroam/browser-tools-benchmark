import { useEffect, useMemo, useState } from "react";
import { useTaskAnalytics } from "../utils/useTaskAnalytics";
import { PASSWORD_TabSync, TASK_ID_TabSync } from "./TabSync";

const CORRECT_SEQUENCE = ["#FF0000", "#0000FF", "#FFFF00", "#00FF00"]; // Red, Blue, Yellow, Green
const PASSWORD = PASSWORD_TabSync;

const TabSyncReceiver = () => {
  const { recordSuccess } = useTaskAnalytics(TASK_ID_TabSync);
  const [receivedColors, setReceivedColors] = useState<string[]>([]);
  const [showPassword, setShowPassword] = useState(false);
  const channel = useMemo(() => new BroadcastChannel("color-sync"), []);

  useEffect(() => {
    const handleMessage = (event: MessageEvent) => {
      const { color } = event.data;
      setReceivedColors((prev) => {
        const newColors = [...prev, color];
        // Only keep the last N colors where N is the length of the correct sequence
        if (newColors.length > CORRECT_SEQUENCE.length) {
          newColors.shift();
        }
        // Check if the sequence matches
        if (newColors.join(",") === CORRECT_SEQUENCE.join(",")) {
          setShowPassword(true);
          recordSuccess();
        }
        return newColors;
      });
    };

    channel.addEventListener("message", handleMessage);
    return () => channel.removeEventListener("message", handleMessage);
  }, [channel, recordSuccess]);

  return (
    <div
      style={{
        padding: "20px",
        maxWidth: "600px",
        margin: "0 auto",
        fontFamily: "Arial, sans-serif",
      }}
    >
      <h1 style={{ color: "#333", marginBottom: "20px" }}>Color Receiver</h1>

      <div
        style={{
          background: "#f5f5f5",
          padding: "20px",
          borderRadius: "8px",
          marginBottom: "30px",
        }}
      >
        <p>Waiting for the correct sequence of colors...</p>
        <p>Keep this tab open and use the sender tab to send colors!</p>
      </div>

      <div
        style={{
          display: "flex",
          gap: "10px",
          marginBottom: "20px",
          justifyContent: "center",
        }}
      >
        {receivedColors.map((color, index) => (
          <div
            key={index}
            style={{
              width: "50px",
              height: "50px",
              background: color,
              borderRadius: "4px",
              border: "2px solid #333",
            }}
          />
        ))}
      </div>

      {showPassword && (
        <div
          style={{
            textAlign: "center",
            animation: "fadeIn 0.5s ease-in",
            padding: "20px",
            background: "#4CAF50",
            color: "white",
            borderRadius: "8px",
            marginTop: "20px",
          }}
        >
          <h2 style={{ margin: "0 0 10px 0" }}>🎉 Success! 🎉</h2>
          <p style={{ margin: "0" }}>Password: {PASSWORD}</p>
        </div>
      )}
    </div>
  );
};

export default TabSyncReceiver;
