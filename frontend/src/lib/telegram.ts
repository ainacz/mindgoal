/**
 * Тонкая обёртка над Telegram WebApp.
 *
 * Работаем с window.Telegram.WebApp напрямую, а не через @telegram-apps/sdk:
 * поверхность SDK за год менялась дважды, а нам нужно пять вызовов, которые
 * в самом WebApp не менялись никогда. Плюс так мини-апп открывается
 * в обычном браузере — без этого отлаживать вёрстку невозможно.
 */

type HapticStyle = "light" | "medium" | "heavy" | "rigid" | "soft";
type NotificationType = "error" | "success" | "warning";

interface WebApp {
  initData: string;
  colorScheme: "light" | "dark";
  ready(): void;
  expand(): void;
  disableVerticalSwipes?(): void;
  setHeaderColor?(color: string): void;
  setBackgroundColor?(color: string): void;
  HapticFeedback?: {
    impactOccurred(style: HapticStyle): void;
    notificationOccurred(type: NotificationType): void;
    selectionChanged(): void;
  };
  showConfirm?(message: string, callback: (ok: boolean) => void): void;
}

declare global {
  interface Window {
    Telegram?: { WebApp?: WebApp };
  }
}

function webApp(): WebApp | undefined {
  return window.Telegram?.WebApp;
}

export const isInsideTelegram = (): boolean => Boolean(webApp()?.initData);

export function initTelegram(): void {
  const app = webApp();
  if (!app) return;
  app.ready();
  app.expand();
  // Свайп вниз внутри мини-аппа Telegram трактует как «закрыть».
  // На экране «Карта» это происходит при обычной прокрутке.
  app.disableVerticalSwipes?.();
  app.setHeaderColor?.("#0A0B0D");
  app.setBackgroundColor?.("#0A0B0D");
}

/** initData уходит в заголовке каждого запроса — это и есть авторизация. */
export function getInitData(): string {
  return webApp()?.initData ?? "";
}

/** Смещение часового пояса. Telegram его не даёт, а стрик без него врёт. */
export function tzOffsetMinutes(): number {
  return -new Date().getTimezoneOffset();
}

export const haptic = {
  tap(): void {
    webApp()?.HapticFeedback?.impactOccurred("light");
  },
  select(): void {
    webApp()?.HapticFeedback?.selectionChanged();
  },
  success(): void {
    webApp()?.HapticFeedback?.notificationOccurred("success");
  },
  warning(): void {
    webApp()?.HapticFeedback?.notificationOccurred("warning");
  },
};

/**
 * Подтверждение в стиле Telegram. Вне мессенджера падает на обычный confirm,
 * чтобы удаление можно было проверить в браузере.
 */
export function confirmAction(message: string): Promise<boolean> {
  const app = webApp();
  if (app?.showConfirm) {
    return new Promise((resolve) => app.showConfirm!(message, resolve));
  }
  return Promise.resolve(window.confirm(message));
}
