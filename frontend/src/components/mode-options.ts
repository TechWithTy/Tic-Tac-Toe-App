import { Bot, BrainCircuit, CircleUserRound, Users } from "lucide-react";
import type { ComponentType } from "react";
import type { GameMode } from "~/types/game";

export interface ModeOption {
  id: GameMode;
  label: string;
  description: string;
  icon: ComponentType<{ className?: string }>;
}

export const modeOptions: readonly ModeOption[] = [
  { id: "human-v-human", label: "Human vs Human", description: "Take turns locally", icon: Users },
  { id: "human-v-cpu", label: "Human vs CPU", description: "Challenge the perfect player", icon: CircleUserRound },
  { id: "cpu-v-cpu", label: "CPU vs CPU", description: "Watch optimal play unfold", icon: Bot },
  { id: "ai-agent-v-cpu", label: "AI Agent vs CPU", description: "Model proposes, server validates", icon: BrainCircuit },
];

