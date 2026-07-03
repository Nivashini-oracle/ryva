import { RadialBarChart, RadialBar, PolarAngleAxis } from "recharts";
import type { OperatorData } from "../App";

const STATE_COLORS = { GREEN: "#22c55e", AMBER: "#f59e0b", RED: "#ef4444" };

function TickRing({ color }: { color: string }) {
  const ticks = Array.from({ length: 24 });
  return (
    <div style={{ position: "absolute", top: 0, left: 0, width: "150px", height: "150px" }}>
      {ticks.map((_, i) => {
        const angle = (i / 24) * 360;
        const major = i % 6 === 0;
        return (
          <div key={i} style={{
            position: "absolute", top: "50%", left: "50%",
            width: major ? "2px" : "1px", height: major ? "8px" : "5px",
            background: major ? color : "#333333",
            transform: `rotate(${angle}deg) translateY(-72px)`,
            transformOrigin: "center top",
          }} />
        );
      })}
    </div>
  );
}

function MachineCard({ op }: { op: OperatorData }) {
  const color = STATE_COLORS[op.state];
  const stripe = `repeating-linear-gradient(45deg, ${color}, ${color} 6px, #0a0a0a 6px, #0a0a0a 12px)`;
  return (
    <div style={{ background: "#111111", border: "1px solid #262626", display: "flex", flexDirection: "column", alignItems: "center", gap: "14px" }}>
      <div style={{ height: "5px", width: "100%", background: stripe }} />
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", width: "100%", padding: "8px 20px 0" }}>
        <span style={{ color: "#e5e5e5", fontSize: "14px", fontWeight: "700", letterSpacing: "0.05em" }}>{op.operatorId}</span>
        <span style={{ fontSize: "9px", fontWeight: "700", padding: "4px 9px", color: color, border: `1px solid ${color}`, letterSpacing: "0.1em" }}>{op.state}</span>
      </div>
      <div style={{ position: "relative", width: "150px", height: "150px", margin: "6px 0" }}>
        <TickRing color={color} />
        <RadialBarChart width={150} height={150} cx={75} cy={75} innerRadius={45} outerRadius={62} startAngle={210} endAngle={-30} data={[{ value: op.cls }]}>
          <PolarAngleAxis type="number" domain={[0, 100]} tick={false} />
          <RadialBar dataKey="value" cornerRadius={0} fill={color} background={{ fill: "#1a1a1a" }} />
        </RadialBarChart>
        <div style={{ position: "absolute", top: "50%", left: "50%", transform: "translate(-50%, -50%)", textAlign: "center" }}>
          <div style={{ color: "#ffffff", fontSize: "26px", fontWeight: "700" }}>{Math.round(op.cls)}</div>
          <div style={{ color: "#666666", fontSize: "10px", letterSpacing: "0.1em" }}>CLS</div>
        </div>
      </div>
      {op.etaMinutes !== null && op.state !== "RED" && (
        <div style={{ background: "#150a00", border: "1px solid #f59e0b", padding: "6px 10px", width: "calc(100% - 40px)", textAlign: "center", marginBottom: "20px" }}>
          <span style={{ color: "#f59e0b", fontSize: "10px" }}>PROJECTED RED IN {op.etaMinutes} MIN</span>
        </div>
      )}
      {(op.etaMinutes === null || op.state === "RED") && <div style={{ paddingBottom: "20px" }} />}
    </div>
  );
}

export default function MachineGrid({ operators }: { operators: OperatorData[] }) {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "18px" }}>
      <div style={{ color: "#666666", fontSize: "10px", letterSpacing: "0.15em" }}>OPERATOR STATUS</div>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(200px, 1fr))", gap: "20px" }}>
        {operators.map(op => <MachineCard key={op.operatorId} op={op} />)}
      </div>
    </div>
  );
}
