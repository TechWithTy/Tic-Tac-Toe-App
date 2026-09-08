import { motion } from "motion/react";

export function AiThinkingIndicator() {
  return (
    <div
      aria-label="AI Agent Is Thinking"
      aria-live="polite"
      className="mb-4 flex w-full min-w-0 flex-wrap items-center justify-center gap-2 rounded-2xl border border-[#d8ff56]/15 bg-[#d8ff56]/[0.04] px-4 py-3 text-center text-xs sm:text-sm"
      role="status"
    >
      <motion.span
        animate={{ backgroundPosition: ["0% 50%", "100% 50%", "0% 50%"] }}
        aria-hidden="true"
        className="bg-[length:200%_auto] bg-gradient-to-r from-[#d8ff56] via-white to-[#ff8a65] bg-clip-text font-semibold text-transparent"
        transition={{ duration: 2.4, ease: "easeInOut", repeat: Infinity }}
      >
        AI Agent Is Thinking
      </motion.span>
      <span aria-hidden="true" className="inline-flex gap-1">
        {[0, 1, 2].map((dot) => (
          <motion.span
            animate={{ opacity: [0.3, 1, 0.3], y: [0, -2, 0] }}
            className="h-1.5 w-1.5 rounded-full bg-[#d8ff56]"
            key={dot}
            transition={{ delay: dot * 0.16, duration: 1.1, repeat: Infinity, ease: "easeInOut" }}
          />
        ))}
      </span>
    </div>
  );
}
