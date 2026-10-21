import { useState } from "react";
import { useParams } from "react-router-dom";

export const PASSWORD_IframeContent = "NestedVoyager";

const IframeContent = () => {
  const { depth } = useParams();
  const currentDepth = parseInt(depth || "0", 10);
  const [showVictory, setShowVictory] = useState(false);

  if (currentDepth === 0) {
    return (
      <div
        style={{
          width: "100%",
          height: "100%",
          display: "flex",
          flexDirection: "column",
          justifyContent: "center",
          alignItems: "center",
          background: "#f0f0f0",
          gap: "20px",
        }}
      >
        {showVictory ? (
          <div
            style={{
              color: "#4CAF50",
              fontWeight: "bold",
              fontSize: "20px",
              textAlign: "center",
              animation: "fadeIn 0.5s ease-in",
            }}
          >
            🎉 Victory! You found the button! 🎉
            <br />
            <span
              style={{
                fontSize: "18px",
                color: "#333",
                marginTop: "10px",
                display: "block",
              }}
            >
              Password: {PASSWORD_IframeContent}
            </span>
          </div>
        ) : (
          <button
            onClick={() => {
              // Send message to all parent frames recursively
              const sendToParent = (win: Window) => {
                if (win.parent && win.parent !== win) {
                  win.parent.postMessage({ type: "CHALLENGE_COMPLETE" }, "*");
                  sendToParent(win.parent);
                }
              };
              sendToParent(window);
              setShowVictory(true);
            }}
            style={{
              padding: "10px 20px",
              fontSize: "16px",
              background: "#4CAF50",
              color: "white",
              border: "none",
              borderRadius: "4px",
              cursor: "pointer",
            }}
          >
            Click me to complete!
          </button>
        )}
      </div>
    );
  }

  return (
    <div
      style={{
        width: "100%",
        height: "100vh",
        padding: "20px",
        boxSizing: "border-box",
        background: `hsl(${currentDepth * 30}, 70%, 95%)`,
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
      }}
    >
      <div
        style={{
          fontFamily: "Arial, sans-serif",
          marginBottom: "10px",
          color: "#666",
        }}
      >
        Layer {currentDepth}
      </div>
      <iframe
        src={`${window.location.origin}/iframe-content/${currentDepth - 1}`}
        style={{
          width: "90%",
          height: "90%",
          border: "2px solid #333",
          borderRadius: "8px",
        }}
      />
    </div>
  );
};

export default IframeContent;
