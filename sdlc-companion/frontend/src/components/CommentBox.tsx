import { useState } from "react";

// Controlled review-comment editor for a single artifact. The parent owns the
// value (collected into the stage's pending-comments batch); a non-empty value
// means this artifact has a comment queued for the next "Submit comments".
export function CommentBox({
  value,
  onChange,
}: {
  value: string;
  onChange: (text: string) => void;
}) {
  const [open, setOpen] = useState(false);
  const has = value.trim() !== "";
  const expanded = open || has;

  if (!expanded) {
    return (
      <button
        className="mt-2 text-xs text-slate-500 hover:text-accent"
        onClick={() => setOpen(true)}
      >
        💬 Comment
      </button>
    );
  }
  return (
    <div className={`mt-2 rounded-md p-2 ${has ? "bg-accent-dim/20 border border-accent/40" : ""}`}>
      <div className="flex items-center justify-between mb-1">
        <span className="text-xs text-slate-500">Review comment</span>
        <button
          className="text-xs text-slate-500 hover:text-slate-200"
          title="Remove comment"
          onClick={() => {
            onChange("");
            setOpen(false);
          }}
        >
          ×
        </button>
      </div>
      <textarea
        className="input"
        rows={2}
        autoFocus
        value={value}
        placeholder="What should the agent change about this artifact?"
        onChange={(e) => onChange(e.target.value)}
      />
    </div>
  );
}
