import { Clock, MessageCircle, Check } from "lucide-react";

import type { ChecklistItem, Today } from "@/types";
import { Checklist } from "@/components/Checklist";
import { Graduation } from "@/components/Graduation";
import { Hint } from "@/components/Hint";
import { StatusBar } from "@/components/StatusBar";
import { celebrateDay } from "@/lib/confetti";
import { haptic } from "@/lib/telegram";

interface Props {
  today: Today;
  phaseStarts: number[];
  onToggleChecklistItem: (item: ChecklistItem, next: boolean) => void;
  onCompleteDay: () => void;
  onSimplify: () => void;
  onMentor: () => void;
  onRetryGeneration: () => void;
  completing?: boolean;
}

/**
 * Экран «Сегодня» — режим фокуса.
 *
 * Здесь только текущий день: ни вчерашнего, ни завтрашнего. Всё остальное
 * живёт на карте. Задача — единственное крупное на экране, кнопка
 * «Завершить день» — единственная заливка.
 */
export function TodayScreen({
  today,
  phaseStarts,
  onToggleChecklistItem,
  onCompleteDay,
  onSimplify,
  onMentor,
  onRetryGeneration,
  completing = false,
}: Props) {
  const { task } = today;

  return (
    <>
      <StatusBar
        title={today.goal_title}
        streakDays={today.streak_days}
        totalXp={today.total_xp}
      />

      <div className="flex-none px-5 pt-1">
        <Graduation
          total={today.duration_days}
          current={today.current_day}
          phaseStarts={phaseStarts}
          showCaret
        />
        <div className="mt-2 flex items-baseline justify-between label-dim">
          <span className="truncate pr-3">{today.phase_title ?? "Маршрут"}</span>
          <span className="tracking-meta text-signal">
            {today.current_day} / {today.duration_days}
          </span>
        </div>
        <div className="mt-3 h-px bg-line-soft" />
      </div>

      {task ? (
        <>
          <div className="flex-1 overflow-y-auto px-5">
            <div className="flex items-center gap-2.5 pt-5 label">
              <span>День {task.day_number}</span>
              <i className="h-[3px] w-[3px] rounded-full bg-dim" />
              <span className="text-bone">{task.estimated_minutes} мин</span>
              {task.is_simplified && (
                <>
                  <i className="h-[3px] w-[3px] rounded-full bg-dim" />
                  <span>упрощён</span>
                </>
              )}
            </div>

            <h1 className="mt-3.5 font-display text-[25px] font-medium leading-tight text-bone">
              {task.title}
            </h1>

            <p className="mt-3 max-w-[34ch] text-[13.5px] leading-relaxed text-muted">
              {task.description}
            </p>

            <Checklist items={task.checklist} onToggle={onToggleChecklistItem} />

            {task.hint && <Hint text={task.hint} />}
          </div>

          <div className="flex-none px-5 pb-3">
            <button
              type="button"
              disabled={completing}
              onClick={() => {
                celebrateDay();
                onCompleteDay();
              }}
              className="btn-primary"
            >
              <Check className="h-3.5 w-3.5" strokeWidth={2.4} />
              Завершить день {task.day_number}
            </button>

            <div className="mt-1.5 flex border-t border-line-soft">
              <button
                type="button"
                onClick={() => {
                  haptic.tap();
                  onSimplify();
                }}
                className="flex flex-1 items-center justify-center gap-2 py-3.5 font-mono text-[10px] uppercase tracking-meta text-muted"
              >
                <Clock className="h-3 w-3" strokeWidth={1.5} />
                Мало времени
              </button>
              <button
                type="button"
                onClick={() => {
                  haptic.tap();
                  onMentor();
                }}
                className="flex flex-1 items-center justify-center gap-2 border-l border-line-soft py-3.5 font-mono text-[10px] uppercase tracking-meta text-muted"
              >
                <MessageCircle className="h-3 w-3" strokeWidth={1.5} />
                Ментор
              </button>
            </div>
          </div>
        </>
      ) : (
        /* Дошёл до края написанного маршрута. Не ошибка — просто дни
           ещё не дописались. Говорим прямо и даём кнопку. */
        <div className="flex flex-1 flex-col items-center justify-center px-6 text-center">
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
