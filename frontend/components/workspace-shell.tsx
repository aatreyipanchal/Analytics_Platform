"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { PropsWithChildren } from "react";

import { clearStoredToken, logout } from "@/lib/api";

const navItems = [
  { href: "/workspace", label: "Overview" },
  { href: "/workspace/ingestion", label: "Ingestion" },
  { href: "/workspace/dashboards", label: "Dashboards" },
  { href: "/workspace/alerts", label: "Alerts" },
  { href: "/workspace/team", label: "Team" },
];

export function WorkspaceShell({ children }: PropsWithChildren) {
  const pathname = usePathname();
  const router = useRouter();

  async function handleLogout() {
    try {
      await logout();
    } catch {
      // Ignore logout failures; local session should still be cleared.
    }
    clearStoredToken();
    router.replace("/");
  }

  return (
    <div className="min-h-screen bg-stone-950 text-stone-100">
      <div className="mx-auto flex min-h-screen max-w-7xl flex-col lg:flex-row">
        <aside className="border-b border-stone-800 bg-stone-950 px-5 py-6 lg:min-h-screen lg:w-72 lg:border-b-0 lg:border-r">
          <div className="space-y-1">
            <p className="text-xs uppercase tracking-[0.28em] text-orange-400">Pulseboard</p>
            <h1 className="text-2xl font-semibold text-stone-50">Analytics Control Plane</h1>
            <p className="text-sm leading-6 text-stone-400">
              Manage workspace access, ingest event streams, and curate dashboards from one product surface.
            </p>
          </div>

          <nav className="mt-8 space-y-2">
            {navItems.map((item) => {
              const active = pathname === item.href;
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`block rounded-2xl px-4 py-3 text-sm transition ${
                    active
                      ? "bg-orange-500 text-white"
                      : "border border-stone-800 bg-stone-900 text-stone-300 hover:border-stone-700 hover:text-white"
                  }`}
                >
                  {item.label}
                </Link>
              );
            })}
          </nav>

          <div className="mt-8 rounded-2xl border border-stone-800 bg-stone-900 p-4 text-sm text-stone-400">
            Use the Ingestion page to create a key, submit sample events, or upload CSV data. Dashboards consume the
            same event stream immediately.
          </div>

          <button
            className="mt-6 w-full rounded-2xl border border-stone-700 px-4 py-3 text-sm font-medium text-stone-200 transition hover:border-stone-500 hover:bg-stone-900"
            onClick={handleLogout}
          >
            Sign out
          </button>
        </aside>

        <main className="flex-1 bg-stone-100 text-stone-900">{children}</main>
      </div>
    </div>
  );
}
