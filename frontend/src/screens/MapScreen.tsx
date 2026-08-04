import { Fragment } from "react";

import type { DailyTask, GoalDetail, Phase } from "@/types";
import { Graduation } from "@/components/Graduation";
import { StatusBar } from "@/components/StatusBar";
import { cn } from "@/lib/cn";
import { haptic } from "@/lib/telegram";

interface Props {
  goal: GoalDetail;
  totalXp: number;
  onOpenDay: (task: DailyTask) => void;
}

interface Row {
  day: number;
  task?: DailyTask;
}

/**
 * Собирает строки маршрута: только написанные дни плюс два запертых
 * следующих. Показывать все девяносто пустых строк незачем — это скролл
 * ни о чём.
 */
function rowsForPhase(phase: Phase, goal: GoalDetail): Row[] {
  const rows: Row[] = [];
  const written = goal.tasks.filter(
    (task) => task.day_number >= phase.start_day && task.day_number <= phase.end_day,
  );
  for (const task of written) rows.push({ day: task.day_number, task });

  const nextLocked = goal.generated_until_day + 1;
  for (let day = nextLocked; day < nextLocked + 2; day += 1) {
    if (day >= phase.start_day && day <= phase.end_day && day <= goal.duration_days) {
      rows.push({ day });
    }
  }
  return rows;
}

export function MapScreen({ goal, totalXp, onOpenDay }: Props) {
  const phaseStarts = goal.phases.map((phase) => phase.start_day);
  const hasLocked = goal.generated_until_day < goal.duration_days;

  return (
    <>
      <StatusBar
        title={goal.title}
        streakDays={goal.streak_days}
        totalXp={totalXp}
      />

      <div className="flex-none px-5 pt-1">
        <Graduation
          total={goal.duration_days}
          current={goal.current_day}
          phaseStarts={phaseStarts}
          showCaret
        />
        <div className="mt-2 flex items-baseline justify-between label-dim">
          <span>
            {goal.phases.length} фазы · {goal.duration_days} делений
          </span>
          <span className="tracking-meta text-signal">
            {goal.current_day} / {goal.duration_days}
          </span>
        </div>
        <div className="mt-3 h-px bg-line-soft" />
      </div>

      <div className="flex-1 overflow-y-auto px-5">
        <div className="flex items-baseline justify-between pt-[18px]">
          <h1 className="font-display text-[19px] font-light text-bone">Маршрут</h1>
          <span className="label-dim">
            Открыт до дня {goal.generated_until_day}
          </span>
        </div>

        <div className="relative mt-4 pl-[46px]">
          {/* Одна непрерывная линия на весь маршрут — она и есть карта. */}
          <span className="absolute bottom-6 left-[19px] top-6 w-px bg-line" />

          {goal.phases.map((phase) => (
            <Fragment key={phase.id}>
              <div className="relative -ml-[46px] py-4 pl-[46px]">
                <span className="absolute left-3 top-[25px] h-px w-[15px] bg-muted" />
                <div className="font-display text-[13.5px] font-medium text-bone">
                  {phase.title}
                </div>
                <div className="mt-1 label-dim">
                  Дни {phase.start_day}—{phase.end_day}
                  {goal.current_day > phase.end_day && " · пройдена"}
                  {goal.current_day >= phase.start_day &&
                    goal.current_day <= phase.end_day &&
                    " · идёт сейчас"}
                </div>
              </div>

              {rowsForPhase(phase, goal).map(({ day, task }) => {
                const isNow = day === goal.current_day;
                const isDone = Boolean(task?.is_completed);
                const isLocked = !task;

                return (
                  <button
                    key={day}
                    type="button"
                    disabled={isLocked}
                    onClick={() => {
                      if (!task) return;
                      haptic.tap();
                      onOpenDay(task);
                    }}
                    className={cn(
                      "relative flex w-full items-baseline gap-3 border-b py-3 text-left",
                      isNow ? "border-line" : "border-line-soft",
                      isLocked && "opacity-55",
                    )}
                  >
                    <span
                      className={cn(
                        "absolute -left-[31px] top-4 h-2 w-2 rounded-full border",
                        isNow
                          ? "border-signal bg-signal shadow-[0_0_0_4px_rgba(111,227,210,0.13)]"
                          : isDone
                            ? "border-bone bg-bone"
                            : "border-dim bg-ink",
                      )}
                    />
                    <span
                      className={cn(
                        "w-[22px] flex-none font-mono text-[10.5px]",
                        isNow ? "text-signal" : "text-dim",
                      )}
                    >
                      {day}
                    </span>
                    {task ? (
                      <>
                        <span
                          className={cn(
                            "text-[13px] leading-snug",
                            isNow ? "font-medium text-bone" : "text-muted",
                          )}
                        >
                          {task.title}
                        </span>
                        <span className="ml-auto pl-2 font-mono text-[9.5px] text-dim">
                          {task.estimated_minutes}м
                        </span>
                      </>
                    ) : (
                      /* Заголовка нет, потому что дня ещё нет. Прочерк честнее
                         замка: замок обещает, что за ним что-то есть. */
                      <span className="inline-block h-px w-[104px] self-center bg-line" />
                    )}
                  </button>
                );
              })}
            </Fragment>
          ))}

          {hasLocked && (
            <p className="mb-5 mt-3.5 border-t border-line-soft pt-3 label-dim leading-relaxed">
              Дни после {goal.generated_until_day} появятся ближе к делу
            </p>
          )}
        </div>
      </div>
    </>
  );
}
