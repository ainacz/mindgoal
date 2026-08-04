import { useEffect, useState } from "react";

import type { ChecklistItem, DailyTask, Tab } from "@/types";
import { ApiError, api } from "@/api";
import { CreateGoalSheet } from "@/screens/CreateGoal/CreateGoalSheet";
import { Empty } from "@/components/Empty";
import { GoalsScreen } from "@/screens/GoalsScreen";
import { MapScreen } from "@/screens/MapScreen";
import { Sheet } from "@/components/Sheet";
import { TabBar } from "@/components/TabBar";
import { TodayScreen } from "@/screens/TodayScreen";
import { initTelegram } from "@/lib/telegram";
import { useResource } from "@/useResource";

export default function App() {
  const [tab, setTab] = useState<Tab>("today");
  const [activeId, setActiveId] = useState<string | null>(null);
  const [wizardOpen, setWizardOpen] = useState(false);
  const [openedDay, setOpenedDay] = useState<DailyTask | null>(null);
  const [completing, setCompleting] = useState(false);

  useEffect(initTelegram, []);

  const session = useResource(api.session, "session");
  const goals = useResource(api.listGoals, "goals");
  const goal = useResource(
    () => (activeId ? api.goal(activeId) : Promise.resolve(null)),
    `goal:${activeId}`,
  );
  const today = useResource(
    () => (activeId ? api.today(activeId) : Promise.resolve(null)),
    `today:${activeId}`,
  );

  // Первая активная цель выбирается сама: выбирать не из чего, пока она одна.
  useEffect(() => {
    if (!activeId && goals.data?.length) {
      setActiveId(goals.data.find((g) => g.status === "active")?.id ?? goals.data[0].id);
    }
  }, [goals.data, activeId]);

  const authFailed =
    session.error instanceof ApiError && session.error.status === 401;

  if (authFailed) {
    return (
      <div className="flex h-full flex-col justify-center">
        <Empty
          title="Открой через Telegram"
          hint="Приложение работает только внутри мессенджера — там оно получает подпись, по которой мы узнаём тебя."
        />
      </div>
    );
  }

  async function toggleChecklistItem(item: ChecklistItem, next: boolean) {
    // Оптимистично: галочка не должна ждать сеть. При ошибке возвращаем как было.
    const undo = () => today.reload();
    today.setData((current) =>
      current?.task
        ? {
            ...current,
            task: {
              ...current.task,
              checklist: current.task.checklist.map((entry) =>
                entry.id === item.id ? { ...entry, is_done: next } : entry,
              ),
            },
          }
        : current,
    );
    await api.setChecklistItem(item, next).catch(undo);
  }

  async function completeDay() {
    const task = today.data?.task;
    if (!task || completing) return;
    setCompleting(true);
    try {
      await api.completeDay(task.id);
      await Promise.all([today.reload(), goal.reload(), goals.reload()]);
    } finally {
      setCompleting(false);
    }
  }

  const todayTitleByGoal = Object.fromEntries(
    (goals.data ?? []).map((item) => [
      item.id,
      item.id === activeId ? today.data?.task?.title : undefined,
    ]),
  );

  return (
    <div className="relative mx-auto flex h-full max-w-[430px] flex-col overflow-hidden bg-ink">
      {tab === "today" &&
        (today.data && goal.data ? (
          <TodayScreen
            today={today.data}
            phaseStarts={goal.data.phases.map((phase) => phase.start_day)}
            completing={completing}
            onToggleChecklistItem={(item, next) => void toggleChecklistItem(item, next)}
            onCompleteDay={() => void completeDay()}
            onSimplify={() => undefined}
            onMentor={() => undefined}
            onRetryGeneration={() => void today.reload()}
          />
        ) : (
          <Loading
            loading={today.loading || goals.loading}
            error={today.error}
            onRetry={() => void today.reload()}
            onCreate={() => setWizardOpen(true)}
            hasGoals={Boolean(goals.data?.length)}
          />
        ))}

      {tab === "map" && goal.data && (
        <MapScreen
          goal={goal.data}
          totalXp={session.data?.total_xp ?? 0}
          onOpenDay={setOpenedDay}
        />
      )}

      {tab === "goals" && (
        <GoalsScreen
          userName={session.data?.first_name ?? "Мои цели"}
          goals={goals.data ?? []}
          totalXp={session.data?.total_xp ?? 0}
          todayTitleByGoal={todayTitleByGoal}
          onOpenGoal={(item) => {
            setActiveId(item.id);
            setTab("today");
          }}
          onDeleteGoal={(item) => {
            void api.deleteGoal(item.id).then(() => {
              if (item.id === activeId) setActiveId(null);
              return goals.reload();
            });
          }}
          onCreateGoal={() => setWizardOpen(true)}
        />
      )}

      <TabBar active={tab} onChange={setTab} />

      <CreateGoalSheet
        open={wizardOpen}
        api={{
          clarify: api.clarify,
          create: api.createGoal,
          updateCriteria: async (id, texts) => {
            await api.updateCriteria(id, texts);
          },
          generate: async (id) => {
            await api.generate(id);
            return api.goal(id);
          },
        }}
        onClose={() => setWizardOpen(false)}
        onFinished={(created) => {
          setActiveId(created.id);
          setWizardOpen(false);
          setTab("today");
          void goals.reload();
        }}
      />

      <Sheet
        open={openedDay !== null}
        onClose={() => setOpenedDay(null)}
        heading={openedDay ? `День ${openedDay.day_number}` : ""}
      >
        {openedDay && (
          <>
            <h2 className="mt-5 font-display text-[22px] font-medium leading-snug text-bone">
              {openedDay.title}
            </h2>
            <div className="mt-2 label-dim">
              {openedDay.estimated_minutes} мин
              {openedDay.is_completed && " · закрыт"}
            </div>
            <p className="mt-3 text-[13.5px] leading-relaxed text-muted">
              {openedDay.description}
            </p>
            <ul className="mt-5 border-t border-line-soft">
              {openedDay.checklist.map((entry) => (
                <li
                  key={entry.id}
                  className="border-b border-line-soft py-3 text-[13.5px] text-muted"
                >
                  {entry.text}
                </li>
              ))}
            </ul>
          </>
        )}
      </Sheet>
    </div>
  );
}

function Loading({
  loading,
  error,
  hasGoals,
  onRetry,
  onCreate,
}: {
  loading: boolean;
  error: Error | null;
  hasGoals: boolean;
  onRetry: () => void;
  onCreate: () => void;
}) {
  if (loading) {
    return (
      <div className="flex flex-1 items-center justify-center label-dim">
        Загружаю
      </div>
    );
  }
  if (error) {
    return (
      <Empty
        title="Не получилось загрузить"
        hint={error.message}
        action={
          <button type="button" onClick={onRetry} className="btn-ghost">
            Попробовать ещё раз
          </button>
        }
      />
    );
  }
  if (!hasGoals) {
    return (
      <Empty
        title="Пока ни одной цели"
        hint="Напиши, чего хочешь достичь, и получишь маршрут из ежедневных шагов по пятнадцать минут."
        action={
          <button type="button" onClick={onCreate} className="btn-primary">
            Создать цель
          </button>
        }
      />
    );
  }
  return <div className="flex-1" />;
}
