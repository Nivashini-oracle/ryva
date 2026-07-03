import { useEffect, useState, useRef } from "react";
import Sidebar from "./components/Sidebar";
import StatCards from "./components/StatCards";
import MachineGrid from "./components/MachineGrid";
import EventPanel from "./components/EventPanel";
import IncidentReport from "./components/IncidentReport";

type State = "GREEN" | "AMBER" | "RED";

export type EventEntry = {
  id: number;
  type: "AMBER" | "RED" | "PPE VIOLATION" | "SOS" | "PPE CLEARED" | "GREEN";
  operator: string;
  timestamp: string;
};

export type OperatorData = {
  operatorId: string;
  cls: number;
  state: State;
  etaMinutes: number | null;
};

type ClsPoint = { t: number; cls: number };

type IncidentData = {
  operatorId: string;
  timestamp: string;
  clsHistory: ClsPoint[];
  recommendation: string;
};

const DUMMY_SHIFT = [
  { operator: "R001", amberMinutes: 18, redEvents: 2, ppeViolations: 1, status: "Needs Attention" as const },
  { operator: "R002", amberMinutes: 5,  redEvents: 0, ppeViolations: 0, status: "Cleared" as const },
  { operator: "R003", amberMinutes: 11, redEvents: 1, ppeViolations: 2, status: "Needs Attention" as const },
];

const INITIAL_OPERATORS: OperatorData[] = [
  { operatorId: "R001", cls: 72, state: "AMBER", etaMinutes: null },
  { operatorId: "R002", cls: 34, state: "GREEN", etaMinutes: null },
  { operatorId: "R003", cls: 85, state: "RED",   etaMinutes: null },
];

