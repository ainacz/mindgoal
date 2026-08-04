interface Props {
  text: string;
}

/**
 * Подсказка — обычный абзац с жирным началом.
 *
 * Была вертикальная черта плюс метка капсом с трекингом: две лишние
 * детали ради одного предложения, которое и так читается как подсказка,
 * если начать его словом «Подсказка».
 */
export function Hint({ text }: Props) {
  return (
    <p className="mb-6 mt-6 text-[13px] leading-relaxed text-dim">
      <b className="font-medium text-muted">Подсказка.</b> {text}
    </p>
  );
}
