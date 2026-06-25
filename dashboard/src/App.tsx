import MachineCard from "./components/MachineCard";
import EventLog from "./components/EventLog";
import ShiftSummary from "./components/ShiftSummary";

function App() {
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
      <h1 style={{ color: "#e2e8f0", fontFamily: "monospace", fontSize: "18px", letterSpacing: "0.2em" }}>
        RYVA — SUPERVISOR DASHBOARD
      </h1>
      <MachineCard operatorId="MACHINE-01" cls={72} state="AMBER" />
      <EventLog />
      <ShiftSummary />
    </div>
  );
}

export default App;
