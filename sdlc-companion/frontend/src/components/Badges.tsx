import type { GateStatus } from "../api/types";

const GATE_STYLE: Record<GateStatus, string> = {
  locked: "border-line text-slate-400",
  passed: "border-rag-green/50 text-rag-green",
  needs_review: "border-rag-amber/50 text-rag-amber",
};

const GATE_LABEL: Record<GateStatus, string> = {
  locked: "locked",
  passed: "passed",
  needs_review: "needs review",
};

export function GateBadge({ status }: { status: GateStatus }) {
  return <span className={`chip ${GATE_STYLE[status]}`}>{GATE_LABEL[status]}</span>;
}

export function RingBadge({ ring }: { ring?: string | null }) {
  if (!ring) return null;
  const color =
    ring === "adopt"
      ? "border-rag-green/50 text-rag-green"
      : ring === "trial"
        ? "border-rag-amber/50 text-rag-amber"
        : "border-rag-red/50 text-rag-red";
  return <span className={`chip ${color}`}>{ring}</span>;
}

export function StaleBadge({ stale }: { stale: boolean }) {
  if (!stale) return null;
  return <span className="chip border-rag-amber/60 text-rag-amber">stale</span>;
}
