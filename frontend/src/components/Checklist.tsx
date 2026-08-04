import { Check } from "lucide-react";

import type { ChecklistItem } from "@/types";
import { cn } from "@/lib/cn";
import { haptic } from "@/lib/telegram";

interface Props {
  items: ChecklistItem[];
  onToggle: (item: ChecklistItem, next: boolean) => void;
}

/**
 * Чек-лист без коробок: кружок, текст, волосяная линия снизу.
 *
 * Выполненный пункт не зачёркивается, а гаснет. Зачёркивание на четырнадцати
 * пикселях превращается в грязь и читается хуже, чем просто тусклый текст.
 */
export function Checklist({ items, onToggle }: Props) {
  const done = items.filter((item) => item.is_done).length;

  return (
    <section className="mt-6">
      <header className="flex items-baseline justify-between border-b border-line pb-2 label-dim text-muted">
        <span>Чек-лист</span>
        <span>
          <b className="font-semibold text-bone">{done}</b> / {items.length}
        </span>
      </header>

      <ul>
        {items.map((item) => (
          <li key={item.id}>
            <button
              type="button"
              onClick={() => {
                haptic.tap();
                onToggle(item, !item.is_done);
              }}
              aria-pressed={item.is_done}
              className="flex w-full items-start gap-3 border-b border-line-soft px-0.5 py-3 text-left"
            >
              <span
                className={cn(
                  "mt-0.5 grid h-4 w-4 flex-none place-items-center rounded-full border transition-colors",
                  item.is_done ? "border-bone bg-bone" : "border-dim",
                )}
              >
                <Check
                  className={cn(
                    "h-2 w-2 text-ink transition-opacity",
                    item.is_done ? "opacity-100" : "opacity-0",
                  )}
                  strokeWidth={4}
                />
              </span>
              <span
                className={cn(
                  "text-sm leading-snug transition-colors",
                  item.is_done ? "text-dim" : "text-bone",
                )}
              >
                {item.text}
              </span>
            </button>
          </li>
        ))}
      </ul>
    </section>
  );
}
