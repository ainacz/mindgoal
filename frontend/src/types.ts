/**
 * Доменные типы. Повторяют схемы Pydantic с бэкенда один в один —
 * если там что-то поменяется, здесь должно поменяться следом.
 */

export type GoalStatus =
  | "draft"
  | "generating"
  | "active"
  | "completed"
  | "archived";

export interface ChecklistItem {
  id: string;
  text: string;
  is_done: boolean;
  order_index: number;
}

export interface DailyTask {
  id: string;
  day_number: number;
  title: string;
  estimated_minutes: number;
  description: string;
  hint: string | null;
  is_completed: boolean;
  completed_at: string | null;
  is_simplified: boolean;
  checklist: ChecklistItem[];
}

export interface Phase {
  id: string;
  title: string;
  start_day: number;
  end_day: number;
  order_index: number;
}

export interface Criterion {
  id: string;
  text: string;
  is_completed: boolean;
  order_index: number;
}

export interface Goal {
  id: string;
  title: string;
  category: string | null;
  duration_days: number;
  current_day: number;
  generated_until_day: number;
  status: GoalStatus;
  streak_days: number;
  created_at: string;
  completed_at: string | null;
}

export interface GoalDetail extends Goal {
  last_completed_date: string | null;
  criteria: Criterion[];
  phases: Phase[];
  tasks: DailyTask[];
}

export interface Today {
  goal_id: string;
  goal_title: string;
  current_day: number;
  duration_days: number;
  streak_days: number;
  total_xp: number;
  phase_title: string | null;
  task: DailyTask | null;
}

export interface ClarifyQuestion {
  question: string;
  options: string[];
}

export type Tab = "today" | "map" | "goals";
