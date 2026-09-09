import { RotateCcw, Sparkles, Wifi, WifiOff } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { fastApiGameApi, previewState } from "~/api/game-api";
import { GameBoard } from "~/components/game-board";
import { GameResult } from "~/components/game-result";
import { AiThinkingIndicator } from "~/components/ai-thinking-indicator";
import { PlayerSelector } from "~/components/player-selector";
import { MagicCard } from "~/components/ui/magic-card";
import { Button } from "~/components/ui/button";
import type { GameApi, GameState, PlayerSelection, PlayerType } from "~/types/game";

const defaultPlayers: PlayerSelection = { x: "human", o: "human" };
type ConnectionStatus = "disconnected" | "syncing" | "connected";

function controllerFor(state: GameState): PlayerType | null {
  if (!state.currentPlayer) return null;
  return state.players[state.currentPlayer.toLowerCase() as keyof PlayerSelection];
}

function isCpuTurn(state: GameState) {
  return state.status === "in_progress" && controllerFor(state) === "cpu";
}

function isAgentTurn(state: GameState) {
  return state.status === "in_progress" && controllerFor(state) === "ai-agent";
}

async function settleAutomatedTurns(api: GameApi, state: GameState, onStep?: (state: GameState) => void) {
  let settled = state;
  while (isCpuTurn(settled) || isAgentTurn(settled)) {
    settled = isCpuTurn(settled)
      ? await api.advanceCpuTurn(settled.gameId)
      : await api.advanceAgentTurn(settled.gameId);
    onStep?.(settled);
  }
  return settled;
}

function errorMessage(error: unknown) {
  if (error instanceof TypeError && /fetch|network/i.test(error.message)) {
    return "Unable to connect to the game server. Check that FastAPI is running at http://localhost:8000.";
  }
  return error instanceof Error ? error.message : "The game service could not be reached.";
}

function statusLabel(state: GameState) {
  if (state.status === "x_won") return "X Wins";
  if (state.status === "o_won") return "O Wins";
  if (state.status === "draw") return "Draw Game";
  return state.currentPlayer ? `${state.currentPlayer} To Move` : "Round Complete";
}

function controllerLabel(controller: PlayerType | null) {
  if (controller === "ai-agent") return "AI Agent";
  if (controller === "cpu") return "CPU";
  if (controller === "human") return "Human";
  return "—";
}

function pairingLabel(players: PlayerSelection) {
  return `${controllerLabel(players.x)} vs ${controllerLabel(players.o)}`;
}

