"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { useEffect, useMemo, useState } from "react";

import { apiRequest, getStoredToken, login, setStoredToken } from "@/lib/api";
import { User } from "@/lib/types";

type Notice = {
  tone: "info" | "success" | "error";
  text: string;
};

const INITIAL_NOTICE: Notice = {
  tone: "info",
  text: "Create an organization, invite operators, and start ingesting product or business events.",
};

export function HomePage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const inviteToken = searchParams.get("invite");
  const [mode, setMode] = useState<"signup" | "login" | "invite">(inviteToken ? "invite" : "signup");
  const [loading, setLoading] = useState(false);
  const [notice, setNotice] = useState<Notice>(INITIAL_NOTICE);
  const [signupForm, setSignupForm] = useState({
    organization_name: "",
    email: "",
    password: "",
  });
  const [loginForm, setLoginForm] = useState({
    email: "",
    password: "",
  });
  const [inviteForm, setInviteForm] = useState({
    password: "",
  });

  useEffect(() => {
    if (inviteToken) {
      return;
    }
    if (getStoredToken()) {
      router.replace("/workspace");
    }
  }, [inviteToken, router]);

  useEffect(() => {
    setMode(inviteToken ? "invite" : "signup");
  }, [inviteToken]);

  const introTitle = useMemo(() => {
    if (mode === "invite") {
      return "Accept your workspace invitation";
    }
    return "Ship an analytics workspace that operators can actually use";
  }, [mode]);

  async function handleSignup() {
    setLoading(true);
    try {
      await apiRequest<User>("/auth/signup", {
        method: "POST",
        body: JSON.stringify({
          ...signupForm,
          role: "Viewer",
        }),
      });
      const token = await login(signupForm.email, signupForm.password);
      setStoredToken(token.access_token);
      router.replace("/workspace");
    } catch (error) {
      setNotice({ tone: "error", text: (error as Error).message });
    } finally {
      setLoading(false);
    }
  }

  async function handleLogin() {
    setLoading(true);
    try {
      const token = await login(loginForm.email, loginForm.password);
      setStoredToken(token.access_token);
      router.replace("/workspace");
    } catch (error) {
      setNotice({ tone: "error", text: (error as Error).message });
    } finally {
      setLoading(false);
    }
  }

  async function handleAcceptInvite() {
    if (!inviteToken) {
      setNotice({ tone: "error", text: "Invitation token is missing from the URL." });
      return;
    }

    setLoading(true);
    try {
      const invitedUser = await apiRequest<User>("/auth/invitations/accept", {
        method: "POST",
        body: JSON.stringify({
          token: inviteToken,
          password: inviteForm.password,
        }),
      });
      const token = await login(invitedUser.email, inviteForm.password);
      setStoredToken(token.access_token);
      router.replace("/workspace");
    } catch (error) {
      setNotice({ tone: "error", text: (error as Error).message });
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="min-h-screen bg-stone-950 px-4 py-8 text-stone-100 sm:px-6 lg:px-8">
      <div className="mx-auto grid max-w-6xl gap-8 lg:grid-cols-[1.1fr_0.9fr]">
        <section className="rounded-[2rem] border border-stone-800 bg-stone-900 p-8 shadow-2xl">
          <p className="text-xs uppercase tracking-[0.32em] text-orange-400">Pulseboard Analytics</p>
          <h1 className="mt-4 max-w-2xl text-4xl font-semibold tracking-tight text-white sm:text-5xl">{introTitle}</h1>
          <p className="mt-5 max-w-2xl text-base leading-7 text-stone-300">
            Multi-tenant access, API-key secured ingestion, CSV imports, dashboard templates, and team onboarding are all
            available in the product flow below.
          </p>

          <div className="mt-8 grid gap-4 sm:grid-cols-2">
            {[
              ["Authentication", "JWT access tokens, refresh cookies, invite-based onboarding, and role hierarchy."],
              ["Ingestion", "Single event, batch event, CSV, and webhook-compatible payload handling."],
              ["Dashboards", "Custom dashboards, widget types, time ranges, auto-refresh, and public sharing."],
              ["Isolation", "Organization-scoped queries for users, keys, dashboards, and event history."],
            ].map(([title, body]) => (
              <div key={title} className="rounded-3xl border border-stone-800 bg-stone-950/60 p-5">
                <p className="text-sm font-semibold text-white">{title}</p>
                <p className="mt-2 text-sm leading-6 text-stone-400">{body}</p>
              </div>
            ))}
          </div>
        </section>

        <section className="rounded-[2rem] border border-stone-200 bg-white p-6 text-stone-900 shadow-2xl">
          {!inviteToken ? (
            <div className="flex gap-2 rounded-full bg-stone-100 p-1 text-sm">
              <button
                className={`flex-1 rounded-full px-4 py-2 ${mode === "signup" ? "bg-stone-950 text-white" : "text-stone-600"}`}
                onClick={() => setMode("signup")}
              >
                Create organization
              </button>
              <button
                className={`flex-1 rounded-full px-4 py-2 ${mode === "login" ? "bg-stone-950 text-white" : "text-stone-600"}`}
                onClick={() => setMode("login")}
              >
                Sign in
              </button>
            </div>
          ) : null}

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

          {mode === "signup" ? (
            <div className="mt-6 space-y-4">
              <input
                className="w-full rounded-2xl border border-stone-200 px-4 py-3 outline-none transition focus:border-orange-400"
                placeholder="Organization name"
                value={signupForm.organization_name}
                onChange={(event) => setSignupForm({ ...signupForm, organization_name: event.target.value })}
              />
              <input
                className="w-full rounded-2xl border border-stone-200 px-4 py-3 outline-none transition focus:border-orange-400"
                placeholder="Work email"
                value={signupForm.email}
                onChange={(event) => {
                  const email = event.target.value;
                  setSignupForm({ ...signupForm, email });
                  setLoginForm((current) => ({ ...current, email }));
                }}
              />
              <input
                className="w-full rounded-2xl border border-stone-200 px-4 py-3 outline-none transition focus:border-orange-400"
                placeholder="Password"
                type="password"
                value={signupForm.password}
                onChange={(event) => setSignupForm({ ...signupForm, password: event.target.value })}
              />
              <button
                className="w-full rounded-2xl bg-orange-500 px-4 py-3 font-semibold text-white transition hover:bg-orange-600 disabled:opacity-60"
                onClick={handleSignup}
                disabled={loading}
              >
                {loading ? "Creating workspace..." : "Create workspace"}
              </button>
            </div>
          ) : null}

          {mode === "login" ? (
            <div className="mt-6 space-y-4">
              <input
                className="w-full rounded-2xl border border-stone-200 px-4 py-3 outline-none transition focus:border-orange-400"
                placeholder="Work email"
                value={loginForm.email}
                onChange={(event) => setLoginForm({ ...loginForm, email: event.target.value })}
              />
              <input
                className="w-full rounded-2xl border border-stone-200 px-4 py-3 outline-none transition focus:border-orange-400"
                placeholder="Password"
                type="password"
                value={loginForm.password}
                onChange={(event) => setLoginForm({ ...loginForm, password: event.target.value })}
              />
              <button
                className="w-full rounded-2xl bg-stone-950 px-4 py-3 font-semibold text-white transition hover:bg-stone-800 disabled:opacity-60"
                onClick={handleLogin}
                disabled={loading}
              >
                {loading ? "Signing in..." : "Sign in"}
              </button>
            </div>
          ) : null}

          {mode === "invite" ? (
            <div className="mt-6 space-y-4">
              <input
                className="w-full rounded-2xl border border-stone-200 px-4 py-3 outline-none transition focus:border-orange-400"
                placeholder="Choose a password"
                type="password"
                value={inviteForm.password}
                onChange={(event) => setInviteForm({ password: event.target.value })}
              />
              <button
                className="w-full rounded-2xl bg-orange-500 px-4 py-3 font-semibold text-white transition hover:bg-orange-600 disabled:opacity-60"
                onClick={handleAcceptInvite}
                disabled={loading}
              >
                {loading ? "Joining workspace..." : "Accept invitation"}
              </button>
            </div>
          ) : null}
        </section>
      </div>
    </main>
  );
}
