"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { LoadingSpinner } from "@/components/loading-spinner";
import { apiRequest, clearStoredToken, getStoredToken, refreshAccessToken, setStoredToken } from "@/lib/api";
import { ApiKey, Dashboard, Invitation, Organization, User } from "@/lib/types";

type WorkspaceState = {
  user: User;
  organization: Organization;
  dashboards: Dashboard[];
  apiKeys: ApiKey[];
  invitations: Invitation[];
};

export default function WorkspaceOverviewPage() {
  const router = useRouter();
  const [data, setData] = useState<WorkspaceState | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      const stored = getStoredToken();
      if (!stored) {
        router.replace("/");
        return;
      }

      try {
        await hydrate(stored);
      } catch {
        try {
          const refreshed = await refreshAccessToken();
          setStoredToken(refreshed.access_token);
          await hydrate(refreshed.access_token);
        } catch (refreshError) {
          clearStoredToken();
          setError((refreshError as Error).message);
          router.replace("/");
        }
      } finally {
        setLoading(false);
      }
    }

    async function hydrate(token: string) {
      const [user, organization, dashboards, apiKeys, invitations] = await Promise.all([
        apiRequest<User>("/auth/me", {}, token),
        apiRequest<Organization>("/organizations/me", {}, token),
        apiRequest<Dashboard[]>("/dashboards", {}, token),
        apiRequest<ApiKey[]>("/organizations/api-keys", {}, token).catch(() => []),
        apiRequest<Invitation[]>("/auth/invitations", {}, token).catch(() => []),
      ]);
      setData({ user, organization, dashboards, apiKeys, invitations });
    }

    void load();
  }, [router]);

  if (loading) {
    return <LoadingSpinner label="Loading workspace" />;
  }

  if (!data) {
    return <div className="p-8 text-sm text-rose-700">{error ?? "Unable to load workspace."}</div>;
  }

  const activeKeys = data.apiKeys.filter((item) => !item.revoked_at).length;
  const pendingInvites = data.invitations.filter((item) => !item.accepted_at).length;

  return (
    <div className="space-y-8 p-6 lg:p-10">
      <section className="rounded-[2rem] border border-stone-200 bg-white p-6 shadow-sm">
        <p className="text-xs uppercase tracking-[0.28em] text-orange-500">Workspace overview</p>
        <div className="mt-3 flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <h2 className="text-3xl font-semibold text-stone-950">{data.organization.name}</h2>
            <p className="mt-2 max-w-2xl text-sm leading-6 text-stone-600">
              Signed in as {data.user.email} with the {data.user.role} role. Use the product sections on the left to manage
              keys, ingest events, and assemble dashboards.
            </p>
          </div>
          <div className="rounded-2xl border border-stone-200 bg-stone-50 px-4 py-3 text-sm text-stone-600">
            Org slug: <span className="mono text-stone-900">{data.organization.slug}</span>
          </div>
        </div>
      </section>

      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {[
          ["Active API keys", String(activeKeys)],
          ["Dashboards", String(data.dashboards.length)],
          ["Pending invites", String(pendingInvites)],
          ["Refresh cadence", data.dashboards[0] ? `${data.dashboards[0].refresh_interval_seconds}s default` : "Not set"],
        ].map(([label, value]) => (
          <div key={label} className="rounded-[1.5rem] border border-stone-200 bg-white p-5 shadow-sm">
            <p className="text-xs uppercase tracking-[0.24em] text-stone-500">{label}</p>
            <p className="mt-3 text-3xl font-semibold text-stone-950">{value}</p>
          </div>
        ))}
      </section>

      <section className="grid gap-6 xl:grid-cols-[1.2fr_0.8fr]">
        <div className="rounded-[2rem] border border-stone-200 bg-white p-6 shadow-sm">
          <div className="flex items-center justify-between gap-4">
            <div>
              <p className="text-xs uppercase tracking-[0.24em] text-stone-500">Dashboards</p>
              <h3 className="mt-1 text-xl font-semibold text-stone-950">Current surfaces</h3>
            </div>
            <Link className="rounded-2xl bg-stone-950 px-4 py-3 text-sm font-medium text-white" href="/workspace/dashboards">
              Open dashboards
            </Link>
          </div>

          <div className="mt-5 space-y-3">
            {data.dashboards.length > 0 ? (
              data.dashboards.map((dashboard) => (
                <div key={dashboard.id} className="rounded-2xl border border-stone-200 bg-stone-50 p-4">
                  <div className="flex items-center justify-between gap-4">
                    <div>
                      <p className="font-semibold text-stone-950">{dashboard.name}</p>
                      <p className="mt-1 text-sm text-stone-600">{dashboard.description || "No description provided."}</p>
                    </div>
                    <span className="rounded-full bg-white px-3 py-1 text-xs text-stone-600">
                      {dashboard.is_public ? "Public" : "Team-only"}
                    </span>
                  </div>
                </div>
              ))
            ) : (
              <div className="rounded-2xl border border-dashed border-stone-300 p-5 text-sm text-stone-600">
                No dashboards yet. Create one from a blank canvas or from a template.
              </div>
            )}
          </div>
        </div>

        <div className="rounded-[2rem] border border-stone-200 bg-white p-6 shadow-sm">
          <p className="text-xs uppercase tracking-[0.24em] text-stone-500">Suggested flow</p>
          <h3 className="mt-1 text-xl font-semibold text-stone-950">What to do next</h3>
          <ol className="mt-5 space-y-4 text-sm leading-6 text-stone-700">
            <li>1. Create or rotate an API key from the Ingestion section.</li>
            <li>2. Submit a sample event or upload a CSV using that key.</li>
            <li>3. Create a dashboard template and add widgets for the event names you just sent.</li>
            <li>4. Invite another user with the right role for review.</li>
          </ol>
          <div className="mt-6 grid gap-3">
            <Link className="rounded-2xl bg-orange-500 px-4 py-3 text-center text-sm font-semibold text-white" href="/workspace/ingestion">
              Go to ingestion
            </Link>
            <Link className="rounded-2xl border border-stone-300 px-4 py-3 text-center text-sm font-semibold text-stone-900" href="/workspace/team">
              Manage team access
            </Link>
          </div>
        </div>
      </section>
    </div>
  );
}
