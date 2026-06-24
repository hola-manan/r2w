import type { LinkChip } from "../api/types";

// Traceability chips: render the upstream/downstream node IDs an artifact links.
export function LinkChips({
  out = [],
  inc = [],
}: {
  out?: LinkChip[];
  inc?: LinkChip[];
}) {
  if (out.length === 0 && inc.length === 0) return null;
  return (
    <div className="flex flex-wrap gap-1.5 mt-2">
      {out.map((l, i) => (
        <span key={`o${i}`} className="chip text-slate-300" title={l.edge}>
          → {l.to}
        </span>
      ))}
      {inc.map((l, i) => (
        <span key={`i${i}`} className="chip text-slate-400" title={l.edge}>
          ← {l.from}
        </span>
      ))}
    </div>
  );
}
