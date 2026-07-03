type ShiftRow = {
  operator: string;
  amberMinutes: number;
  redEvents: number;
  ppeViolations: number;
  status: "Cleared" | "Needs Attention";
};

interface SidebarProps {
  connected: boolean;
  dateStr: string;
  shiftRows: ShiftRow[];
}

export default function Sidebar({ shiftRows }: SidebarProps) {
  const now = new Date();
  const timeStr = now.toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit" });

  return (
    <div style={{ width: "clamp(180px, 14vw, 260px)", flexShrink: 0, background: "#0d0d0d", borderRight: "1px solid #262626", display: "flex", flexDirection: "column", padding: "24px 0", minHeight: "100vh" }}>
      <div style={{ padding: "0 20px 28px", borderBottom: "1px solid #262626" }}>
        <div style={{ color: "#f59e0b", fontSize: "22px", fontWeight: "700", letterSpacing: "0.15em" }}>RYVA</div>
        <div style={{ color: "#666666", fontSize: "10px", letterSpacing: "0.15em", marginTop: "2px" }}>SAFETY INTELLIGENCE</div>
      </div>
      <div style={{ padding: "20px", borderBottom: "1px solid #262626" }}>
        <div style={{ color: "#666666", fontSize: "10px", letterSpacing: "0.15em", marginBottom: "8px" }}>CURRENT SHIFT</div>
        <div style={{ color: "#e5e5e5", fontSize: "13px", marginBottom: "4px" }}>Shift 2</div>
        <div style={{ color: "#666666", fontSize: "11px", marginBottom: "2px" }}>14:00 - 22:00</div>
        <div style={{ color: "#666666", fontSize: "11px" }}>{timeStr}</div>
      </div>
      <div style={{ padding: "20px", borderBottom: "1px solid #262626", flex: 1 }}>
        <div style={{ color: "#666666", fontSize: "10px", letterSpacing: "0.15em", marginBottom: "12px" }}>OPERATORS</div>
        {shiftRows.map((row, i) => (
          <div key={i} style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "8px 10px", marginBottom: "6px", background: "#111111", border: "1px solid #262626", borderLeft: `3px solid ${row.status === "Cleared" ? "#22c55e" : "#f59e0b"}` }}>
            <span style={{ color: "#e5e5e5", fontSize: "12px" }}>{row.operator}</span>
            <span style={{ fontSize: "9px", fontWeight: "700", padding: "2px 6px", color: row.status === "Cleared" ? "#22c55e" : "#f59e0b" }}>
              {row.status === "Cleared" ? "OK" : "WATCH"}
            </span>
          </div>
        ))}
      </div>
      <div style={{ padding: "20px" }}>
        <div style={{ color: "#666666", fontSize: "10px", letterSpacing: "0.15em", marginBottom: "12px" }}>SYSTEM</div>
        {[{ label: "Vision", ok: true }, { label: "BLE Wristband", ok: true }, { label: "CLS Engine", ok: true }, { label: "WebSocket", ok: true }].map((s, i) => (
          <div key={i} style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "8px" }}>
            <span style={{ color: "#666666", fontSize: "11px" }}>{s.label}</span>
            <span style={{ width: "6px", height: "6px", borderRadius: "50%", background: s.ok ? "#22c55e" : "#ef4444", display: "inline-block" }} />
          </div>
        ))}
      </div>
    </div>
  );
}
