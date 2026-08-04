import confetti from "canvas-confetti";

import { haptic } from "@/lib/telegram";

/**
 * Единственный праздник в приложении — закрытый день.
 *
 * Цвета те же, что в системе: костяной и бирюзовый. Разноцветное конфетти
 * выглядело бы как чужая библиотека, случайно попавшая в макет.
 */
export function celebrateDay(): void {
  haptic.success();

  if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;

  void confetti({
    particleCount: 70,
    spread: 62,
    startVelocity: 34,
    ticks: 140,
    scalar: 0.85,
    origin: { y: 0.72 },
    colors: ["#EDE7DA", "#6FE3D2", "#D9A441"],
    disableForReducedMotion: true,
  });
}
