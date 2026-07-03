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
    <div style={{ position: "fixed", top: 0, left: 0, right: 0, bottom: 0, background: "rgba(0,0,0,0.75)", display: "flex", alignItems: "center", justifyContent: "center", zIndex: 1000 }}>
      <div style={{ background: "#161628", borderRadius: "16px", padding: "28px", width: "520px", boxShadow: "0 8px 40px rgba(0,0,0,0.6)", border: "1px solid #ef4444" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "20px" }}>
          <div>
            <div style={{ color: "#475569", fontSize: "10px", letterSpacing: "0.1em" }}>RYVA / INCIDENT</div>
            <div style={{ color: "#ef4444", fontSize: "16px", fontWeight: "700" }}>[!] Incident Report</div>
          </div>
          <button onClick={onClose} style={{ background: "none", border: "1px solid #1e1e3a", color: "#475569", borderRadius: "6px", padding: "6px 12px", cursor: "pointer", fontFamily: "monospace", fontSize: "11px" }}>CLOSE</button>
        </div>
        <div style={{ display: "flex", gap: "24px", marginBottom: "20px" }}>
          <div>
            <div style={{ color: "#475569", fontSize: "10px", marginBottom: "4px" }}>OPERATOR</div>
            <div style={{ color: "#e2e8f0", fontSize: "14px", fontWeight: "700" }}>{operatorId}</div>
          </div>
          <div>
            <div style={{ color: "#475569", fontSize: "10px", marginBottom: "4px" }}>TRIGGERED AT</div>
            <div style={{ color: "#e2e8f0", fontSize: "14px", fontWeight: "700" }}>{timestamp}</div>
          </div>
        </div>
        <div style={{ marginBottom: "20px" }}>
          <div style={{ color: "#475569", fontSize: "10px", marginBottom: "10px" }}>5-MINUTE CLS HISTORY</div>
          <ResponsiveContainer width="100%" height={150}>
            <LineChart data={clsHistory}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e1e3a" />
              <XAxis dataKey="t" hide />
              <YAxis domain={[0, 100]} tick={{ fill: "#475569", fontSize: 10, fontFamily: "monospace" }} />
              <Tooltip contentStyle={{ background: "#0f0f1f", border: "1px solid #1e1e3a", borderRadius: "8px", fontFamily: "monospace", fontSize: "11px" }} itemStyle={{ color: "#ef4444" }} labelStyle={{ color: "#475569" }} />
              <Line type="monotone" dataKey="cls" stroke="#ef4444" strokeWidth={2} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>
        <div style={{ background: "#0f0f1f", border: "1px solid #1e1e3a", borderRadius: "8px", padding: "14px 16px" }}>
          <div style={{ color: "#475569", fontSize: "10px", marginBottom: "6px" }}>RECOMMENDED ACTION</div>
          <div style={{ color: "#f59e0b", fontSize: "13px" }}>{recommendation}</div>
        </div>
      </div>
    </div>
  );
}
