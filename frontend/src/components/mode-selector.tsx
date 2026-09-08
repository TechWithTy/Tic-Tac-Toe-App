import type { GameMode } from "~/types/game";
import { modeOptions } from "~/components/mode-options";

interface ModeSelectorProps {
  value: GameMode;
  onChange: (mode: GameMode) => void;
}

export function ModeSelector({ value, onChange }: ModeSelectorProps) {
  return (
    <fieldset className="space-y-3">
      <legend className="text-sm font-medium text-white/65">Choose your arena</legend>
      <div className="grid gap-2 sm:grid-cols-2">
        {modeOptions.map(({ id, label, description, icon: Icon }) => {
          const selected = value === id;

          return (
            <label
              className={`relative flex cursor-pointer items-center gap-3 rounded-2xl border p-3 transition ${selected ? "border-[#d8ff56]/60 bg-[#d8ff56]/10" : "border-white/10 bg-white/[0.03] hover:border-white/25 hover:bg-white/[0.06]"}`}
              key={id}
            >
              <input
                checked={selected}
                className="sr-only"
                name="game-mode"
                onChange={() => onChange(id)}
                type="radio"
                value={id}
              />
              <span className={`pointer-events-none flex h-9 w-9 shrink-0 items-center justify-center rounded-xl ${selected ? "bg-[#d8ff56] text-[#101219]" : "bg-white/10 text-white/55"}`}>
                <Icon aria-hidden="true" className="h-4 w-4" />
              </span>
              <span className="pointer-events-none min-w-0">
                <span className="block text-sm font-medium text-white">{label}</span>
                <span className="mt-0.5 block truncate text-xs text-white/45">{description}</span>
              </span>
              <span aria-hidden="true" className={`pointer-events-none ml-auto h-2 w-2 rounded-full ${selected ? "bg-[#d8ff56]" : "bg-white/15"}`} />
            </label>
          );
        })}
      </div>
    </fieldset>
  );
}

