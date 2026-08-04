import type { ClarifyQuestion } from "@/types";
import { cn } from "@/lib/cn";
import { haptic } from "@/lib/telegram";

interface Props {
  questions: ClarifyQuestion[];
  answers: Record<string, string>;
  busy: boolean;
  onAnswer: (question: string, option: string) => void;
  onNext: () => void;
}

/**
 * Ответы чипами, а не полями ввода: три касания вместо трёх абзацев,
 * и модель получает нормализованные значения вместо свободного текста.
 */
export function StepQuestions({
  questions,
  answers,
  busy,
  onAnswer,
  onNext,
}: Props) {
  const answered = questions.every((item) => answers[item.question]);

  return (
    <>
      <h2 className="mt-6 font-display text-[23px] font-medium leading-snug text-bone">
        {questions.length === 1 ? "Уточню одну вещь" : `Уточню ${questions.length} вещи`}
      </h2>
      <p className="mt-2.5 text-[13px] leading-relaxed text-muted">
        Иначе маршрут получится общим — а нужен твой.
      </p>

      <div className="mt-6 space-y-5">
        {questions.map((item) => (
          <div key={item.question}>
            <div className="text-sm leading-snug text-bone">{item.question}</div>
            <div className="mt-2.5 flex flex-wrap gap-2">
              {item.options.map((option) => {
                const active = answers[item.question] === option;
                return (
                  <button
                    key={option}
                    type="button"
                    onClick={() => {
                      haptic.select();
                      onAnswer(item.question, option);
                    }}
                    className={cn(
                      "rounded-[11px] border px-3 py-2 text-[13px] transition-colors",
                      active ? "border-bone text-bone" : "border-line text-muted",
                    )}
                  >
                    {option}
                  </button>
                );
              })}
            </div>
          </div>
        ))}
      </div>

      <button
        type="button"
        disabled={busy || !answered}
        onClick={onNext}
        className="btn-primary mt-6"
      >
        {busy ? "Думаю…" : "Дальше"}
      </button>
    </>
  );
}
