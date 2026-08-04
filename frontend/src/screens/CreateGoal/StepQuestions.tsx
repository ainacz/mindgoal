import { useState } from "react";

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
 *
 * Но у каждого вопроса есть «Своё». Тестировщик на «выучить столицы»
 * упёрся в выбор между двумя вариантами, хотя честный ответ был третьим.
 * Варианты придумывает модель — иногда она придумает их плохо, и человек
 * не должен из-за этого врать про себя.
 */
export function StepQuestions({
  questions,
  answers,
  busy,
  onAnswer,
  onNext,
}: Props) {
  const [freeForm, setFreeForm] = useState<Record<string, boolean>>({});
  const answered = questions.every((item) => answers[item.question]?.trim());

  return (
    <>
      <h2 className="mt-6 font-display text-[23px] font-medium leading-snug text-bone">
        {questions.length === 1
          ? "Уточню одну вещь"
          : `Уточню ${questions.length} вещи`}
      </h2>
      <p className="mt-2.5 text-[13px] leading-relaxed text-muted">
        Иначе маршрут получится общим — а нужен твой.
      </p>

      <div className="mt-6 space-y-5">
        {questions.map((item) => {
          const isFree = freeForm[item.question];
          return (
            <div key={item.question}>
              <div className="text-sm leading-snug text-bone">{item.question}</div>

              {isFree ? (
                <div className="mt-2.5 border-b border-line pb-2 focus-within:border-bone">
                  <input
                    autoFocus
                    value={answers[item.question] ?? ""}
                    onChange={(event) => onAnswer(item.question, event.target.value)}
                    placeholder="Ответь своими словами"
                    maxLength={200}
                    className="w-full bg-transparent text-[15px] text-bone outline-none placeholder:text-dim"
                  />
                </div>
              ) : (
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

                  <button
                    type="button"
                    onClick={() => {
                      haptic.tap();
                      onAnswer(item.question, "");
                      setFreeForm((previous) => ({
                        ...previous,
                        [item.question]: true,
                      }));
                    }}
                    className="rounded-[11px] border border-dashed border-line px-3 py-2 text-[13px] text-dim"
                  >
                    Своё
                  </button>
                </div>
              )}
            </div>
          );
        })}
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
