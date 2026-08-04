interface Props {
  /** Слева — название активной цели или имя человека. */
  title: string;
  streakDays: number;
  totalXp: number;
}

/**
 * Строка состояния обычным текстом, без моно-капса и без иконок.
 *
 * Раньше здесь стояли разреженные заглавные и иконка пламени — на экране,
 * где такого набора было ещё четыре. Огонёк оставлен эмодзи: он читается
 * мгновенно и не требует ни библиотеки, ни цвета.
 */
export function StatusBar({ title, streakDays, totalXp }: Props) {
  return (
    <div className="flex flex-none items-center justify-between px-[22px] pb-3 pt-[18px]">
      <div className="max-w-[210px] truncate text-[12.5px] text-muted">{title}</div>
      <div className="text-[12.5px] text-muted">
        {streakDays > 0 && (
          <>
            🔥 <b className="font-semibold text-brass">{streakDays}</b>
            <span className="px-1.5 text-dim">·</span>
          </>
        )}
        {totalXp} XP
      </div>
    </div>
  );
}
