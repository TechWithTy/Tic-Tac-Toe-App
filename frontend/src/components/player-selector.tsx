import type { PlayerType } from "~/types/game";
import { playerOptions } from "~/components/player-options";

interface PlayerSelectorProps {
  player: "x" | "o";
  value: PlayerType;
  onChange: (value: PlayerType) => void;
  aiAgentAvailable?: boolean;
  disabled?: boolean;
}

export function PlayerSelector({ player, value, onChange, aiAgentAvailable = false, disabled: selectionDisabled = false }: PlayerSelectorProps) {
  const mark = player.toUpperCase();

  return (
    <fieldset aria-label={`Player ${mark}`} className="min-w-0 space-y-3">
      <legend className="flex items-center justify-center gap-2 text-center text-sm font-medium text-white/70 sm:justify-start sm:text-left">
        <span className="flex h-7 w-7 items-center justify-center rounded-lg bg-white/10 text-xs font-semibold text-[#d8ff56]">
          {mark}
        </span>
        Player {mark}
      </legend>
      <div className="space-y-2">
        {playerOptions.map(({ id, label, description, icon: Icon }) => {
          const selected = value === id;
          const disabled = selectionDisabled || (id === "ai-agent" && !aiAgentAvailable);

          return (
            <label
              aria-disabled={disabled}
              className={`relative flex items-center gap-3 rounded-2xl border p-3 transition ${disabled ? "cursor-not-allowed border-white/5 bg-white/[0.015] opacity-45" : `cursor-pointer ${selected ? "border-[#d8ff56]/60 bg-[#d8ff56]/10" : "border-white/10 bg-white/[0.03] hover:border-white/25 hover:bg-white/[0.06]"}`}`}
              key={id}
              title={disabled ? "AI Agent unavailable until the service is connected" : undefined}
            >
              <input
                aria-label={label}
                checked={selected}
                className="sr-only"
                disabled={disabled}
                name={`player-${player}`}
                onChange={() => onChange(id)}
                type="radio"
                value={id}
              />
              <span className={`pointer-events-none flex h-9 w-9 shrink-0 items-center justify-center rounded-xl ${selected && !disabled ? "bg-[#d8ff56] text-[#101219]" : "bg-white/10 text-white/55"}`}>
                <Icon aria-hidden="true" className="h-4 w-4" />
              </span>
              <span className="pointer-events-none min-w-0 flex-1 text-center sm:text-left">
                <span className={`block text-sm font-medium ${disabled ? "text-white/55" : "text-white"}`}>{label}</span>
                <span className="mt-0.5 block break-words text-xs text-white/45 sm:truncate">{description}</span>
              </span>
              <span aria-hidden="true" className={`pointer-events-none ml-auto h-2 w-2 rounded-full ${selected && !disabled ? "bg-[#d8ff56]" : "bg-white/15"}`} />
            </label>
          );
        })}
      </div>
    </fieldset>
  );
}
