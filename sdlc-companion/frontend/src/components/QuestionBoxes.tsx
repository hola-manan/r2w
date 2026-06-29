import { useState } from "react";

export interface OpenQuestion {
  key: string;
  name: string;
  question: string;
}

// Bundle the answered boxes into a single message of `- <question>: <answer>`
// lines so the agent receives one structured turn instead of a free-form blob.
function formatAnswers(questions: OpenQuestion[], answers: Record<string, string>): string {
  return questions
    .map((q) => [q, answers[q.key]?.trim()] as const)
    .filter(([, a]) => a)
    .map(([q, a]) => `- ${q.question} ${a}`)
    .join("\n");
}

export function QuestionBoxes({
  questions,
  onSubmit,
  busy,
}: {
  questions: OpenQuestion[];
  onSubmit: (text: string) => void;
  busy: boolean;
}) {
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const hasAnswer = questions.some((q) => answers[q.key]?.trim());

  const submit = () => {
    if (busy || !hasAnswer) return;
    onSubmit(formatAnswers(questions, answers));
    setAnswers({});
  };

  return (
    <div className="border-t border-line p-3 space-y-3">
      <p className="text-xs uppercase tracking-wide text-slate-500">
        Open questions — answer in the boxes below
      </p>
      {questions.map((q) => (
        <div key={q.key} className="space-y-1">
          <label className="block text-xs text-accent">
            <span className="text-slate-400">{q.name}: </span>
            {q.question}
          </label>
          <textarea
            className="input"
            rows={2}
            value={answers[q.key] ?? ""}
            placeholder="Your answer…"
            onChange={(e) =>
              setAnswers((a) => ({ ...a, [q.key]: e.target.value }))
            }
          />
        </div>
      ))}
      <button
        className="btn btn-primary w-full"
        onClick={submit}
        disabled={busy || !hasAnswer}
      >
        Submit answers
      </button>
    </div>
  );
}
