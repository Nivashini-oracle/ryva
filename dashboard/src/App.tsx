import MachineCard from "./components/MachineCard";

function App() {
  return (
    <div style={{
      minHeight: "100vh",
      background: "#0f0f1a",
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
    }}>
      <MachineCard
        operatorId="MACHINE-01"
        cls={72}
        state="AMBER"
      />
    </div>
  );
}

export default App;
