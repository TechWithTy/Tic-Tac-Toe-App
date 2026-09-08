import type { GameApi, GameCapabilities, GameMode, GameState, Mark, MoveActor, PlayerSelection } from "~/types/game";

const API_BASE_URL = import.meta.env.VITE_API_URL ?? "http://127.0.0.1:8500";

type ApiMode =
  | "human_vs_human"
  | "human_vs_cpu"
  | "human_vs_ai"
  | "cpu_vs_human"
  | "cpu_vs_cpu"
  | "cpu_vs_ai"
  | "ai_vs_human"
  | "ai_vs_cpu"
  | "ai_vs_ai";
type ApiStatus = "in_progress" | "x_won" | "o_won" | "draw";

interface ApiGameState {
  game_id: string;
  mode: ApiMode;
  players: PlayerSelection;
  board: Mark[];
  current_player: Mark;
  status: ApiStatus;
  winner: Mark;
  turn: number;
}

interface ApiGameCapabilities {
  ai_agent_available: boolean;
}

const modeFromApi: Record<ApiMode, GameMode> = {
  human_vs_human: "human-v-human",
  human_vs_cpu: "human-v-cpu",
  human_vs_ai: "human-v-ai",
  cpu_vs_human: "cpu-v-human",
  cpu_vs_cpu: "cpu-v-cpu",
  cpu_vs_ai: "cpu-v-ai",
  ai_vs_human: "ai-agent-v-human",
  ai_vs_cpu: "ai-agent-v-cpu",
  ai_vs_ai: "ai-agent-v-ai",
};

export class GameApiError extends Error {
  public readonly status: number;

  constructor(message: string, status: number) {
    super(message);
    this.status = status;
    this.name = "GameApiError";
  }
}

function mapGameState(state: ApiGameState): GameState {
  return {
    gameId: state.game_id,
    mode: modeFromApi[state.mode],
    players: state.players,
    board: state.board,
    currentPlayer: state.current_player,
    status: state.status,
    winner: state.winner,
    winningCells: [],
  };
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...init?.headers },
  });

  if (response.ok) {
    return response.json() as Promise<T>;
  }

  const body = (await response.json().catch(() => null)) as { detail?: { message?: string } } | null;
  throw new GameApiError(body?.detail?.message ?? "The game service returned an error", response.status);
}

const jsonRequest = (method: "POST", body?: unknown): RequestInit => ({
  body: body === undefined ? undefined : JSON.stringify(body),
  method,
});

export const previewState: GameState = {
  gameId: "preview",
  mode: "human-v-human",
  players: { x: "human", o: "human" },
  board: Array.from({ length: 9 }, () => null),
  currentPlayer: "X",
  status: "in_progress",
  winner: null,
  winningCells: [],
};

export const fastApiGameApi: GameApi = {
  async createGame(players) {
    const state = await request<ApiGameState>("/games", jsonRequest("POST", { players }));
    return mapGameState(state);
  },
  async getCapabilities(): Promise<GameCapabilities> {
    const capabilities = await request<ApiGameCapabilities>("/games/capabilities");
    return { aiAgentAvailable: capabilities.ai_agent_available };
  },
  async getGameState(gameId) {
    const state = await request<ApiGameState>(`/games/${gameId}`);
    return mapGameState(state);
  },
  async makeMove(gameId, cell, actor: MoveActor = "human") {
    const state = await request<ApiGameState>(
      `/games/${gameId}/moves`,
      jsonRequest("POST", { actor, index: cell }),
    );
    return mapGameState(state);
  },
  async advanceCpuTurn(gameId) {
    const state = await request<ApiGameState>(`/games/${gameId}/cpu-move`, jsonRequest("POST"));
    return mapGameState(state);
  },
  async advanceAgentTurn(gameId) {
    const state = await request<ApiGameState>(`/games/${gameId}/agent-turn`, jsonRequest("POST"));
    return mapGameState(state);
  },
  async resetGame(gameId) {
    const state = await request<ApiGameState>(`/games/${gameId}/reset`, jsonRequest("POST"));
    return mapGameState(state);
  },
};
