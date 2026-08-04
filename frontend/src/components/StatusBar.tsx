import { Flame } from "lucide-react";

interface Props {
  /** Слева — название активной цели или имя человека. */
  title: string;
  streakDays: number;
  totalXp: number;
}

/**
 * Строка состояния вместо шапки с аватаркой.
 *
 * Человек знает, как его зовут, и знает свою фотографию. Место в шапке
 * дороже: здесь стоит то, что меняется — цель, стрик, опыт.
 */
export function StatusBar({ title, streakDays, totalXp }: Props) {
  return (
    <div className="flex flex-none items-center justify-between px-5 pb-3 pt-4">
      <div className="label max-w-[196px] truncate tracking-meta">{title}</div>
      <div className="flex items-center gap-4 font-mono text-[11px] text-muted">
        <span className="flex items-center gap-1.5">
          <Flame className="h-3 w-3 text-brass" strokeWidth={1.5} />
          <b className="font-semibold text-brass">{streakDays}</b>
        </span>
        <span>
          <b className="font-semibold text-bone">{totalXp}</b> XP
        </span>
      </div>
    </div>
  );
}
