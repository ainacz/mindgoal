import { useRef, useState } from "react";
import { Plus, Trash2 } from "lucide-react";

import type { Goal } from "@/types";
import { Empty } from "@/components/Empty";
import { StatusBar } from "@/components/StatusBar";
import { cn } from "@/lib/cn";
import { confirmAction, haptic } from "@/lib/telegram";

interface Props {
  userName: string;
  goals: Goal[];
  totalXp: number;
  todayTitleByGoal: Record<string, string | undefined>;
  onOpenGoal: (goal: Goal) => void;
  onDeleteGoal: (goal: Goal) => void;
  onCreateGoal: () => void;
}

const SWIPE_THRESHOLD = 48;

export function GoalsScreen({
  userName,
  goals,
  totalXp,
  todayTitleByGoal,
  onOpenGoal,
  onDeleteGoal,
  onCreateGoal,
}: Props) {
  const [swipedId, setSwipedId] = useState<string | null>(null);
  const startX = useRef(0);

  const bestStreak = goals.reduce((max, goal) => Math.max(max, goal.streak_days), 0);

  async function askAndDelete(goal: Goal) {
    haptic.warning();
    const confirmed = await confirmAction(
      `Удалить «${goal.title}»? Маршрут и весь прогресс пропадут.`,
    );
    setSwipedId(null);
    if (confirmed) onDeleteGoal(goal);
  }

  return (
    <>
      <StatusBar title={userName} streakDays={bestStreak} totalXp={totalXp} />

      {goals.length === 0 ? (
        <Empty
          title="Пока ни одной цели"
          hint="Напиши, чего хочешь достичь, и получишь маршрут из ежедневных шагов по пятнадцать минут."
          action={
            <button type="button" onClick={onCreateGoal} className="btn-primary">
              <Plus className="h-3.5 w-3.5" strokeWidth={2} />
              Создать цель
            </button>
          }
        />
      ) : (
        <div className="flex-1 overflow-y-auto px-[22px] pt-3">
          <div className="flex items-baseline justify-between">
            <h1 className="font-display text-[19px] font-light text-bone">Мои цели</h1>
            <span className="text-[12.5px] text-dim">
              {goals.filter((goal) => goal.status === "active").length} активные
            </span>
          </div>

          {goals.map((goal) => {
            const isSwiped = swipedId === goal.id;
            const isArchived =
              goal.status === "completed" || goal.status === "archived";

            return (
              <article
                key={goal.id}
                className={cn(
                  "relative overflow-hidden border-b border-line-soft py-5",
                  isArchived && "opacity-40",
                )}
                onTouchStart={(event) => {
                  startX.current = event.touches[0].clientX;
                }}
                onTouchEnd={(event) => {
                  const delta = startX.current - event.changedTouches[0].clientX;
                  if (delta > SWIPE_THRESHOLD) {
                    haptic.tap();
                    setSwipedId(goal.id);
                  } else if (delta < -SWIPE_THRESHOLD) {
                    setSwipedId(null);
                  }
                }}
              >
                {isSwiped && (
                  <button
                    type="button"
                    onClick={() => void askAndDelete(goal)}
                    className="absolute bottom-4 right-0 top-4 flex w-[74px] flex-col items-center justify-center gap-1.5 rounded-[13px] border border-danger/30 bg-danger/10 text-[11px] text-danger"
                  >
                    <Trash2 className="h-3.5 w-3.5" strokeWidth={1.5} />
                    Удалить
                  </button>
                )}

                {/* При свайпе содержимое не уезжает под край, а ужимается:
                    так ничего не обрезается на середине слова. */}
                <button
                  type="button"
                  onClick={() => onOpenGoal(goal)}
                  className={cn(
                    "block w-full text-left transition-all duration-300",
                    isSwiped && "pr-[92px]",
                  )}
                >
                  {goal.category && (
                    <div className="text-[12px] text-muted">{goal.category}</div>
                  )}
                  <h2 className="mt-2.5 font-display text-[21px] font-light leading-tight text-bone">
                    {goal.title}
                  </h2>

                  {!isArchived && todayTitleByGoal[goal.id] && (
                    <p className="mt-2 truncate text-[12.5px] leading-snug text-dim">
                      <span className="text-muted">Сегодня:</span>{" "}
                      {todayTitleByGoal[goal.id]}
                    </p>
                  )}

                  {/* Полоска, а не девяносто делений: в карточке нужен
                      только ответ «далеко ли», а не показание. */}
                  <div className="mt-4 h-[2px] w-full rounded-sm bg-line">
                    <div
                      className="h-full rounded-sm bg-bone opacity-60"
                      style={{
                        width: `${Math.round(
                          (goal.current_day / goal.duration_days) * 100,
                        )}%`,
                      }}
                    />
                  </div>

                  <div className="mt-2.5 flex justify-between text-[12px] text-dim">
                    <span>
                      {isArchived
                        ? `${goal.duration_days} из ${goal.duration_days} · завершена`
                        : `День ${goal.current_day} из ${goal.duration_days}`}
                    </span>
                    {!isArchived && goal.streak_days > 0 && (
                      <span className="text-brass">
                        {goal.streak_days} дней подряд
                      </span>
                    )}
                  </div>
                </button>
              </article>
            );
          })}

          <button
            type="button"
            onClick={onCreateGoal}
            className="mb-2 mt-6 flex h-12 w-full items-center justify-center gap-2.5 rounded-[13px] border border-dashed border-line text-[13.5px] text-muted transition-colors active:border-muted active:text-bone"
          >
            <Plus className="h-3 w-3" strokeWidth={1.6} />
            Новая цель
          </button>
        </div>
      )}
    </>
  );
}
