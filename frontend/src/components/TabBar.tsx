import type { ReactNode } from "react";

import type { Tab } from "@/types";
import { cn } from "@/lib/cn";
import { haptic } from "@/lib/telegram";

interface Props {
  active: Tab;
  onChange: (tab: Tab) => void;
}

/**
 * Иконки нарисованы вручную, а не взяты из библиотеки: это часть опознавания
 * приложения. «Сегодня» — столбики шкалы, «Карта» — узлы маршрута,
 * «Цели» — убывающий список. Эмодзи здесь были бы шагом назад.
 */
const ICONS: Record<Tab, ReactNode> = {
  today: (
    <>
      <path d="M4 19v-6" />
      <path d="M9.3 19V5" />
      <path d="M14.7 19v-9" />
      <path d="M20 19v-4" />
    </>
  ),
  map: (
    <>
      <circle cx="7" cy="5.5" r="2.2" />
      <path d="M7 8v4a3 3 0 0 0 3 3h4a3 3 0 0 1 3 3v.5" />
      <circle cx="17" cy="18.5" r="2.2" />
    </>
  ),
  goals: (
    <>
      <path d="M4 6h16" />
      <path d="M4 12h11" />
      <path d="M4 18h6" />
    </>
  ),
};

const LABELS: Record<Tab, string> = {
  today: "Сегодня",
  map: "Карта",
  goals: "Цели",
};

export function TabBar({ active, onChange }: Props) {
  return (
    <nav className="flex flex-none border-t border-line">
      {(Object.keys(LABELS) as Tab[]).map((tab) => {
        const isActive = tab === active;
        return (
          <button
            key={tab}
            type="button"
            aria-current={isActive ? "page" : undefined}
            onClick={() => {
              if (!isActive) haptic.select();
              onChange(tab);
            }}
            className={cn(
              "relative flex flex-1 flex-col items-center gap-[7px] pb-[18px] pt-3 transition-colors",
              isActive ? "text-bone" : "text-dim",
            )}
          >
            {isActive && (
              <span className="absolute -top-px left-1/2 h-0.5 w-6 -translate-x-1/2 bg-bone" />
            )}
            <svg
              viewBox="0 0 24 24"
              className="h-[18px] w-[18px]"
              fill="none"
              stroke="currentColor"
              strokeWidth={1.5}
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              {ICONS[tab]}
            </svg>
            <span className="font-mono text-[9px] uppercase tracking-meta">
              {LABELS[tab]}
            </span>
          </button>
        );
      })}
    </nav>
  );
}
