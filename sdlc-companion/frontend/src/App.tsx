import { Link, Outlet } from "react-router-dom";

export default function App() {
  return (
    <div className="min-h-full flex flex-col">
      <header className="border-b border-line px-6 py-3 flex items-center gap-3">
        <Link to="/" className="font-semibold tracking-tight text-slate-100">
          <span className="text-accent">◆</span> SDLC Companion
        </Link>
        <span className="text-xs text-slate-500">
          requirements → PRD → stack → spec → tasks
        </span>
      </header>
      <main className="flex-1 min-h-0">
        <Outlet />
      </main>
    </div>
  );
}
