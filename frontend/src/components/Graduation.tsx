import { useMemo } from "react";

import { cn } from "@/lib/cn";

interface Props {
  /** Сколько всего делений — обычно длина маршрута в днях. */
  total: number;
  /** День, на котором человек стоит. */
  current: number;
  /** Дни, с которых начинаются фазы: их деления во всю высоту. */
  phaseStarts?: number[];
  height?: number;
  showCaret?: boolean;
  /** Режим генерации: заполняется слева направо бирюзовым. */
  filling?: boolean;
  className?: string;
}

const NO_PHASES: number[] = [];

const BONE = "#EDE7DA";
const SIGNAL = "#6FE3D2";
const IDLE = "#2A2F37";
const BASELINE = "#242830";

interface Tick {
  x: number;
  top: number;
  color: string;
  opacity: number;
}

/**
 * Шкала — подпись всей системы.
 *
 * Не украшение, а показание: пройденные дни костяные и светлеют
 * к сегодняшнему, текущий бирюзовый, будущие тусклые, каждое десятое
 * деление выше, границы фаз — во всю высоту.
 *
 * Один и тот же объект живёт в трёх масштабах: горизонтально в шапке,
 * сжато в карточке цели, крупно на экране генерации.
 */
export function Graduation({
  total,
  current,
  phaseStarts = NO_PHASES,
  height = 28,
  showCaret = false,
  filling = false,
  className,
}: Props) {
  const width = 350;
  const base = height - 1;

  const ticks = useMemo<Tick[]>(() => {
    const step = width / total;
    const phases = new Set(phaseStarts);
    const out: Tick[] = [];

    for (let day = 1; day <= total; day += 1) {
      const x = (day - 0.5) * step;
      const isDecade = day % 10 === 0;
      let length = isDecade ? height * 0.5 : height * 0.28;
      if (phases.has(day)) length = height * 0.8;

      let color = IDLE;
      let opacity = 1;

      if (filling) {
        if (day <= current) {
          color = SIGNAL;
          opacity = 0.35 + 0.6 * (day / Math.max(current, 1));
          length = isDecade ? height * 0.6 : height * 0.4;
        }
      } else if (day < current) {
        color = BONE;
        opacity = 0.16 + 0.44 * Math.pow(day / Math.max(current, 1), 1.8);
      } else if (day === current) {
        color = SIGNAL;
        opacity = 1;
        length = height * 0.94;
      }

      out.push({ x, top: base - length, color, opacity });
    }
    return out;
  }, [total, current, phaseStarts, height, base, filling]);

  const caretX = ((current - 0.5) * width) / total;

  return (
    <svg
      viewBox={`0 0 ${width} ${height}`}
      preserveAspectRatio="none"
      className={cn("block w-full overflow-visible", className)}
      style={{ height }}
      role="img"
      aria-label={`День ${current} из ${total}`}
    >
      {ticks.map((tick, index) => (
        <line
          key={index}
          x1={tick.x}
          y1={base}
          x2={tick.x}
          y2={tick.top}
          stroke={tick.color}
          strokeOpacity={tick.opacity}
          strokeWidth={1}
          vectorEffect="non-scaling-stroke"
        />
      ))}
      <line
        x1={0}
        y1={base}
        x2={width}
        y2={base}
        stroke={BASELINE}
        strokeWidth={1}
        vectorEffect="non-scaling-stroke"
      />
      {showCaret && !filling && (
        <circle cx={caretX} cy={base - height * 0.94} r={2.3} fill={SIGNAL} />
      )}
    </svg>
  );
}
