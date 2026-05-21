"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import { LoadingSpinner } from "@/components/loading-spinner";
import { apiRequest, getStoredToken } from "@/lib/api";
import { Invitation, User } from "@/lib/types";

type Notice = {
  tone: "info" | "success" | "error";
  text: string;
};

export default function TeamPage() {
  const router = useRouter();
  const [token, setToken] = useState<string | null>(null);
  const [user, setUser] = useState<User | null>(null);
  const [invitations, setInvitations] = useState<Invitation[]>([]);
  const [inviteForm, setInviteForm] = useState({ email: "", role: "Analyst" });
  const [notice, setNotice] = useState<Notice>({
    tone: "info",
    text: "Owners and admins can invite teammates into the current organization with scoped roles.",
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const stored = getStoredToken();
    if (!stored) {
      router.replace("/");
      return;
    }
    setToken(stored);

    async function load() {
      try {
        const [currentUser, currentInvitations] = await Promise.all([
          apiRequest<User>("/auth/me", {}, stored),
          apiRequest<Invitation[]>("/auth/invitations", {}, stored).catch(() => []),
        ]);
        setUser(currentUser);
        setInvitations(currentInvitations);
      } catch (error) {
        setNotice({ tone: "error", text: (error as Error).message });
      } finally {
        setLoading(false);
      }
    }

    void load();
  }, [router]);

  async function createInvitation() {
    if (!token) {
      return;
    }
    try {
      const created = await apiRequest<Invitation>("/auth/invitations", {
        method: "POST",
        body: JSON.stringify(inviteForm),
      }, token);
      setInvitations((current) => [created, ...current]);
      setNotice({ tone: "success", text: `Invite created for ${created.email}. Share the generated link below.` });
    } catch (error) {
      setNotice({ tone: "error", text: (error as Error).message });
    }
  }

  if (loading) {
    return <LoadingSpinner label="Loading team access" />;
  }

  return (
    <div className="space-y-8 p-6 lg:p-10">
      <section className="rounded-[2rem] border border-stone-200 bg-white p-6 shadow-sm">
        <p className="text-xs uppercase tracking-[0.28em] text-orange-500">Team access</p>
        <h2 className="mt-2 text-3xl font-semibold text-stone-950">Invite-based onboarding and role controls</h2>
        <p className="mt-2 max-w-3xl text-sm leading-6 text-stone-600">
          Operators join through invitation links. Endpoint guards enforce Owner → Admin → Analyst → Viewer access across
          organization-scoped APIs.
        </p>
        <div
          className={`mt-5 rounded-3xl border px-4 py-3 text-sm ${
            notice.tone === "error"
              ? "border-rose-200 bg-rose-50 text-rose-900"
              : notice.tone === "success"
                ? "border-emerald-200 bg-emerald-50 text-emerald-900"
                : "border-stone-200 bg-stone-50 text-stone-700"
          }`}
        >
          {notice.text}
        </div>
      </section>

      <section className="grid gap-6 xl:grid-cols-[0.85fr_1.15fr]">
        <div className="space-y-6">
          <div className="rounded-[2rem] border border-stone-200 bg-white p-6 shadow-sm">
            <p className="text-xs uppercase tracking-[0.24em] text-stone-500">Current operator</p>
            <h3 className="mt-1 text-xl font-semibold text-stone-950">{user?.email}</h3>
            <p className="mt-2 text-sm text-stone-600">Role: {user?.role}</p>
          </div>

          <div className="rounded-[2rem] border border-stone-200 bg-white p-6 shadow-sm">
            <p className="text-xs uppercase tracking-[0.24em] text-stone-500">Role hierarchy</p>
            <div className="mt-4 space-y-3">
              {[
                ["Owner", "Full administrative control, organization settings, and access governance."],
                ["Admin", "Invites, API key management, and workspace administration."],
                ["Analyst", "Dashboard creation and metric exploration."],
                ["Viewer", "Read-only dashboard access."],
              ].map(([role, text]) => (
                <div key={role} className="rounded-2xl border border-stone-200 bg-stone-50 p-4">
                  <p className="font-semibold text-stone-950">{role}</p>
                  <p className="mt-1 text-sm text-stone-600">{text}</p>
                </div>
              ))}
            </div>
          </div>
        </div>

        <div className="rounded-[2rem] border border-stone-200 bg-white p-6 shadow-sm">
          <p className="text-xs uppercase tracking-[0.24em] text-stone-500">Invitations</p>
          <h3 className="mt-1 text-xl font-semibold text-stone-950">Create teammate invite</h3>
          <div className="mt-5 grid gap-3 sm:grid-cols-[1fr_160px_auto]">
            <input
              className="rounded-2xl border border-stone-200 px-4 py-3"
              placeholder="teammate@company.com"
              value={inviteForm.email}
              onChange={(event) => setInviteForm({ ...inviteForm, email: event.target.value })}
            />
            <select
              className="rounded-2xl border border-stone-200 px-4 py-3"
              value={inviteForm.role}
              onChange={(event) => setInviteForm({ ...inviteForm, role: event.target.value })}
            >
              <option>Admin</option>
              <option>Analyst</option>
              <option>Viewer</option>
            </select>
            <button className="rounded-2xl bg-stone-950 px-4 py-3 text-sm font-semibold text-white" onClick={createInvitation}>
              Invite
            </button>
          </div>

          <div className="mt-6 space-y-3">
            {invitations.length > 0 ? (
              invitations.map((invite) => (
                <div key={invite.id} className="rounded-2xl border border-stone-200 bg-stone-50 p-4">
                  <div className="flex items-center justify-between gap-3">
                    <div>
                      <p className="font-semibold text-stone-950">{invite.email}</p>
                      <p className="mt-1 text-xs text-stone-500">{invite.role}</p>
                    </div>
                    <span className={`rounded-full px-3 py-1 text-xs ${invite.accepted_at ? "bg-emerald-100 text-emerald-700" : "bg-amber-100 text-amber-700"}`}>
                      {invite.accepted_at ? "Accepted" : "Pending"}
                    </span>
                  </div>
                  <a className="mono mt-3 block break-all text-xs text-orange-700" href={invite.invite_link}>
                    {invite.invite_link}
                  </a>
                </div>
              ))
            ) : (
              <div className="rounded-2xl border border-dashed border-stone-300 p-5 text-sm text-stone-600">
                No invitations yet. Create one to test invite-based onboarding.
              </div>
            )}
          </div>
        </div>
      </section>
    </div>
  );
}
