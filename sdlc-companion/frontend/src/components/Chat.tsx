import { useState } from "react";

export interface ChatMessage {
  role: "user" | "agent";
  content: string;
}

export function Chat({
  messages,
  onSend,
  busy,
  placeholder,
}: {
  messages: ChatMessage[];
  onSend: (text: string) => void;
  busy: boolean;
  placeholder?: string;
}) {
  const [text, setText] = useState("");
  const submit = () => {
    const t = text.trim();
    if (!t || busy) return;
    onSend(t);
    setText("");
  };
  return (
    <div className="flex flex-col h-full min-h-0 card p-0">
      <div className="flex-1 min-h-0 overflow-auto p-4 space-y-3">
        {messages.length === 0 && (
          <p className="text-sm text-slate-500">{placeholder || "Start the conversation…"}</p>
        )}
        {messages.map((m, i) => (
          <div
            key={i}
            className={`max-w-[85%] rounded-lg px-3 py-2 text-sm ${
              m.role === "user"
                ? "ml-auto bg-accent-dim text-white"
                : "bg-ink-soft text-slate-200"
            }`}
          >
            {m.content}
          </div>
        ))}
        {busy && <div className="text-xs text-slate-500">thinking…</div>}
      </div>
      <div className="border-t border-line p-3 flex gap-2">
        <input
          className="input"
          value={text}
          placeholder="Type a message…"
          onChange={(e) => setText(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && submit()}
        />
        <button className="btn btn-primary" onClick={submit} disabled={busy}>
          Send
        </button>
      </div>
    </div>
  );
}
