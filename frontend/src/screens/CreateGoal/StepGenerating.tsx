import { useEffect, useState } from "react";

import { Graduation } from "@/components/Graduation";

interface Props {
  durationDays: number;
  /** Генерация упала: показываем причину и кнопку повтора вместо лога. */
  failed?: boolean;
  onRetry?: () => void;
}

const STAGES = [
  "Разметил три фазы",
  "Проверил критерии на измеримость",
  "Пишу дни 1—7",
];

/**
 * Экран генерации.
 *
 * Пятнадцать секунд ожидания нужно объяснить, а не спрятать за спиннером.
 * Поэтому здесь лог: что готово, что идёт, что будет позже.
 */
export function StepGenerating({ durationDays, failed, onRetry }: Props) {
  const [stage, setStage] = useState(0);

  useEffect(() => {
    if (failed) return;
    // Прогресс честный по смыслу, но не по секундам: бэкенд отдаёт скелет
    // одним ответом и промежуточных событий у нас нет. Показываем движение,
    // чтобы человек видел, что приложение живо.
    const timer = window.setInterval(
      () => setStage((value) => Math.min(value + 1, STAGES.length - 1)),
      4200,
    );
    return () => window.clearInterval(timer);
  }, [failed]);

  if (failed) {
    return (
      <>
        <h2 className="mt-6 font-display text-[23px] font-medium leading-snug text-bone">
          Не получилось собрать маршрут
        </h2>
        <p className="mt-2.5 text-[13px] leading-relaxed text-muted">
          Цель и критерии сохранены — ничего вводить заново не нужно.
        </p>
        <button type="button" onClick={onRetry} className="btn-primary mt-6">
          Попробовать ещё раз
        </button>
      </>
    );
  }

  const writtenDays = Math.round(((stage + 1) / STAGES.length) * 7);

  return (
    <>
      <div className="mt-6">
        <Graduation
          total={durationDays}
          current={Math.max(writtenDays, 1)}
          height={44}
          filling
        />
        <div className="mt-3.5 flex items-baseline justify-between font-mono text-[10px] uppercase tracking-meta">
          <span className="text-signal">{STAGES[stage]}</span>
          <span className="text-dim">
            {writtenDays} / {durationDays}
          </span>
        </div>
      </div>

      <ul className="mt-5 border-t border-line-soft">
        {STAGES.map((text, index) => (
          <li
            key={text}
            className="flex justify-between border-b border-line-soft py-3 text-[13px]"
          >
            <span className={index <= stage ? "text-bone" : "text-dim"}>{text}</span>
            <span
              className={
                index < stage
                  ? "font-mono text-[9.5px] uppercase tracking-meta text-dim"
                  : "font-mono text-[9.5px] uppercase tracking-meta text-signal"
              }
            >
              {index < stage ? "Готово" : index === stage ? "Идёт" : ""}
            </span>
          </li>
        ))}
        <li className="flex justify-between border-b border-line-soft py-3 text-[13px] text-dim">
          <span>Дни 8—{durationDays}</span>
          <span className="font-mono text-[9.5px] uppercase tracking-meta">Позже</span>
        </li>
      </ul>

      <p className="mt-6 text-center label-dim leading-relaxed">
        Обычно 15—20 секунд.
        <br />
        Остальные дни допишутся по ходу
      </p>
    </>
  );
}
