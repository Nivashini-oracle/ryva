import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";

type ClsPoint = { t: number; cls: number };

interface IncidentReportProps {
  operatorId: string;
  timestamp: string;
  clsHistory: ClsPoint[];
  recommendation: string;
  onClose: () => void;
}

export default function IncidentReport({ operatorId, timestamp, clsHistory, recommendation, onClose }: IncidentReportProps) {
  return (
    <div style={{
      position: "fixed",
      top: 0, left: 0, right: 0, bottom: 0,
      background: "rgba(0,0,0,0.7)",
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
      zIndex: 1000,
    }}>
      <div style={{
        background: "#1e1e2e",
        borderRadius: "16px",
        padding: "28px",
        width: "520px",
        boxShadow: "0 8px 40px rgba(0,0,0,0.6)",
        border: "1px solid #ef4444",
      }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "20px" }}>
          <h2 style={{ color: "#ef4444", fontFamily: "monospace", fontSize: "16px", letterSpacing: "0.1em" }}>
            [!] INCIDENT REPORT
          </h2>
          <button onClick={onClose} style={{
            background: "none",
            border: "1px solid #64748b",
            color: "#64748b",
            borderRadius: "6px",
            padding: "4px 10px",
            cursor: "pointer",
            fontFamily: "monospace",
            fontSize: "12px",
          }}>
            CLOSE
          </button>
        </div>

        <div style={{ display: "flex", gap: "24px", marginBottom: "20px" }}>
          <div>
            <div style={{ color: "#64748b", fontFamily: "monospace", fontSize: "11px" }}>OPERATOR</div>
            <div style={{ color: "#e2e8f0", fontFamily: "monospace", fontSize: "14px" }}>{operatorId}</div>
          </div>
          <div>
            <div style={{ color: "#64748b", fontFamily: "monospace", fontSize: "11px" }}>TIME</div>
            <div style={{ color: "#e2e8f0", fontFamily: "monospace", fontSize: "14px" }}>{timestamp}</div>
          </div>
        </div>

        <div style={{ marginBottom: "20px" }}>
          <div style={{ color: "#64748b", fontFamily: "monospace", fontSize: "11px", marginBottom: "8px" }}>
            5-MINUTE CLS HISTORY
          </div>
          <ResponsiveContainer width="100%" height={160}>
            <LineChart data={clsHistory}>
              <CartesianGrid strokeDasharray="3 3" stroke="#2d2d3f" />
              <XAxis dataKey="t" hide />
              <YAxis domain={[0, 100]} tick={{ fill: "#64748b", fontSize: 10 }} />
              <Tooltip
                contentStyle={{ background: "#2d2d3f", border: "none", borderRadius: "8px", fontFamily: "monospace", fontSize: "12px" }}
                labelStyle={{ color: "#64748b" }}
                itemStyle={{ color: "#ef4444" }}
              />
              <Line type="monotone" dataKey="cls" stroke="#ef4444" strokeWidth={2} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>

        <div style={{
          background: "#2d2d3f",
          borderRadius: "8px",
          padding: "12px 16px",
        }}>
          <div style={{ color: "#64748b", fontFamily: "monospace", fontSize: "11px", marginBottom: "4px" }}>
            RECOMMENDATION
          </div>
          <div style={{ color: "#f59e0b", fontFamily: "monospace", fontSize: "13px" }}>
            {recommendation}
          </div>
        </div>
      </div>
    </div>
  );
}
