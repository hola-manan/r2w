import type { Scorecard as ScorecardData } from "../api/types";

const DOT: Record<string, string> = {
  red: "bg-rag-red",
  amber: "bg-rag-amber",
  green: "bg-rag-green",
};

export function Scorecard({ card }: { card: ScorecardData | null }) {
  if (!card) {
    return (
      <div className="card text-sm text-slate-500">
        Readiness scorecard appears here as the conversation progresses.
      </div>
    );
  }
  return (
    <div className="card">
      <div className="flex items-center justify-between mb-3">
        <h3 className="font-medium text-slate-100">Readiness</h3>
        <span
          className={`chip ${
            card.gate_passed
              ? "border-rag-green/50 text-rag-green"
              : "border-rag-amber/50 text-rag-amber"
          }`}
        >
          {card.gate_passed ? "gate open" : "gate locked"}
        </span>
      </div>
      <ul className="space-y-2">
        {card.dimensions.map((d) => (
          <li key={d.key} className="text-sm">
            <div className="flex items-center gap-2">
              <span className={`h-2.5 w-2.5 rounded-full ${DOT[d.rag]}`} />
              <span className="text-slate-200">{d.name}</span>
              {d.kind === "hard" && (
                <span className="chip border-line text-slate-500">hard</span>
              )}
              <span className="ml-auto text-slate-500">L{d.level}</span>
            </div>
            {d.justification && (
              <p className="ml-4 text-xs text-slate-500">{d.justification}</p>
            )}
            {d.followup_question && (
              <p className="ml-4 text-xs text-accent">→ {d.followup_question}</p>
            )}
          </li>
        ))}
      </ul>
      <div className="mt-3 text-xs text-slate-500">
        weighted soft {Math.round(card.weighted_soft * 100)}% / threshold{" "}
        {Math.round(card.threshold * 100)}%
        {card.blockers.length > 0 && (
          <span className="text-rag-amber"> · blockers: {card.blockers.join(", ")}</span>
        )}
      </div>
    </div>
  );
}
