import type { GoalDetail } from "@/types";

interface Props {
  goal: GoalDetail;
  onStart: () => void;
}

/**
 * Финал мастера.
 *
 * Человек уходит отсюда не с планом, а с задачей на пятнадцать минут —
 * поэтому день 1 стоит крупно и последним, прямо над кнопкой.
 */
export function StepReady({ goal, onStart }: Props) {
  const firstDay = goal.tasks.find((task) => task.day_number === 1);

  return (
    <>
      <ul className="mt-6">
        {goal.phases.map((phase) => (
          <li
            key={phase.id}
            className="flex items-baseline justify-between border-b border-line-soft py-3"
          >
            <span className="font-display text-sm font-medium text-bone">
              {phase.title}
            </span>
            <span className="label-dim">
              {phase.start_day}—{phase.end_day}
            </span>
          </li>
        ))}
      </ul>

      {firstDay && (
        <div className="mt-6 border-l border-signal pl-3">
          <div className="label-dim tracking-label text-signal">
            День 1 · {firstDay.estimated_minutes} минут
          </div>
          <h3 className="mt-2 font-display text-[19px] font-medium leading-snug text-bone">
            {firstDay.title}
          </h3>
          <p className="mt-2 text-[13px] leading-relaxed text-muted">
            {firstDay.description}
          </p>
        </div>
      )}

      <button type="button" onClick={onStart} className="btn-primary mt-6">
        Начать
      </button>
    </>
  );
}
