import { Check } from "lucide-react";

import type { ChecklistItem } from "@/types";
import { cn } from "@/lib/cn";
import { haptic } from "@/lib/telegram";

interface Props {
  items: ChecklistItem[];
  onToggle: (item: ChecklistItem, next: boolean) => void;
}

/**
 * Чек-лист без коробок, без шапки со счётчиком и без линий между пунктами.
 *
 * Счётчик «2 из 3» повторял то, что и так видно по кружкам, а линии
 * между тремя строчками добавляли три черты на экран, где их и без того
 * хватало. Выполненный пункт не зачёркивается, а гаснет: зачёркивание
 * на четырнадцати пикселях превращается в грязь.
 */
export function Checklist({ items, onToggle }: Props) {
  return (
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
            className="flex w-full items-start gap-3.5 py-2.5 text-left"
          >
            <span
              className={cn(
                "mt-[3px] grid h-[15px] w-[15px] flex-none place-items-center rounded-full border transition-colors",
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
                "text-[14px] leading-snug transition-colors",
                item.is_done ? "text-dim" : "text-bone",
              )}
            >
              {item.text}
            </span>
          </button>
        </li>
      ))}
    </ul>
  );
}
