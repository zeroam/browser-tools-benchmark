import React from "react";
import { Link } from "react-router-dom";

export const PASSWORD_TabSync = "ChromaticSync";
export const TASK_ID_TabSync = "tab-sync";

const TabSync: React.FC = () => {
  return (
    <div
      style={{
        padding: "20px",
        maxWidth: "800px",
        margin: "0 auto",
        fontFamily: "Arial, sans-serif",
      }}
    >
      <h1 style={{ color: "#333", marginBottom: "20px" }}>
        Tab Sync Challenge
      </h1>

      <div
        style={{
          background: "#f5f5f5",
          padding: "20px",
          borderRadius: "8px",
          marginBottom: "30px",
        }}
      >
        <h2 style={{ color: "#444", marginBottom: "15px" }}>Instructions</h2>
        <p>To complete this challenge, you need to:</p>
        <ol style={{ lineHeight: "1.6" }}>
          <li>Open the Sender tab in a new window</li>
          <li>Open the Receiver tab in another window</li>
          <li>Use the Sender tab to send the correct sequence of colors</li>
          <li>
            The password will be revealed in the Receiver tab when successful
          </li>
        </ol>
      </div>

      <div
        style={{
          display: "flex",
          gap: "20px",
          justifyContent: "center",
        }}
      >
        <Link
          to="/tab-sync/sender"
          target="_blank"
          style={{
            padding: "12px 24px",
            background: "#4CAF50",
            color: "white",
            textDecoration: "none",
            borderRadius: "4px",
            fontWeight: "bold",
          }}
        >
          Open Sender Tab
        </Link>
        <Link
          to="/tab-sync/receiver"
          target="_blank"
          style={{
            padding: "12px 24px",
            background: "#2196F3",
            color: "white",
            textDecoration: "none",
            borderRadius: "4px",
            fontWeight: "bold",
          }}
        >
          Open Receiver Tab
        </Link>
      </div>
    </div>
  );
};

export default TabSync;
