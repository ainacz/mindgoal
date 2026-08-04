import { cn } from "@/lib/cn";
import { haptic } from "@/lib/telegram";

interface Props {
  title: string;
  duration: number;
  busy: boolean;
  onTitleChange: (value: string) => void;
  onDurationChange: (value: number) => void;
  onNext: () => void;
}

const DURATIONS = [30, 60, 90];

export function StepGoal({
  title,
  duration,
  busy,
  onTitleChange,
  onDurationChange,
  onNext,
}: Props) {
  return (
    <>
      <h2 className="mt-6 font-display text-[23px] font-medium leading-snug text-bone">
        Чего ты хочешь достичь?
      </h2>
      <p className="mt-2.5 text-[13px] leading-relaxed text-muted">
        Пиши как есть, своими словами. Если получится размыто — уточню
        на следующем шаге.
      </p>

      {/* Поле без коробки: ответ важнее рамки вокруг него. */}
      <div className="mt-5 border-b border-line pb-3 focus-within:border-bone">
        <input
          value={title}
          onChange={(event) => onTitleChange(event.target.value)}
          placeholder="Стать AI-инженером"
          maxLength={200}
          autoComplete="off"
          className="w-full bg-transparent font-display text-[21px] font-light text-bone outline-none placeholder:text-dim"
        />
      </div>

      <div className="mt-7 label">Срок</div>
      <div className="mt-3 flex gap-2.5">
        {DURATIONS.map((value) => {
          const active = value === duration;
          return (
            <button
              key={value}
              type="button"
              onClick={() => {
                haptic.select();
                onDurationChange(value);
              }}
              className={cn(
                "flex-1 rounded-[13px] border px-0 pb-3 pt-3.5 text-center transition-colors",
                active ? "border-bone" : "border-line",
              )}
            >
              <div
                className={cn(
                  "font-mono text-[19px] font-semibold",
                  active ? "text-bone" : "text-muted",
                )}
              >
                {value}
              </div>
              <div
                className={cn(
                  "mt-1 font-mono text-[8.5px] uppercase tracking-label",
                  active ? "text-muted" : "text-dim",
                )}
              >
                дней
              </div>
            </button>
          );
        })}
      </div>

      <button
        type="button"
        disabled={busy || title.trim().length < 3}
        onClick={onNext}
        className="btn-primary mt-6"
      >
        {busy ? "Смотрю цель…" : "Дальше"}
      </button>

      <p className="mt-3.5 text-center label-dim leading-relaxed">
        Дни ждут тебя, а не наоборот —
        <br />
        пропуск ничего не сжигает
      </p>
    </>
  );
}
