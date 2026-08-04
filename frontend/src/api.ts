/**
 * Клиент бэкенда. Голый fetch — без React Query.
 *
 * У нас три выборки и одна инвалидация. Кэш, ключи, провайдер и devtools
 * ради этого не окупаются; ТЗ допускало и Fetch. Когда экранов станет
 * больше, а перекрёстных инвалидаций — десяток, поменяем: все вызовы
 * уже собраны в одном файле.
 */

import type {
  ChecklistItem,
  ClarifyQuestion,
  Criterion,
  DailyTask,
  Goal,
  GoalDetail,
  Today,
} from "@/types";
import { getInitData, tzOffsetMinutes } from "@/lib/telegram";

const BASE = import.meta.env.VITE_API_URL ?? "";

export class ApiError extends Error {
  constructor(
    readonly status: number,
    message: string,
  ) {
    super(message);
  }
}

async function req<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(BASE + path, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      // Подпись Telegram и есть авторизация — уходит с каждым запросом.
      "X-Telegram-Init-Data": getInitData(),
      ...init?.headers,
    },
  });

  if (!response.ok) {
    const body = (await response.json().catch(() => ({}))) as { detail?: string };
    throw new ApiError(response.status, body.detail ?? response.statusText);
  }
  return response.status === 204 ? (undefined as T) : ((await response.json()) as T);
}

const post = <T>(path: string, body?: unknown) =>
  req<T>(path, { method: "POST", body: body ? JSON.stringify(body) : undefined });

export const api = {
  session: () =>
    post<{ id: number; first_name: string | null; total_xp: number }>(
      "/api/session",
      { tz_offset_minutes: tzOffsetMinutes() },
    ),

  listGoals: () => req<Goal[]>("/api/goals"),
  goal: (id: string) => req<GoalDetail>(`/api/goals/${id}`),
  today: (id: string) => req<Today>(`/api/goals/${id}/today`),

  clarify: (title: string, duration_days: number) =>
    post<{ questions: ClarifyQuestion[] }>("/api/goals/clarify", {
      title,
      duration_days,
    }).then((r) => r.questions),

  createGoal: (
    title: string,
    duration_days: number,
    answers: Array<{ question: string; answer: string }>,
  ) =>
    post<{ goal: Goal; criteria: Criterion[]; reality_note: string | null }>("/api/goals", {
      title,
      duration_days,
      answers,
    }),

  updateCriteria: (id: string, texts: string[]) =>
    req<Criterion[]>(`/api/goals/${id}/criteria`, {
      method: "PATCH",
      body: JSON.stringify({ texts }),
    }),

  // Ответы про точку старта нужны генератору маршрута, а не только
  // критериям — иначе дни одинаковые у новичка и у продолжающего.
  generate: (id: string, answers: Array<{ question: string; answer: string }>) =>
    post<Goal>(`/api/goals/${id}/generate`, { answers }),
  completeDay: (taskId: string, resultNote: string | null) =>
    post<unknown>(`/api/tasks/${taskId}/complete`, { result_note: resultNote }),
  simplifyDay: (taskId: string) =>
    post<DailyTask>(`/api/tasks/${taskId}/simplify`),
  ensureDays: (id: string) => post<{ added: number }>(`/api/goals/${id}/ensure-days`),
  deleteGoal: (id: string) => req<void>(`/api/goals/${id}`, { method: "DELETE" }),

  setChecklistItem: (item: ChecklistItem, is_done: boolean) =>
    req<ChecklistItem>(`/api/checklist/${item.id}`, {
      method: "PATCH",
      body: JSON.stringify({ is_done }),
    }),
};
