import { useEffect, useState, useRef } from "react";
import MachineCard from "./components/MachineCard";
import EventLog from "./components/EventLog";
import ShiftSummary from "./components/ShiftSummary";

type State = "GREEN" | "AMBER" | "RED";

export type EventEntry = {
  id: number;
  type: "AMBER" | "RED" | "PPE VIOLATION" | "SOS";
  operator: string;
  timestamp: string;
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
  const wsRef = useRef<WebSocket | null>(null);
  const counterRef = useRef(0);

  useEffect(() => {
    function connect() {
      const ws = new WebSocket('ws://localhost:8765/ws');
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
      <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
        <h1 style={{ color: "#e2e8f0", fontFamily: "monospace", fontSize: "18px", letterSpacing: "0.2em" }}>
          RYVA � SUPERVISOR DASHBOARD
        </h1>
        <span style={{
          width: "8px", height: "8px", borderRadius: "50%",
          backgroundColor: connected ? "#22c55e" : "#ef4444",
          boxShadow: connected ? "0 0 6px #22c55e" : "0 0 6px #ef4444",
          display: "inline-block",
        }} />
      </div>
      <MachineCard operatorId={operatorId} cls={cls} state={state} />
      <EventLog events={events} />
      <ShiftSummary rows={DUMMY_SHIFT} />
    </div>
  );
}
