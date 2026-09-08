import { Bot, BrainCircuit, CircleUserRound } from "lucide-react";
import type { ComponentType } from "react";
import type { PlayerType } from "~/types/game";

export interface PlayerOption {
  id: PlayerType;
  label: string;
  description: string;
  icon: ComponentType<{ className?: string }>;
}

export const playerOptions: readonly PlayerOption[] = [
  { id: "human", label: "Human", description: "Choose each move", icon: CircleUserRound },
  { id: "cpu", label: "CPU", description: "Perfect deterministic player", icon: Bot },
  { id: "ai-agent", label: "AI Agent", description: "Proposes through MCP", icon: BrainCircuit },
];