function App() {
  const [pendingPlayers, setPendingPlayers] = useState<PlayerSelection>(defaultPlayers);
  const [gameState, setGameState] = useState<GameState>({ ...previewState });
  const [isGameStarted, setIsGameStarted] = useState(false);
  const [aiAgentAvailable, setAiAgentAvailable] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState<ConnectionStatus>("disconnected");
  const connectionAttemptRef = useRef(0);

  useEffect(() => {
    let isCurrent = true;
    const capabilityAttempt = ++connectionAttemptRef.current;
    setConnectionStatus("syncing");
    void fastApiGameApi.getCapabilities()
      .then(({ aiAgentAvailable: available }) => {
        if (isCurrent && connectionAttemptRef.current === capabilityAttempt) {
          setAiAgentAvailable(available);
          setConnectionStatus("connected");
        }
      })
      .catch(() => {
        if (isCurrent && connectionAttemptRef.current === capabilityAttempt) {
          setAiAgentAvailable(false);
          setConnectionStatus("disconnected");
        }
      });

    return () => {
      isCurrent = false;
    };
  }, []);

  const updatePlayer = (player: "x" | "o", value: PlayerType) => {
    if (value === "ai-agent" && !aiAgentAvailable) return;
    setPendingPlayers((current) => ({ ...current, [player]: value }));
  };

  const returnToSetup = async (gameId: string) => {
    await fastApiGameApi.resetGame(gameId);
    setGameState({ ...previewState, players: pendingPlayers });
    setIsGameStarted(false);
  };

  const handleStartGame = async () => {
    setError(null);
    setIsLoading(true);
    setIsGameStarted(false);
    setGameState({ ...previewState, players: pendingPlayers });
    connectionAttemptRef.current += 1;
    try {
      const createdState = await fastApiGameApi.createGame(pendingPlayers);
      setGameState(createdState);
      setIsGameStarted(true);
      const settledState = await settleAutomatedTurns(fastApiGameApi, createdState, setGameState);
      setConnectionStatus("connected");
      setGameState(settledState);
    } catch (requestError) {
      if (requestError instanceof TypeError && /fetch|network/i.test(requestError.message)) {
        setConnectionStatus("disconnected");
      }
      setError(errorMessage(requestError));
    } finally {
      setIsLoading(false);
    }
  };

  const handleCellSelect = async (cell: number) => {
    if (isLoading || !isGameStarted || gameState.status !== "in_progress" || controllerFor(gameState) !== "human") return;

    setIsLoading(true);
    setError(null);
    connectionAttemptRef.current += 1;
    try {
      const nextState = await fastApiGameApi.makeMove(gameState.gameId, cell);
      setGameState(nextState);
      const settledState = await settleAutomatedTurns(fastApiGameApi, nextState);
      setConnectionStatus("connected");
      setGameState(settledState);
    } catch (requestError) {
      if (requestError instanceof TypeError && /fetch|network/i.test(requestError.message)) {
        setConnectionStatus("disconnected");
      }
      setError(errorMessage(requestError));
    } finally {
      setIsLoading(false);
    }
  };

  const handleReset = async () => {
    if (isLoading || !isGameStarted) return;

    setError(null);
    setIsLoading(true);
    connectionAttemptRef.current += 1;
    try {
      await returnToSetup(gameState.gameId);
      setConnectionStatus("connected");
    } catch (requestError) {
      if (requestError instanceof TypeError && /fetch|network/i.test(requestError.message)) {
        setConnectionStatus("disconnected");
      }
      setError(errorMessage(requestError));
    } finally {
      setIsLoading(false);
    }
  };

  const currentController = controllerFor(gameState);
  const isAiThinking = isLoading && currentController === "ai-agent";
  const boardDisabled = isLoading || !isGameStarted || gameState.status !== "in_progress" || currentController !== "human";
  const gameStatus = statusLabel(gameState);
  const connectionLabel = connectionStatus === "syncing" || isLoading ? "Syncing" : connectionStatus === "connected" ? "FastAPI Connected" : "Disconnected";

  return (
    <main className="min-h-screen overflow-hidden bg-[#0b0d12] text-[#f7f7f2]">
      <div aria-hidden="true" className="pointer-events-none fixed inset-0 bg-[radial-gradient(circle_at_20%_10%,rgba(216,255,86,0.08),transparent_28%),radial-gradient(circle_at_90%_80%,rgba(255,138,101,0.08),transparent_25%)]" />
      <div className="relative mx-auto flex min-h-screen w-full max-w-7xl flex-col px-5 py-6 sm:px-8 lg:px-12">
        <header className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex flex-col items-center gap-3 text-center sm:flex-row sm:text-left">
            <span className="flex h-10 w-10 items-center justify-center rounded-2xl bg-[#d8ff56] text-[#101219] shadow-[0_0_2rem_rgba(216,255,86,0.18)]">
              <Sparkles aria-hidden="true" className="h-5 w-5" />
            </span>
            <div className="text-center sm:text-left">
              <p className="text-sm font-semibold tracking-[0.22em] text-white">GRIDLINE</p>
              <p className="text-xs text-white/40">A server-led tic-tac-toe room</p>
            </div>
          </div>
          <span className="inline-flex self-center items-center gap-2 rounded-full border border-white/10 bg-white/[0.03] px-3 py-1.5 text-center text-xs text-white/45 sm:self-auto">
            {connectionStatus === "connected" && !isLoading ? <Wifi aria-hidden="true" className="h-3.5 w-3.5 text-[#d8ff56]" /> : <WifiOff aria-hidden="true" className="h-3.5 w-3.5 text-[#ff8a65]" />}
            {connectionLabel}
          </span>
        </header>

        <section className="grid flex-1 items-center gap-10 py-12 lg:grid-cols-[minmax(0,0.85fr)_minmax(28rem,1.15fr)] lg:gap-16 lg:py-16">
          <div className="max-w-xl text-center sm:text-left">
            <p className="mb-5 flex items-center justify-center gap-2 text-xs font-semibold uppercase tracking-[0.24em] text-[#d8ff56] sm:justify-start"><span className="h-px w-8 bg-[#d8ff56]" />Make your mark</p>
            <h1 className="max-w-lg text-center text-5xl font-semibold leading-[0.98] tracking-[-0.055em] text-white sm:text-left sm:text-7xl">Small board.<br /><span className="text-white/35">Big decisions.</span></h1>
            <p className="mt-7 max-w-md text-center text-base leading-7 text-white/55 sm:text-left">A focused arena for human play, deterministic opponents, and agent proposals validated by the game server.</p>

            <div className="mt-10 rounded-3xl border border-white/10 bg-white/[0.025] p-5 backdrop-blur-sm sm:p-6">
              <div className="flex items-end justify-between gap-4">
                <div>
                  <h2 className="text-lg font-semibold text-white">Choose your players</h2>
                  <p className="mt-1 text-sm text-white/45">Each controller is selected independently.</p>
                </div>
                <span className="hidden rounded-full bg-white/5 px-3 py-1 text-xs text-white/45 sm:inline-flex">{pairingLabel(pendingPlayers)}</span>
              </div>
              <div className="mt-5 grid min-w-0 grid-cols-1 gap-4 md:grid-cols-2">
                <PlayerSelector player="x" value={pendingPlayers.x} onChange={(value) => updatePlayer("x", value)} aiAgentAvailable={aiAgentAvailable} disabled={isGameStarted || isLoading} />
                <PlayerSelector player="o" value={pendingPlayers.o} onChange={(value) => updatePlayer("o", value)} aiAgentAvailable={aiAgentAvailable} disabled={isGameStarted || isLoading} />
              </div>
              <Button aria-label={isGameStarted ? "Game Started" : "Start game"} className="mt-5 h-11 w-full rounded-xl bg-[#d8ff56] font-semibold text-[#101219] hover:bg-[#e5ff91] disabled:bg-white/10 disabled:text-white/40" disabled={isLoading || isGameStarted} onClick={handleStartGame}>
                {isGameStarted ? "Game Started" : isLoading ? "Starting…" : "Start game"}
              </Button>
            </div>
          </div>

          <MagicCard className="rounded-[2rem] bg-[#11141c] shadow-2xl shadow-black/30" gradientColor="#d8ff56" gradientFrom="#d8ff56" gradientTo="#ff8a65" gradientOpacity={0.2}>
            <div className="p-5 sm:p-7">
              <div className="mb-6 flex items-start justify-between gap-4">
                <div>
                  <p className="text-xs font-semibold uppercase tracking-[0.2em] text-white/35">Round 01 · {pairingLabel(gameState.players)}</p>
                  <h2 className="mt-2 text-center text-2xl font-semibold tracking-tight text-white sm:text-left">{!isGameStarted ? "Ready when you are" : gameState.status === "in_progress" ? "Your next move" : "Round complete"}</h2>
                </div>
                <Button aria-label="Reset game" className="h-10 rounded-xl border-white/10 bg-white/5 px-3 text-white/65 hover:bg-white/10 hover:text-white" disabled={isLoading || !isGameStarted} onClick={handleReset} variant="outline">
                  <RotateCcw aria-hidden="true" className="h-4 w-4" />
                  <span className="sr-only sm:not-sr-only">Reset</span>
                </Button>
              </div>

              <div aria-live="polite" className="mx-auto mb-5 flex w-full max-w-[34rem] flex-col items-center justify-center gap-2 rounded-2xl border border-[#d8ff56]/15 bg-[#d8ff56]/[0.06] px-4 py-4 text-center">
                <p className="text-xs uppercase tracking-[0.18em] text-[#d8ff56]/70">Current Turn</p>
                <p className="text-sm font-medium text-white">{gameStatus} <span className="font-normal text-white/45">· Server State</span></p>
                <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-[#d8ff56] text-lg font-semibold text-[#101219]">{gameState.currentPlayer ?? gameState.winner ?? "—"}</span>
              </div>

              <GameBoard disabled={boardDisabled} gameState={gameState} onCellSelect={handleCellSelect} />

              <GameResult status={gameState.status} winner={gameState.winner} onRestart={handleReset} />

              {isAiThinking && <AiThinkingIndicator />}

              <div className="mt-5 flex min-w-0 flex-col items-center gap-3 text-center text-sm leading-6 text-white/45 sm:flex-row sm:items-start sm:text-left">
                <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-lg bg-white/5 text-white/40 sm:mt-0.5"><Wifi aria-hidden="true" className="h-4 w-4" /></span>
                <p className="min-w-0 break-words">{!isGameStarted ? "Choose a controller for each player, then start the game." : isLoading ? "Syncing With The Game Server…" : currentController === "ai-agent" ? `Waiting For The AI Agent To Propose A ${gameState.currentPlayer} Move Through MCP.` : currentController === "cpu" ? "The CPU Is Thinking…" : gameState.status === "in_progress" ? "Moves Are Validated And Applied By FastAPI." : "The Server Has Closed This Board. Reset To Play Again."}</p>
              </div>

              {error && (
                <div aria-live="assertive" className="mt-4 rounded-2xl border border-[#ff8a65]/30 bg-[#ff8a65]/10 px-4 py-3 text-sm text-[#ffd0c2]" role="alert">
                  {error}
                </div>
              )}
            </div>
          </MagicCard>
        </section>

        <footer className="flex flex-col items-center gap-2 border-t border-white/10 pt-5 text-center text-xs text-white/30 sm:flex-row sm:items-center sm:justify-between sm:text-left">
          <span>Server proposes the truth. The client presents it clearly.</span>
          <span>3 × 3 · X starts · no second rules engine</span>
        </footer>
      </div>
    </main>
  );
}

export default App;