export default function App() {
  const [operators, setOperators] = useState<OperatorData[]>(INITIAL_OPERATORS);
  const [events, setEvents] = useState<EventEntry[]>([]);
  const [connected, setConnected] = useState(false);
  const [activePPE, setActivePPE] = useState<Set<string>>(new Set());
  const [incident, setIncident] = useState<IncidentData | null>(null);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const wsRef = useRef<WebSocket | null>(null);
  const counterRef = useRef(0);

  const now = new Date();
  const dateStr = now.toLocaleDateString("en-IN", { day: "numeric", month: "short", year: "numeric" });

  useEffect(() => {
    function connect() {
      const ws = new WebSocket("ws://localhost:8765/ws");
      wsRef.current = ws;
      ws.onopen = () => setConnected(true);
      ws.onmessage = (e) => {
        const msg = JSON.parse(e.data);
        if (msg.type === "cls_update") {
          setOperators(prev => {
            const exists = prev.find(o => o.operatorId === msg.operator_id);
            if (exists) return prev.map(o => o.operatorId === msg.operator_id ? { ...o, cls: msg.cls, state: msg.state } : o);
            return [...prev, { operatorId: msg.operator_id, cls: msg.cls, state: msg.state, etaMinutes: null }];
          });
        }
        if (msg.type === "event") {
          counterRef.current += 1;
          setEvents(prev => [{ id: counterRef.current, type: msg.event_type as EventEntry["type"], operator: msg.operator_id, timestamp: msg.ts }, ...prev].slice(0, 100));
        }
        if (msg.type === "ppe_violation") {
          counterRef.current += 1;
          if (msg.cleared) {
            setActivePPE(prev => { const n = new Set(prev); n.delete(msg.operator_id); return n; });
            setEvents(prev => [{ id: counterRef.current, type: "PPE CLEARED" as const, operator: msg.operator_id, timestamp: msg.ts }, ...prev].slice(0, 100));
          } else {
            setActivePPE(prev => new Set(prev).add(msg.operator_id));
            setEvents(prev => [{ id: counterRef.current, type: "PPE VIOLATION" as const, operator: msg.operator_id, timestamp: msg.ts }, ...prev].slice(0, 100));
          }
        }
        if (msg.type === "sos") {
          counterRef.current += 1;
          setEvents(prev => [{ id: counterRef.current, type: "SOS" as const, operator: msg.operator_id, timestamp: msg.ts }, ...prev].slice(0, 100));
        }
        if (msg.type === "incident_report") {
          setIncident({ operatorId: msg.data.operator_id, timestamp: msg.data.ts, clsHistory: msg.data.cls_history, recommendation: msg.data.recommendation });
        }
        if (msg.type === "cls_history") {
          const data: ClsPoint[] = msg.data;
          if (data.length >= 2) {
            const slope = (data[data.length - 1].cls - data[0].cls) / (data.length - 1);
            const newest = data[data.length - 1];
            const eta = slope > 0.03 && newest.cls < 71 ? Math.round((71 - newest.cls) / slope / 60) : null;
            setOperators(prev => prev.map(o => o.operatorId === msg.operator_id ? { ...o, etaMinutes: eta } : o));
          }
        }
      };
      ws.onclose = () => { setConnected(false); setTimeout(connect, 3000); };
    }
    connect();
    return () => wsRef.current?.close();
  }, []);

  const amberCount = operators.filter(o => o.state === "AMBER").length;
  const redCount = operators.filter(o => o.state === "RED").length;
  const ppeCount = activePPE.size;
  const stripe = "repeating-linear-gradient(45deg, #f59e0b, #f59e0b 8px, #0a0a0a 8px, #0a0a0a 16px)";

  return (
    <div style={{ minHeight: "100vh", background: "#0a0a0a", fontFamily: "monospace" }}>
      <div style={{ height: "5px", background: stripe }} />
      {incident && (
        <IncidentReport
          operatorId={incident.operatorId}
          timestamp={incident.timestamp}
          clsHistory={incident.clsHistory}
          recommendation={incident.recommendation}
          onClose={() => setIncident(null)}
        />
      )}
      <div style={{ display: "flex" }}>
        {sidebarOpen && <Sidebar connected={connected} dateStr={dateStr} shiftRows={DUMMY_SHIFT} />}
        <div style={{ flex: 1, display: "flex", flexDirection: "column", padding: "28px 28px 28px 0", gap: "24px", minWidth: 0 }}>
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "4px 0 8px 28px", gap: "20px" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "18px" }}>
              <button
                onClick={() => setSidebarOpen(prev => !prev)}
                aria-label="Toggle sidebar"
                style={{
                  width: "36px", height: "36px", flexShrink: 0,
                  background: "#111111", border: "1px solid #262626",
                  color: "#f59e0b", cursor: "pointer",
                  display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", gap: "4px",
                }}
              >
                <span style={{ width: "16px", height: "2px", background: "#f59e0b" }} />
                <span style={{ width: "16px", height: "2px", background: "#f59e0b" }} />
                <span style={{ width: "16px", height: "2px", background: "#f59e0b" }} />
              </button>
              <div>
                <div style={{ color: "#666666", fontSize: "11px", letterSpacing: "0.2em", marginBottom: "6px" }}>RYVA / SUPERVISOR</div>
                <div style={{ color: "#e5e5e5", fontSize: "22px", fontWeight: "700", letterSpacing: "0.06em" }}>OPERATOR MONITORING</div>
              </div>
            </div>
            <div style={{ display: "flex", alignItems: "center", gap: "8px", background: "#111111", border: "1px solid #262626", borderLeft: `3px solid ${connected ? "#22c55e" : "#ef4444"}`, padding: "8px 16px", flexShrink: 0 }}>
              <span style={{ width: "6px", height: "6px", borderRadius: "50%", background: connected ? "#22c55e" : "#ef4444", boxShadow: connected ? "0 0 6px #22c55e" : "0 0 6px #ef4444", display: "inline-block" }} />
              <span style={{ color: connected ? "#22c55e" : "#ef4444", fontSize: "11px", letterSpacing: "0.05em" }}>{connected ? "LIVE" : "DISCONNECTED"}</span>
              <span style={{ color: "#666666", fontSize: "11px", marginLeft: "8px" }}>{dateStr}</span>
            </div>
          </div>
          <div style={{ padding: "0 0 0 28px", display: "flex", flexDirection: "column", gap: "24px" }}>
            {activePPE.size > 0 && (
              <div style={{ background: "#150a00", border: "1px solid #ef4444", borderLeft: "4px solid #ef4444", padding: "10px 16px" }}>
                <span style={{ color: "#ef4444", fontSize: "11px", fontWeight: "700", letterSpacing: "0.05em" }}>[!] ACTIVE PPE VIOLATION -- {Array.from(activePPE).join(", ")}</span>
              </div>
            )}
            <StatCards amberCount={amberCount} redCount={redCount} ppeCount={ppeCount} totalOps={operators.length} />
            <div style={{ display: "flex", gap: "20px", flex: 1, minHeight: 0 }}>
              <div style={{ flex: 1, minWidth: 0 }}><MachineGrid operators={operators} /></div>
              <div style={{ width: "clamp(240px, 18vw, 340px)", flexShrink: 0 }}><EventPanel events={events} /></div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
