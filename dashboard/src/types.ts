export type State = "GREEN" | "AMBER" | "RED";

export type EventEntry = {
  id: number;
  type: "AMBER" | "RED" | "PPE VIOLATION" | "SOS" | "PPE CLEARED" | "GREEN";
  operator: string;
  timestamp: string;
};

export type OperatorData = {
  operatorId: string;
  cls: number;
  state: State;
  etaMinutes: number | null;
};

