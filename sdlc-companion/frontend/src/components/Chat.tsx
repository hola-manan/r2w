import { useRef, useState } from "react";
import type { Attachment } from "../api/types";
import { api } from "../api/client";
import { QuestionBoxes, type OpenQuestion } from "./QuestionBoxes";

export interface ChatMessage {
  role: "user" | "agent";
  content: string;
  attachments?: string[]; // filenames, rendered as chips in the log
}

export function Chat({
  projectId,
  messages,
  onSend,
  busy,
  placeholder,
  questions = [],
}: {
  projectId: string;
  messages: ChatMessage[];
  onSend: (text: string, attachments: Attachment[]) => void;
  busy: boolean;
  placeholder?: string;
  questions?: OpenQuestion[];
}) {
  const [text, setText] = useState("");
  const [attachments, setAttachments] = useState<Attachment[]>([]);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState("");
  const fileRef = useRef<HTMLInputElement>(null);

  const submit = () => {
    const t = text.trim();
    if ((!t && attachments.length === 0) || busy) return;
    onSend(t, attachments);
    setText("");
    setAttachments([]);
  };

  const pickFile = async (file: File | undefined) => {
    if (fileRef.current) fileRef.current.value = ""; // allow re-picking the same file
    if (!file) return;
    setUploadError("");
    setUploading(true);
    try {
      const att = await api.extract(projectId, file);
      setAttachments((a) => [...a, att]);
    } catch (e) {
      setUploadError(String(e));
    } finally {
      setUploading(false);
    }
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
            {m.attachments && m.attachments.length > 0 && (
              <div className="mt-1 flex flex-wrap gap-1">
                {m.attachments.map((name, j) => (
                  <span key={j} className="chip border-line text-slate-300">
                    📎 {name}
                  </span>
                ))}
              </div>
            )}
          </div>
        ))}
        {busy && <div className="text-xs text-slate-500">thinking…</div>}
      </div>

      {questions.length > 0 && (
        <QuestionBoxes
          questions={questions}
          onSubmit={(t) => onSend(t, [])}
          busy={busy}
        />
      )}

      {(attachments.length > 0 || uploading || uploadError) && (
        <div className="border-t border-line px-3 pt-2 flex flex-wrap items-center gap-2">
          {attachments.map((a, i) => (
            <span key={i} className="chip border-line text-slate-300">
              📎 {a.filename}
              <button
                className="ml-1 text-slate-500 hover:text-slate-200"
                onClick={() => setAttachments((cur) => cur.filter((_, j) => j !== i))}
              >
                ×
              </button>
            </span>
          ))}
          {uploading && <span className="text-xs text-slate-500">extracting…</span>}
          {uploadError && <span className="text-xs text-rag-red">{uploadError}</span>}
        </div>
      )}

      <div className="border-t border-line p-3 flex gap-2">
        <input
          ref={fileRef}
          type="file"
          accept=".docx,.xlsx"
          className="hidden"
          onChange={(e) => pickFile(e.target.files?.[0])}
        />
        <button
          className="btn"
          title="Attach a .docx or .xlsx"
          onClick={() => fileRef.current?.click()}
          disabled={busy || uploading}
        >
          📎
        </button>
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
