import type { ReactNode } from "react";

interface Props {
  title: string;
  hint?: string;
  action?: ReactNode;
}

/**
 * Пустой экран — это приглашение к действию, а не сообщение об отсутствии
 * данных. Поэтому здесь глагол, а не «ничего не найдено».
 */
export function Empty({ title, hint, action }: Props) {
  return (
    <div className="flex flex-1 flex-col items-center justify-center px-6 text-center">
      <h2 className="font-display text-[21px] font-light leading-snug text-bone">
        {title}
      </h2>
      {hint && (
        <p className="mt-3 max-w-[28ch] text-[13px] leading-relaxed text-muted">
          {hint}
        </p>
      )}
      {action && <div className="mt-7 w-full max-w-[260px]">{action}</div>}
    </div>
  );
}
