import type { ReactNode } from "react";
import { X } from "lucide-react";

interface Props {
  open: boolean;
  onClose?: () => void;
  /** Слева в шапке: «Шаг 1 из 3» или «Маршрут готов». */
  heading: ReactNode;
  /** Полоса шагов: сколько всего и который идёт. Ноль — не показывать. */
  steps?: { total: number; current: number };
  children: ReactNode;
}

/**
 * Шторка снизу.
 *
 * Всё нативное в Telegram приходит снизу; центрированное окно с затемнением
 * читается как веб-страница, случайно попавшая в мессенджер.
 */
export function Sheet({ open, onClose, heading, steps, children }: Props) {
  if (!open) return null;

  return (
    <div className="absolute inset-0 z-20 flex flex-col justify-end">
      <button
        type="button"
        aria-label="Закрыть"
        onClick={onClose}
        className="absolute inset-0 cursor-default bg-gradient-to-b from-ink/60 to-ink/95"
      />

      <div className="relative max-h-[92%] overflow-y-auto rounded-t-sheet border-t border-line bg-sheet px-[22px] pb-6 pt-2.5">
        <div className="mx-auto mb-4 h-[3px] w-[34px] rounded-sm bg-dim" />

        <div className="flex items-center justify-between">
          <div className="label-dim text-muted">{heading}</div>
          {onClose && (
            <button
              type="button"
              onClick={onClose}
              aria-label="Закрыть"
              className="grid h-[26px] w-[26px] place-items-center text-muted"
            >
              <X className="h-3.5 w-3.5" strokeWidth={1.6} />
            </button>
          )}
        </div>

        {steps && steps.total > 1 && (
          <div className="mt-3 flex gap-[5px]">
            {Array.from({ length: steps.total }, (_, index) => {
              const position = index + 1;
              return (
                <i
                  key={position}
                  className={
                    position < steps.current
                      ? "h-0.5 flex-1 rounded-sm bg-bone opacity-30"
                      : position === steps.current
                        ? "h-0.5 flex-1 rounded-sm bg-bone"
                        : "h-0.5 flex-1 rounded-sm bg-line"
                  }
                />
              );
            })}
          </div>
        )}

        {children}
      </div>
    </div>
  );
}
