interface Props {
  text: string;
}

/**
 * Подсказка держится на волосяной линии слева, а не на цветной плашке.
 *
 * Бирюзовый здесь был бы вторым акцентом на экране, где он уже потрачен
 * на текущий день. Подсказке и положено быть тихой.
 */
export function Hint({ text }: Props) {
  return (
    <aside className="my-5 border-l border-dim pl-3">
      <div className="label-dim text-muted">Подсказка</div>
      <p className="mt-1.5 text-[13px] leading-relaxed text-muted">{text}</p>
    </aside>
  );
}
