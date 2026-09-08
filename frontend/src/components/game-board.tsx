import { cn } from "~/lib/utils";
import type { GameState } from "~/types/game";

interface GameBoardProps {
  gameState: GameState;
  disabled?: boolean;
  onCellSelect: (cell: number) => void;
}

export function GameBoard({ gameState, disabled = false, onCellSelect }: GameBoardProps) {
  const winningCells = new Set(gameState.winningCells);
  const boardIsComplete = gameState.status !== "in_progress";

  return (
    <div
      aria-label="Tic-tac-toe board"
      className="grid aspect-square w-full max-w-[34rem] grid-cols-3 gap-2 rounded-[1.5rem] bg-white/5 p-2 sm:gap-3 sm:p-3"
      role="grid"
    >
      {gameState.board.map((mark, index) => {
        const isWinningCell = winningCells.has(index);
        const isDisabled = disabled || boardIsComplete || mark !== null;

        return (
          <div key={index} role="gridcell">
            <button
              aria-label={`Cell ${index + 1}${mark ? `, ${mark}` : ""}`}
              aria-selected={isWinningCell}
              className={cn(
                "group relative flex min-h-20 w-full items-center justify-center rounded-[1.1rem] border border-white/10 bg-[#171a23] text-5xl font-semibold transition duration-200 sm:text-6xl",
                "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#d8ff56] focus-visible:ring-offset-2 focus-visible:ring-offset-[#101219]",
                "hover:border-white/25 hover:bg-[#202532] disabled:cursor-not-allowed disabled:hover:translate-y-0",
                mark === "X" && "text-[#d8ff56]",
                mark === "O" && "text-[#ff8a65]",
                isWinningCell && "border-[#d8ff56]/70 bg-[#d8ff56]/10 shadow-[0_0_2rem_rgba(216,255,86,0.18)]",
                !mark && !isDisabled && "text-white/20"
              )}
              disabled={isDisabled}
              onClick={() => onCellSelect(index)}
              type="button"
            >
              <span aria-hidden="true">{mark}</span>
              {!mark && !isDisabled && (
                <span aria-hidden="true" className="absolute inset-0 m-auto h-2 w-2 rounded-full bg-[#d8ff56] opacity-0 shadow-none transition-opacity duration-150 group-hover:opacity-100" />
              )}
            </button>
          </div>
        );
      })}
    </div>
  );
}

