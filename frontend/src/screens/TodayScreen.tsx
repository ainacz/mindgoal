import { useEffect, useState } from "react";
import { Check } from "lucide-react";

import type { ChecklistItem, Today } from "@/types";
import { Checklist } from "@/components/Checklist";
import { Hint } from "@/components/Hint";
import { celebrateDay } from "@/lib/confetti";
import { haptic } from "@/lib/telegram";

interface Props {
  today: Today;
  onToggleChecklistItem: (item: ChecklistItem, next: boolean) => void;
  onCompleteDay: (resultNote: string | null) => void;
  onSimplify: () => void;
  onRetryGeneration: () => void;
  completing?: boolean;
  simplifying?: boolean;
}

/**
 * Экран «Сегодня» — режим фокуса.
 *
 * Якорь экрана — номер дня. Он же и заголовок, и весь прогресс: шкала
 * из девяноста делений отсюда убрана, она рябила и жила на трёх экранах
 * сразу. Осталась на «Карте», где на каждое деление приходится строка.
 *
 * Название цели здесь тоже не нужно: человек помнит, к чему идёт.
 * Ему важно, какой сегодня день пути.
 */
export function TodayScreen({
  today,
  onToggleChecklistItem,
  onCompleteDay,
  onSimplify,
  onRetryGeneration,
  completing = false,
  simplifying = false,
}: Props) {
  const { task } = today;
  const [note, setNote] = useState("");

  // Новый день — чистое поле, иначе в него утечёт вчерашний результат.
  useEffect(() => setNote(""), [task?.id]);

  return (
    <>
      <header className="flex flex-none items-baseline gap-3 px-[22px] pt-7">
        <span className="font-display text-[64px] font-light leading-[0.9] text-bone">
          {today.current_day}
        </span>
        <span className="text-[13px] text-dim">из {today.duration_days}</span>
        {task && (
          <span className="ml-auto text-[13px] text-muted">
            {task.estimated_minutes} минут
          </span>
        )}
      </header>

      {task ? (
        <>
          <div className="flex-1 overflow-y-auto px-[22px]">
            <h1 className="mt-7 font-display text-[24px] font-medium leading-[1.26] text-bone">
              {task.title}
            </h1>
            <p className="mt-3 text-[14px] leading-relaxed text-muted">
              {task.description}
            </p>

            {/* Единственная линия на экране: делит, что делать, и как проверить. */}
            <div className="my-7 h-px bg-line-soft" />

            <Checklist items={task.checklist} onToggle={onToggleChecklistItem} />

            {/* Поле есть только там, где у дня есть число: вес, время,
                ссылка. Вопрос задаёт сам день — на «что вышло» человек
                пишет «нормально», на «вес и повторения» пишет вес.
                Эти записи читает генератор следующих дней. */}
            {task.result_prompt && (
              <label className="mt-6 block">
                <span className="text-[12.5px] text-muted">
                  {task.result_prompt}
                </span>
                <input
                  value={note}
                  onChange={(event) => setNote(event.target.value)}
                  maxLength={200}
                  className="mt-2 w-full border-b border-line bg-transparent pb-2 text-[14px] text-bone outline-none focus:border-bone"
                />
              </label>
            )}

            {task.hint && <Hint text={task.hint} />}
          </div>

          <div className="flex-none px-[22px] pb-4">
            <button
              type="button"
              disabled={completing}
              onClick={() => {
                celebrateDay();
                onCompleteDay(note.trim() || null);
              }}
              className="btn-primary"
            >
              <Check className="h-3.5 w-3.5" strokeWidth={2.4} />
              Завершить день
            </button>

            {/* Текстовая ссылка, а не кнопка: это выход из потока,
                а не второе действие дня. Показываем один раз — упрощённый
                день упростить ещё раз нельзя, и бэкенд это подтвердит 409-й. */}
            {!task.is_simplified && (
              <div className="mt-3.5 flex justify-center">
                <button
                  type="button"
                  disabled={simplifying}
                  onClick={() => {
                    haptic.tap();
                    onSimplify();
                  }}
                  className="py-1 text-[12.5px] text-muted disabled:opacity-50"
                >
                  {simplifying ? "Переписываю день…" : "Мало времени"}
                </button>
              </div>
            )}
          </div>
        </>
      ) : (
        /* Дошёл до края написанного маршрута. Не ошибка — дни ещё пишутся. */
        <div className="flex flex-1 flex-col items-center justify-center px-7 text-center">
          <h2 className="font-display text-[21px] font-light text-bone">
            Дописываю следующие дни
          </h2>
          <p className="mt-3 max-w-[26ch] text-[13px] leading-relaxed text-muted">
            Это занимает несколько секунд. Если задача так и не появилась —
            попробуй ещё раз.
          </p>
          <button
            type="button"
            onClick={onRetryGeneration}
            className="btn-ghost mt-7 max-w-[240px]"
          >
            Попробовать ещё раз
          </button>
        </div>
      )}
    </>
  );
}
