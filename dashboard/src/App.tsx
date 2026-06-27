import { useEffect, useState, useRef } from "react";
import MachineCard from "./components/MachineCard";
import EventLog from "./components/EventLog";
import ShiftSummary from "./components/ShiftSummary";
import IncidentReport from "./components/IncidentReport";

type State = "GREEN" | "AMBER" | "RED";

export type EventEntry = {
  id: number;
  type: "AMBER" | "RED" | "PPE VIOLATION" | "SOS" | "PPE CLEARED" | "GREEN";
  operator: string;
  timestamp: string;
};

type ClsPoint = { t: number; cls: number };

type IncidentData = {
  operatorId: string;
  timestamp: string;
  clsHistory: ClsPoint[];
  recommendation: string;
};

const DUMMY_SHIFT = [
  { operator: "Operator Rajan", amberMinutes: 18, redEvents: 2, ppeViolations: 1, status: "Needs Attention" as const },
  { operator: "Operator Kumar", amberMinutes: 5,  redEvents: 0, ppeViolations: 0, status: "Cleared" as const },
  { operator: "Operator Singh", amberMinutes: 11, redEvents: 1, ppeViolations: 2, status: "Needs Attention" as const },
];

export default function App() {
  const [cls, setCls] = useState(72);
  const [state, setState] = useState<State>("AMBER");
  const [operatorId, setOperatorId] = useState("MACHINE-01");
  const [events, setEvents] = useState<EventEntry[]>([]);
  const [connected, setConnected] = useState(false);
  const [activePPE, setActivePPE] = useState<Set<string>>(new Set());
  const [incident, setIncident] = useState<IncidentData | null>(null);
  const [etaMinutes, setEtaMinutes] = useState<number | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const counterRef = useRef(0);

  useEffect(() => {
    function connect() {
      const ws = new WebSocket("ws://localhost:8765/ws");
      wsRef.current = ws;

      ws.onopen = () => setConnected(true);

      ws.onmessage = (e) => {
        const msg = JSON.parse(e.data);

        if (msg.type === "cls_update") {
          setCls(msg.cls);
          setState(msg.state);
          setOperatorId(msg.operator_id);
        }

        if (msg.type === "event") {
          counterRef.current += 1;
          setEvents(prev => [{
            id: counterRef.current,
            type: msg.event_type,
            operator: msg.operator_id,
            timestamp: msg.ts,
          }, ...prev].slice(0, 100));
        }

        if (msg.type === "ppe_violation") {
          counterRef.current += 1;
          if (msg.cleared) {
            setActivePPE(prev => {
              const next = new Set(prev);
              next.delete(msg.operator_id);
              return next;
            });
            setEvents(prev => [{
              id: counterRef.current,
              type: "PPE CLEARED",
              operator: msg.operator_id,
              timestamp: msg.ts,
            }, ...prev].slice(0, 100));
          } else {
            setActivePPE(prev => new Set(prev).add(msg.operator_id));
            setEvents(prev => [{
              id: counterRef.current,
              type: "PPE VIOLATION",
              operator: msg.operator_id,
              timestamp: msg.ts,
            }, ...prev].slice(0, 100));
          }
        }

        if (msg.type === "sos") {
          counterRef.current += 1;
          setEvents(prev => [{
            id: counterRef.current,
            type: "SOS",
            operator: msg.operator_id,
            timestamp: msg.ts,
          }, ...prev].slice(0, 100));
        }

        if (msg.type === "incident_report") {
          setIncident({
            operatorId: msg.data.operator_id,
            timestamp: msg.data.ts,
            clsHistory: msg.data.cls_history,
            recommendation: msg.data.recommendation,
          });
        }

        if (msg.type === "cls_history") {
          const data: ClsPoint[] = msg.data;
          if (data.length >= 2) {
            const oldest = data[0];
            const newest = data[data.length - 1];
            const slope = (newest.cls - oldest.cls) / (data.length - 1);
            if (slope > 0.03 && newest.cls < 71) {
              const eta = Math.round((71 - newest.cls) / slope / 60);
              setEtaMinutes(eta > 0 ? eta : null);
            } else {
              setEtaMinutes(null);
            }
          }
        }
      };

      ws.onclose = () => {
        setConnected(false);
        setTimeout(connect, 3000);
      };
    }

    connect();
    return () => wsRef.current?.close();
  }, []);

  return (
    <div style={{
      minHeight: "100vh",
      background: "#0f0f1a",
      display: "flex",
      flexDirection: "column",
      alignItems: "center",
      padding: "40px 20px",
      gap: "24px",
    }}>
      {incident && (
        <IncidentReport
          operatorId={incident.operatorId}
          timestamp={incident.timestamp}
          clsHistory={incident.clsHistory}
          recommendation={incident.recommendation}
          onClose={() => setIncident(null)}
        />
      )}

      <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
        <h1 style={{ color: "#e2e8f0", fontFamily: "monospace", fontSize: "18px", letterSpacing: "0.2em" }}>
          RYVA - SUPERVISOR DASHBOARD
        </h1>
        <span style={{
          width: "8px", height: "8px", borderRadius: "50%",
          backgroundColor: connected ? "#22c55e" : "#ef4444",
          boxShadow: connected ? "0 0 6px #22c55e" : "0 0 6px #ef4444",
          display: "inline-block",
        }} />
      </div>

      {activePPE.size > 0 && (
        <div style={{
          background: "#2d0a0a",
          border: "1px solid #ef4444",
          borderRadius: "12px",
          padding: "12px 20px",
          width: "100%",
          maxWidth: "600px",
          display: "flex",
          alignItems: "center",
          gap: "12px",
        }}>
          <span style={{ color: "#ef4444", fontFamily: "monospace", fontSize: "13px", fontWeight: "700" }}>
            [!] ACTIVE PPE VIOLATION -- {Array.from(activePPE).join(", ")}
          </span>
        </div>
      )}

      <MachineCard operatorId={operatorId} cls={cls} state={state} etaMinutes={etaMinutes} />
      <EventLog events={events} />
      <ShiftSummary rows={DUMMY_SHIFT} />
    </div>
  );
}
