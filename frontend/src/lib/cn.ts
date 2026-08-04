/** Склейка классов. Своя, чтобы не тянуть зависимость ради восьми строк. */
export function cn(...parts: Array<string | false | null | undefined>): string {
  return parts.filter(Boolean).join(" ");
}
