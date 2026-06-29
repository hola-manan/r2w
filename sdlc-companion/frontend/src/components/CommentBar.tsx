// Batch-submit bar for pending artifact comments. Shown only when there is at
// least one queued comment; submitting sends them all to the stage agent.
export function CommentBar({
  count,
  busy,
  onSubmit,
  onClear,
}: {
  count: number;
  busy: boolean;
  onSubmit: () => void;
  onClear: () => void;
}) {
  if (count === 0) return null;
  return (
    <div className="card flex items-center gap-3 border-accent/40">
      <span className="text-sm text-slate-200">
        {count} comment{count === 1 ? "" : "s"} pending
      </span>
      <div className="ml-auto flex gap-2">
        <button className="btn" onClick={onClear} disabled={busy}>
          Clear
        </button>
        <button className="btn btn-primary" onClick={onSubmit} disabled={busy}>
          Submit comments
        </button>
      </div>
    </div>
  );
}
