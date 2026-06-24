export function SplitView({
  left,
  right,
}: {
  left: React.ReactNode;
  right: React.ReactNode;
}) {
  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 h-full min-h-0">
      <div className="min-h-0 flex flex-col">{left}</div>
      <div className="min-h-0 overflow-auto">{right}</div>
    </div>
  );
}
