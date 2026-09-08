export type GameMode =
  | "human-v-human"
  | "human-v-cpu"
  | "human-v-ai"
  | "cpu-v-human"
  | "cpu-v-cpu"
  | "cpu-v-ai"
  | "ai-agent-v-human"
  | "ai-agent-v-cpu"
  | "ai-agent-v-ai";

export type PlayerType = "human" | "cpu" | "ai-agent";

export interface PlayerSelection {
  x: PlayerType;
  o: PlayerType;
}

export type Mark = "X" | "O" | null;
export type GameStatus = "in_progress" | "x_won" | "o_won" | "draw";
export type MoveActor = "human" | "ai-agent";

export interface GameState {
  gameId: string;
  mode: GameMode;
  players: PlayerSelection;
  board: readonly Mark[];
  currentPlayer: Mark;
  status: GameStatus;
  winner: Mark;
  winningCells: readonly number[];
}

export interface GameApi {
  createGame(players: PlayerSelection): Promise<GameState>;
  getCapabilities(): Promise<GameCapabilities>;
  getGameState(gameId: string): Promise<GameState>;
  makeMove(gameId: string, cell: number, actor?: MoveActor): Promise<GameState>;
  advanceCpuTurn(gameId: string): Promise<GameState>;
  advanceAgentTurn(gameId: string): Promise<GameState>;
  resetGame(gameId: string): Promise<GameState>;
}

export interface GameCapabilities {
  aiAgentAvailable: boolean;
}

