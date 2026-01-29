import Link from "next/link";

export default function AppShell({
  title,
  subtitle,
  children,
  right,
}: {
  title: string;
  subtitle?: string;
  children: React.ReactNode;
  right?: React.ReactNode;
}) {
  return (
    <main className="min-h-screen bg-neutral-50">
      <header className="sticky top-0 z-10 border-b bg-white/80 backdrop-blur">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
          <div className="flex items-center gap-3">
            <Link
              href="/"
              className="rounded-xl border px-3 py-2 text-sm text-neutral-700 hover:bg-neutral-50"
            >
              ← Dashboard
            </Link>
            <div>
              <div className="text-lg font-semibold">{title}</div>
              {subtitle ? (
                <div className="text-xs text-neutral-500">{subtitle}</div>
              ) : null}
            </div>
          </div>
          <div className="flex items-center gap-2">{right}</div>
        </div>
      </header>

      <div className="mx-auto max-w-6xl px-6 py-6">{children}</div>
    </main>
  );
}
