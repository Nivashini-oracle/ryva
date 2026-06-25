type ShiftRow = {
  operator: string;
  amberMinutes: number;
  redEvents: number;
  ppeViolations: number;
  status: "Cleared" | "Needs Attention";
};

const DUMMY_SHIFT: ShiftRow[] = [
  { operator: "Operator Rajan", amberMinutes: 18, redEvents: 2, ppeViolations: 1, status: "Needs Attention" },
  { operator: "Operator Kumar", amberMinutes: 5,  redEvents: 0, ppeViolations: 0, status: "Cleared" },
  { operator: "Operator Singh", amberMinutes: 11, redEvents: 1, ppeViolations: 2, status: "Needs Attention" },
];

export default function ShiftSummary() {
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
        SHIFT SUMMARY
      </h2>
      <table style={{ width: "100%", borderCollapse: "collapse", fontFamily: "monospace", fontSize: "13px" }}>
        <thead>
          <tr style={{ color: "#64748b", textAlign: "left" }}>
            <th style={{ padding: "8px 12px" }}>Operator</th>
            <th style={{ padding: "8px 12px" }}>AMBER Min</th>
            <th style={{ padding: "8px 12px" }}>RED Events</th>
            <th style={{ padding: "8px 12px" }}>PPE</th>
            <th style={{ padding: "8px 12px" }}>Status</th>
          </tr>
        </thead>
        <tbody>
          {DUMMY_SHIFT.map((row, i) => (
            <tr key={i} style={{ borderTop: "1px solid #2d2d3f" }}>
              <td style={{ padding: "10px 12px", color: "#e2e8f0" }}>{row.operator}</td>
              <td style={{ padding: "10px 12px", color: "#f59e0b" }}>{row.amberMinutes}</td>
              <td style={{ padding: "10px 12px", color: "#ef4444" }}>{row.redEvents}</td>
              <td style={{ padding: "10px 12px", color: "#ef4444" }}>{row.ppeViolations}</td>
              <td style={{ padding: "10px 12px" }}>
                <span style={{
                  color: row.status === "Cleared" ? "#22c55e" : "#f59e0b",
                  fontWeight: "700",
                }}>
                  {row.status}
                </span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
