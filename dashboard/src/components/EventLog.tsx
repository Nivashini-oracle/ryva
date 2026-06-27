export type EventEntry = {
  id: number;
  type: "AMBER" | "RED" | "PPE VIOLATION" | "SOS" | "PPE CLEARED" | "GREEN";
  operator: string;
  timestamp: string;
};

const BADGE_COLORS: Record<string, string> = {
  "GREEN":         "#22c55e",
  "AMBER":         "#f59e0b",
  "RED":           "#ef4444",
  "PPE VIOLATION": "#ef4444",
  "PPE CLEARED":   "#22c55e",
  "SOS":           "#a855f7",
};

const BADGE_LABELS: Record<string, string> = {
  "GREEN":         "GREEN",
  "AMBER":         "AMBER",
  "RED":           "RED",
  "PPE VIOLATION": "PPE VIOLATION",
  "PPE CLEARED":   "PPE CLEARED",
  "SOS":           "SOS",
};

const DUMMY_EVENTS: EventEntry[] = [
  { id: 1, type: "RED",           operator: "Operator Rajan",  timestamp: "14:45:02" },
  { id: 2, type: "PPE VIOLATION", operator: "Operator Rajan",  timestamp: "14:38:21" },
  { id: 3, type: "PPE CLEARED",   operator: "Operator Rajan",  timestamp: "14:35:00" },
  { id: 4, type: "AMBER",         operator: "Operator Kumar",  timestamp: "14:23:11" },
  { id: 5, type: "GREEN",         operator: "Operator Kumar",  timestamp: "14:20:00" },
  { id: 6, type: "SOS",           operator: "Operator Kumar",  timestamp: "09:01:47" },
];

export default function EventLog({ events }: { events?: EventEntry[] }) {
  const display = events && events.length > 0 ? events : DUMMY_EVENTS;

  return (
    <div style={{
      background: "#1e1e2e",
      borderRadius: "16px",
      padding: "20px",
      width: "100%",
      maxWidth: "600px",
      boxShadow: "0 4px 24px rgba(0,0,0,0.4)",
    }}>
      <h2 style={{ color: "#e2e8f0", fontFamily: "monospace", fontSize: "14px", marginBottom: "12px", letterSpacing: "0.1em" }}>
        EVENT LOG
      </h2>
      <div style={{ maxHeight: "200px", overflowY: "auto", display: "flex", flexDirection: "column", gap: "8px" }}>
        {display.map(event => (
          <div key={event.id} style={{
            display: "flex",
            alignItems: "center",
            gap: "12px",
            padding: "8px 12px",
            background: "#2d2d3f",
            borderRadius: "8px",
          }}>
            <span style={{
              background: BADGE_COLORS[event.type] || "#64748b",
              color: "#fff",
              fontSize: "10px",
              fontFamily: "monospace",
              fontWeight: "700",
              padding: "2px 8px",
              borderRadius: "4px",
              minWidth: "100px",
              textAlign: "center",
            }}>
              {BADGE_LABELS[event.type] || event.type}
            </span>
            <span style={{ color: "#e2e8f0", fontFamily: "monospace", fontSize: "13px", flex: 1 }}>
              {event.operator}
            </span>
            <span style={{ color: "#64748b", fontFamily: "monospace", fontSize: "12px" }}>
              {event.timestamp}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
