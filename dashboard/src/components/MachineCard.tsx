import { RadialBarChart, RadialBar, PolarAngleAxis } from "recharts";

type State = "GREEN" | "AMBER" | "RED";

interface MachineCardProps {
  operatorId: string;
  cls: number;
  state: State;
}

const STATE_COLORS: Record<State, string> = {
  GREEN: "#22c55e",
  AMBER: "#f59e0b",
  RED: "#ef4444",
};

export default function MachineCard({ operatorId, cls, state }: MachineCardProps) {
  const color = STATE_COLORS[state];
  const data = [{ value: cls }];

  return (
    <div style={{
      background: "#1e1e2e",
      borderRadius: "16px",
      padding: "24px",
      width: "240px",
      display: "flex",
      flexDirection: "column",
      alignItems: "center",
      gap: "12px",
      boxShadow: "0 4px 24px rgba(0,0,0,0.4)",
    }}>
      <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
        <div style={{
          width: "10px",
          height: "10px",
          borderRadius: "50%",
          backgroundColor: color,
          boxShadow: `0 0 6px ${color}`,
        }} />
        <span style={{ color: "#e2e8f0", fontFamily: "monospace", fontSize: "14px" }}>
          {operatorId}
        </span>
      </div>

      <div style={{ position: "relative" }}>
        <RadialBarChart
          width={180}
          height={180}
          cx={90}
          cy={90}
          innerRadius={60}
          outerRadius={85}
          startAngle={210}
          endAngle={-30}
          data={data}
        >
          <PolarAngleAxis type="number" domain={[0, 100]} tick={false} />
          <RadialBar
            dataKey="value"
            cornerRadius={6}
            fill="#2d2d3f"
            background={{ fill: "#2d2d3f" }}
            data={[{ value: 100 }]}
          />
          <RadialBar
            dataKey="value"
            cornerRadius={6}
            fill={color}
            data={data}
          />
        </RadialBarChart>

        <div style={{
          position: "absolute",
          top: "50%",
          left: "50%",
          transform: "translate(-50%, -50%)",
          textAlign: "center",
        }}>
          <div style={{ color: "#ffffff", fontSize: "28px", fontWeight: "700", fontFamily: "monospace" }}>
            {cls}
          </div>
          <div style={{ color: "#64748b", fontSize: "11px", fontFamily: "monospace" }}>
            CLS
          </div>
        </div>
      </div>
    </div>
  );
}
