import { useState } from "react";

import type { ClarifyQuestion, Criterion, Goal, GoalDetail } from "@/types";
import { Sheet } from "@/components/Sheet";
import { StepCriteria } from "@/screens/CreateGoal/StepCriteria";
import { StepGenerating } from "@/screens/CreateGoal/StepGenerating";
import { StepGoal } from "@/screens/CreateGoal/StepGoal";
import { StepQuestions } from "@/screens/CreateGoal/StepQuestions";
import { StepReady } from "@/screens/CreateGoal/StepReady";
import { haptic } from "@/lib/telegram";

/**
 * Всё, что мастеру нужно от внешнего мира. На шаге 4 сюда приходит
 * заглушка с демо-данными, на шаге 5 — реальные вызовы React Query.
 * Сам мастер про сеть не знает.
 */
export interface WizardApi {
  clarify(title: string, durationDays: number): Promise<ClarifyQuestion[]>;
  create(
    title: string,
    durationDays: number,
    answers: Array<{ question: string; answer: string }>,
  ): Promise<{ goal: Goal; criteria: Criterion[] }>;
  updateCriteria(goalId: string, texts: string[]): Promise<void>;
  generate(
    goalId: string,
    answers: Array<{ question: string; answer: string }>,
  ): Promise<GoalDetail>;
}

interface Props {
  open: boolean;
  api: WizardApi;
  onClose: () => void;
  onFinished: (goal: GoalDetail) => void;
}

type Stage = "goal" | "questions" | "criteria" | "generating" | "ready";

export function CreateGoalSheet({ open, api, onClose, onFinished }: Props) {
  const [stage, setStage] = useState<Stage>("goal");
  const [busy, setBusy] = useState(false);
  const [failed, setFailed] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [title, setTitle] = useState("");
  const [duration, setDuration] = useState(90);
  const [questions, setQuestions] = useState<ClarifyQuestion[]>([]);
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [goalId, setGoalId] = useState<string | null>(null);
  const [criteria, setCriteria] = useState<string[]>([]);
  const [ready, setReady] = useState<GoalDetail | null>(null);

  /** Шагов всего два, если цель уже конкретная: уточнение пропускается. */
  const totalSteps = questions.length > 0 ? 3 : 2;
  const currentStep =
    stage === "goal" ? 1 : stage === "questions" ? 2 : totalSteps;

  function reset() {
    setStage("goal");
    setBusy(false);
    setFailed(false);
    setError(null);
    setTitle("");
    setDuration(90);
    setQuestions([]);
    setAnswers({});
    setGoalId(null);
    setCriteria([]);
    setReady(null);
  }

  async function goToCriteria(
    withAnswers: Array<{ question: string; answer: string }>,
  ) {
    setBusy(true);
    try {
      const created = await api.create(title.trim(), duration, withAnswers);
      setGoalId(created.goal.id);
      setCriteria(created.criteria.map((item) => item.text));
      setStage("criteria");
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Не получилось. Попробуй ещё раз.",
      );
    } finally {
      setBusy(false);
    }
  }

  async function handleFirstStep() {
    setBusy(true);
    setError(null);
    try {
      const asked = await api.clarify(title.trim(), duration);
      if (asked.length === 0) {
        await goToCriteria([]);
        return;
      }
      setQuestions(asked);
      setStage("questions");
    } catch (err) {
      // Молчаливая кнопка — худшее, что может случиться в мастере:
      // человек жмёт и не понимает, сломалось или думает.
      setError(
        err instanceof Error ? err.message : "Не получилось. Попробуй ещё раз.",
      );
    } finally {
      setBusy(false);
    }
  }

  async function handleGenerate() {
    if (!goalId) return;
    setStage("generating");
    setFailed(false);
    try {
      await api.updateCriteria(
        goalId,
        criteria.map((text) => text.trim()).filter(Boolean),
      );
      const detail = await api.generate(
        goalId,
        questions.map((item) => ({
          question: item.question,
          answer: answers[item.question] ?? "",
        })),
      );
      setReady(detail);
      haptic.success();
      setStage("ready");
    } catch {
      // Цель осталась в draft — введённое не потеряно, поэтому предлагаем
      // именно «попробовать ещё раз», а не начинать заново.
      setFailed(true);
    }
  }

  const heading =
    stage === "generating"
      ? "Собираю маршрут"
      : stage === "ready"
        ? "Маршрут готов"
        : `Шаг ${currentStep} из ${totalSteps}`;

  return (
    <Sheet
      open={open}
      onClose={
        stage === "generating" && !failed
          ? undefined
          : () => {
              reset();
              onClose();
            }
      }
      heading={heading}
      steps={
        stage === "generating" || stage === "ready"
          ? undefined
          : { total: totalSteps, current: currentStep }
      }
    >
      {stage === "goal" && (
        <StepGoal
          title={title}
          duration={duration}
          busy={busy}
          error={error}
          onTitleChange={setTitle}
          onDurationChange={setDuration}
          onNext={() => void handleFirstStep()}
        />
      )}

      {stage === "questions" && (
        <StepQuestions
          questions={questions}
          answers={answers}
          busy={busy}
          onAnswer={(question, option) =>
            setAnswers((previous) => ({ ...previous, [question]: option }))
          }
          onNext={() =>
            void goToCriteria(
              questions.map((item) => ({
                question: item.question,
                answer: answers[item.question] ?? "",
              })),
            )
          }
        />
      )}

      {stage === "criteria" && (
        <StepCriteria
          criteria={criteria}
          busy={busy}
          onChange={(index, value) =>
            setCriteria((previous) =>
              previous.map((text, position) => (position === index ? value : text)),
            )
          }
          onGenerate={() => void handleGenerate()}
        />
      )}

      {stage === "generating" && (
        <StepGenerating
          durationDays={duration}
          failed={failed}
          onRetry={() => void handleGenerate()}
        />
      )}

      {stage === "ready" && ready && (
        <StepReady
          goal={ready}
          onStart={() => {
            const finished = ready;
            reset();
            onFinished(finished);
          }}
        />
      )}
    </Sheet>
  );
}
