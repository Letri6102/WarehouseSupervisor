import Link from "next/link";

export default function NavCard({
  href,
  title,
  desc,
  meta,
}: {
  href: string;
  title: string;
  desc: string;
  meta?: string;
}) {
  return (
    <Link
      href={href}
      className="group rounded-3xl border bg-white p-5 shadow-sm hover:shadow-md transition"
    >
      <div className="flex items-start justify-between gap-3">
        <div>
          <div className="text-lg font-semibold group-hover:underline">
            {title}
          </div>
          <div className="mt-1 text-sm text-neutral-600">{desc}</div>
        </div>
        {meta ? (
          <span className="rounded-full bg-neutral-100 px-3 py-1 text-xs text-neutral-700">
            {meta}
          </span>
        ) : null}
      </div>
    </Link>
  );
}
