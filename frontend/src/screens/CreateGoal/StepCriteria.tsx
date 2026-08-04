import { Pencil } from "lucide-react";

interface Props {
  criteria: string[];
  /** Не null, когда срок не бьётся с уровнем. */
  realityNote: string | null;
  busy: boolean;
  onChange: (index: number, value: string) => void;
  onGenerate: () => void;
}

/**
 * Критерии готовности. Каждый можно переписать прямо здесь — поэтому это
 * поля ввода, а не текст с кнопкой «редактировать».
 */
export function StepCriteria({
  criteria,
  realityNote,
  busy,
  onChange,
  onGenerate,
}: Props) {
  return (
    <>
      <h2 className="mt-6 font-display text-[23px] font-medium leading-snug text-bone">
        Считаем, что дошёл, когда
      </h2>
      <p className="mt-2.5 text-[13px] leading-relaxed text-muted">
        Только то, что можно предъявить. Не «разобрался», а ссылка, файл, оффер.
      </p>

      {/* Не запрет, а предупреждение: человек вправе взяться
          за невозможное — но должен узнать об этом сейчас,
          а не на тридцатый день. */}
      {realityNote && (
        <div className="mt-5 border-l border-brass pl-3">
          <div className="label-dim tracking-label text-brass">Про срок</div>
          <p className="mt-1.5 text-[13px] leading-relaxed text-muted">
            {realityNote}
          </p>
        </div>
      )}

      <ul className="mt-5">
        {criteria.map((text, index) => (
          <li
            key={index}
            className="flex items-start gap-3 border-b border-line-soft py-3.5 first:border-t first:border-line"
          >
            {/* Точка, а не квадрат: квадрат читается как чекбокс,
                который просят отметить, а отмечать тут нечего. */}
            <span className="mt-[9px] h-[3px] w-[3px] flex-none rounded-full bg-muted" />
            <input
              value={text}
              onChange={(event) => onChange(index, event.target.value)}
              maxLength={300}
              className="flex-1 bg-transparent text-sm leading-snug text-bone outline-none"
            />
            <Pencil className="mt-0.5 h-3.5 w-3.5 flex-none text-dim" strokeWidth={1.5} />
          </li>
        ))}
      </ul>

      <button
        type="button"
        disabled={busy || criteria.every((text) => !text.trim())}
        onClick={onGenerate}
        className="btn-primary mt-6"
      >
        Собрать маршрут
      </button>

      <p className="mt-3.5 text-center label-dim">Любой пункт можно переписать</p>
    </>
  );
}
