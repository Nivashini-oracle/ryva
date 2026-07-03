import type { EventEntry } from "../App";

const BADGE_COLORS: Record<string, string> = {
  GREEN: "#22c55e", AMBER: "#f59e0b", RED: "#ef4444",
  "PPE VIOLATION": "#ef4444", "PPE CLEARED": "#22c55e", SOS: "#a855f7",
};

const DUMMY_EVENTS: EventEntry[] = [
  { id: 1, type: "RED",           operator: "R001", timestamp: "14:45:02" },
  { id: 2, type: "PPE VIOLATION", operator: "R001", timestamp: "14:38:21" },
  { id: 3, type: "PPE CLEARED",   operator: "R001", timestamp: "14:35:00" },
  { id: 4, type: "AMBER",         operator: "R002", timestamp: "14:23:11" },
  { id: 5, type: "GREEN",         operator: "R002", timestamp: "14:20:00" },
  { id: 6, type: "SOS",           operator: "R003", timestamp: "09:01:47" },
];

export default function EventPanel({ events }: { events?: EventEntry[] }) {
  const display = events && events.length > 0 ? events : DUMMY_EVENTS;
  return (
    <div style={{ background: "#111111", border: "1px solid #262626", padding: "20px", height: "100%", display: "flex", flexDirection: "column", gap: "12px" }}>
      <div style={{ color: "#666666", fontSize: "10px", letterSpacing: "0.15em" }}>EVENT LOG</div>
      <div style={{ flex: 1, overflowY: "auto", display: "flex", flexDirection: "column", gap: "8px" }}>
        {display.map(event => (
          <div key={event.id} style={{ display: "flex", flexDirection: "column", gap: "4px", padding: "10px 12px", background: "#0a0a0a", borderLeft: `3px solid ${BADGE_COLORS[event.type] || "#666666"}` }}>
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
              <span style={{ color: BADGE_COLORS[event.type] || "#666666", fontSize: "10px", fontWeight: "700", letterSpacing: "0.05em" }}>{event.type}</span>
              <span style={{ color: "#666666", fontSize: "10px" }}>{event.timestamp}</span>
            </div>
            <span style={{ color: "#999999", fontSize: "11px" }}>{event.operator}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
