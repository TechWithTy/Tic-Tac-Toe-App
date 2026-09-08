import { motion } from "motion/react";
import { RotateCcw, Sparkles, Trophy } from "lucide-react";
import { Button } from "~/components/ui/button";
import type { GameStatus, Mark } from "~/types/game";

interface GameResultProps {
  status: GameStatus;
  winner: Mark;
  onRestart: () => void;
}

const confettiPieces = [
  { left: "5%", color: "#d8ff56", x: -28, rotate: -35 },
  { left: "15%", color: "#ff8a65", x: 22, rotate: 24 },
  { left: "27%", color: "#f7f7f2", x: -18, rotate: 48 },
  { left: "39%", color: "#d8ff56", x: 30, rotate: -20 },
  { left: "51%", color: "#ff8a65", x: -24, rotate: 36 },
  { left: "63%", color: "#f7f7f2", x: 20, rotate: -42 },
  { left: "75%", color: "#d8ff56", x: -16, rotate: 18 },
  { left: "87%", color: "#ff8a65", x: 28, rotate: -28 },
];

function ConfettiBurst() {
  return (
    <div className="pointer-events-none absolute inset-x-3 top-0 h-24 overflow-hidden" role="img" aria-label="Winner confetti">
      {confettiPieces.map((piece, index) => (
        <motion.span
          key={`${piece.left}-${index}`}
          className="absolute top-0 h-3 w-1.5 rounded-full"
          style={{ backgroundColor: piece.color, left: piece.left }}
          initial={{ opacity: 0, y: -12, rotate: 0 }}
          animate={{ opacity: [0, 1, 1, 0], y: [0, 24 + index * 4, 58 + index * 3, 96], x: [0, piece.x, piece.x * 1.4, piece.x * 1.7], rotate: [0, piece.rotate, piece.rotate * 2, piece.rotate * 3] }}
          transition={{ duration: 2.2, delay: index * 0.06, ease: "easeOut" }}
        />
      ))}
    </div>
  );
}

export function GameResult({ status, winner, onRestart }: GameResultProps) {
  if (status === "in_progress") return null;

  const hasWinner = status === "x_won" || status === "o_won";

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6">
      <motion.div
        aria-hidden="true"
        className="absolute inset-0 bg-[#050608]/75 backdrop-blur-sm"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.25 }}
      />
      <motion.section
        role="dialog"
        aria-modal="true"
        aria-labelledby="game-result-heading"
        aria-describedby="game-result-description"
        className="relative w-full max-w-md overflow-hidden rounded-3xl border border-[#d8ff56]/25 bg-[#11141c] px-5 py-7 text-center shadow-2xl shadow-black/50 sm:px-8 sm:py-9"
        initial={{ opacity: 0, y: 18, scale: 0.96 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        transition={{ duration: 0.35, ease: "easeOut" }}
      >
        {hasWinner && <ConfettiBurst />}
        <motion.div
          animate={hasWinner ? { scale: [1, 1.08, 1] } : { rotate: [0, -2, 2, 0] }}
          transition={{ duration: 1.4, repeat: Infinity, repeatDelay: 1.6 }}
          className="relative mx-auto flex h-12 w-12 items-center justify-center rounded-2xl bg-[#d8ff56] text-[#101219]"
        >
          {hasWinner ? <Trophy aria-hidden="true" className="h-6 w-6" /> : <Sparkles aria-hidden="true" className="h-6 w-6" />}
        </motion.div>
        <p className="relative mt-4 text-xs font-semibold uppercase tracking-[0.2em] text-[#d8ff56]/70">Round Complete</p>
        <h3 id="game-result-heading" className="relative mt-2 text-3xl font-semibold tracking-tight text-white">
          {hasWinner ? `Winner: ${winner}` : "Draw Game"}
        </h3>
        <p id="game-result-description" className="relative mt-2 text-sm text-white/50">
          {hasWinner ? `${winner} closed out the board.` : "Perfectly matched. Nobody takes the round."}
        </p>
        <Button aria-label="Restart game" className="relative mt-5 h-10 rounded-xl bg-[#d8ff56] px-5 font-semibold text-[#101219] hover:bg-[#e5ff91]" onClick={onRestart}>
          <RotateCcw aria-hidden="true" className="mr-2 h-4 w-4" />
          Restart game
        </Button>
      </motion.section>
    </div>
  );
}
