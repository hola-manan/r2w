import type { Artifact } from "../api/types";
import { LinkChips } from "./LinkChips";
import { StaleBadge } from "./Badges";

function titleOf(a: Artifact): string {
  return (
    (a.title as string) ||
    (a.statement as string) ||
    (a.decision as string) ||
    (a.name as string) ||
    a.id
  );
}

const HIDE = new Set([
  "id", "doc_type", "project_id", "version", "created_by_agent",
  "last_changed", "stale", "links_out", "links_in", "title", "statement",
  "decision", "name",
]);

export function ArtifactCard({
  artifact,
  children,
}: {
  artifact: Artifact;
  children?: React.ReactNode;
}) {
  const fields = Object.entries(artifact).filter(
    ([k, v]) =>
      !HIDE.has(k) &&
      v !== null &&
      v !== "" &&
      !(Array.isArray(v) && v.length === 0) &&
      !(typeof v === "object" && !Array.isArray(v) && Object.keys(v as object).length === 0),
  );
  return (
    <div className={`card ${artifact.stale ? "border-rag-amber/40" : ""}`}>
      <div className="flex items-start justify-between gap-2">
        <div>
          <span className="text-xs text-accent font-mono">{artifact.id}</span>
          <h3 className="font-medium text-slate-100">{titleOf(artifact)}</h3>
        </div>
        <StaleBadge stale={artifact.stale} />
      </div>
      <dl className="mt-2 space-y-1 text-sm text-slate-300">
        {fields.map(([k, v]) => (
          <div key={k} className="flex gap-2">
            <dt className="text-slate-500 min-w-[7rem]">{k}</dt>
            <dd className="flex-1">{render(v)}</dd>
          </div>
        ))}
      </dl>
      <LinkChips out={artifact.links_out} inc={artifact.links_in} />
      {children}
    </div>
  );
}

function render(v: unknown): React.ReactNode {
  if (Array.isArray(v)) return v.join(", ");
  if (typeof v === "object") return JSON.stringify(v);
  return String(v);
}
