interface StatCardsProps {
  amberCount: number;
  redCount: number;
  ppeCount: number;
  totalOps: number;
}

export default function StatCards({ amberCount, redCount, ppeCount, totalOps }: StatCardsProps) {
  const cards = [
    { label: "TOTAL OPERATORS", value: totalOps, color: "#f59e0b" },
    { label: "AMBER ALERTS", value: amberCount, color: "#f59e0b" },
    { label: "RED ALERTS", value: redCount, color: "#ef4444" },
    { label: "PPE VIOLATIONS", value: ppeCount, color: "#ef4444" },
  ];

  return (
    <div style={{ display: "flex", gap: "16px" }}>
      {cards.map((card, i) => (
        <div key={i} style={{ flex: 1, background: "#111111", border: "1px solid #262626", borderLeft: `4px solid ${card.color}`, padding: "16px 20px" }}>
          <div style={{ color: "#666666", fontSize: "10px", letterSpacing: "0.15em", marginBottom: "8px" }}>{card.label}</div>
          <div style={{ color: card.color, fontSize: "32px", fontWeight: "700" }}>{card.value}</div>
        </div>
      ))}
    </div>
  );
}
