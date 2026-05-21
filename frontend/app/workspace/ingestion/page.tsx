"use client";

import { ChangeEvent, useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";

import { LoadingSpinner } from "@/components/loading-spinner";
import { apiRequest, getApiBase, getStoredToken } from "@/lib/api";
import { ApiKey, EventRecord, User } from "@/lib/types";
import { openOrgEventsSocket } from "@/lib/ws";

type Notice = {
  tone: "info" | "success" | "error";
  text: string;
};

const SAMPLE_EVENT = {
  event_name: "signup_completed",
  timestamp: "2026-05-20T10:30:00+00:00",
  user_id: "user_42",
  properties: {
    source: "landing-page",
    plan: "pro",
  },
};

export default function IngestionPage() {
  const router = useRouter();
  const [token, setToken] = useState<string | null>(null);
  const [user, setUser] = useState<User | null>(null);
  const [apiKeys, setApiKeys] = useState<ApiKey[]>([]);
  const [recentEvents, setRecentEvents] = useState<EventRecord[]>([]);
  const [notice, setNotice] = useState<Notice>({
    tone: "info",
    text: "Generate an ingestion key, paste it into the test field, and send sample events directly from this screen.",
  });
  const [apiKeyName, setApiKeyName] = useState("Primary ingestion key");
  const [ingestionSecret, setIngestionSecret] = useState("");
  const [samplePayload, setSamplePayload] = useState(JSON.stringify(SAMPLE_EVENT, null, 2));
  const [csvFile, setCsvFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(true);

  const sampleCurl = useMemo(
    () =>
      `curl -X POST ${getApiBase()}/events \\\n  -H "Content-Type: application/json" \\\n  -H "X-API-Key: ${ingestionSecret || "<paste-key-here>"}" \\\n  -d '${JSON.stringify(SAMPLE_EVENT)}'`,
    [ingestionSecret],
  );

  useEffect(() => {
    const stored = getStoredToken();
    if (!stored) {
      router.replace("/");
      return;
    }
    setToken(stored);

    async function load() {
      try {
        const [nextUser, nextKeys, nextEvents] = await Promise.all([
          apiRequest<User>("/auth/me", {}, stored),
          apiRequest<ApiKey[]>("/organizations/api-keys", {}, stored),
          apiRequest<EventRecord[]>("/events/recent", {}, stored),
        ]);
        setUser(nextUser);
        setApiKeys(nextKeys);
        setRecentEvents(nextEvents);
      } catch (error) {
        setNotice({ tone: "error", text: (error as Error).message });
      } finally {
        setLoading(false);
      }
    }

    void load();

    const socket = openOrgEventsSocket(stored, () => {
      void refreshEvents(stored);
    });
    return () => socket.close();
  }, [router]);

  async function refreshEvents(currentToken = token) {
    if (!currentToken) {
      return;
    }
    const nextEvents = await apiRequest<EventRecord[]>("/events/recent", {}, currentToken);
    setRecentEvents(nextEvents);
  }

  async function createApiKey() {
    if (!token) {
      return;
    }
    const created = await apiRequest<ApiKey>(
      "/organizations/api-keys",
      { method: "POST", body: JSON.stringify({ name: apiKeyName }) },
      token,
    );
    setApiKeys((current) => [created, ...current]);
    if (created.secret) {
      setIngestionSecret(created.secret);
    }
    setNotice({
      tone: "success",
      text: created.secret
        ? `API key created. Copy the full secret now: ${created.secret}`
        : "API key created.",
    });
  }

  async function rotateApiKey(id: number) {
    if (!token) {
      return;
    }
    const rotated = await apiRequest<ApiKey>(`/organizations/api-keys/${id}/rotate`, { method: "POST" }, token);
    setApiKeys((current) => current.map((item) => (item.id === id ? rotated : item)));
    if (rotated.secret) {
      setIngestionSecret(rotated.secret);
    }
    setNotice({
      tone: "success",
      text: rotated.secret
        ? `API key rotated. New secret: ${rotated.secret}`
        : "API key rotated.",
    });
  }

  async function revokeApiKey(id: number) {
    if (!token) {
      return;
    }
    await apiRequest<void>(`/organizations/api-keys/${id}`, { method: "DELETE" }, token);
    setApiKeys((current) =>
      current.map((item) => (item.id === id ? { ...item, revoked_at: new Date().toISOString() } : item)),
    );
    setNotice({ tone: "success", text: "API key revoked." });
  }

  async function sendSampleEvent() {
    try {
      await apiRequest("/events", {
        method: "POST",
        body: samplePayload,
        headers: {
          "X-API-Key": ingestionSecret,
        },
      });
      setNotice({ tone: "success", text: "Sample event accepted. Refreshing recent event stream..." });
      await new Promise((resolve) => window.setTimeout(resolve, 700));
      await refreshEvents();
    } catch (error) {
      setNotice({ tone: "error", text: (error as Error).message });
    }
  }

  async function uploadCsv() {
    if (!csvFile) {
      setNotice({ tone: "error", text: "Choose a CSV file first." });
      return;
    }

    const formData = new FormData();
    formData.append("file", csvFile);

    try {
      await apiRequest("/events/upload/csv", {
        method: "POST",
        body: formData,
        headers: {
          "X-API-Key": ingestionSecret,
        },
      });
      setNotice({ tone: "success", text: "CSV accepted. Events are being normalized in the background." });
      await new Promise((resolve) => window.setTimeout(resolve, 700));
      await refreshEvents();
    } catch (error) {
      setNotice({ tone: "error", text: (error as Error).message });
    }
  }

  function handleCsvChange(event: ChangeEvent<HTMLInputElement>) {
    setCsvFile(event.target.files?.[0] ?? null);
  }

  if (loading) {
    return <LoadingSpinner label="Loading ingestion controls" />;
  }

  return (
    <div className="space-y-8 p-6 lg:p-10">
      <section className="rounded-[2rem] border border-stone-200 bg-white p-6 shadow-sm">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <p className="text-xs uppercase tracking-[0.28em] text-orange-500">Ingestion</p>
            <h2 className="mt-2 text-3xl font-semibold text-stone-950">Data sources and event intake</h2>
            <p className="mt-2 max-w-3xl text-sm leading-6 text-stone-600">
              Use API keys to ingest single events, batches, CSV uploads, or webhook-style payloads. Event records land in
              the same organization-isolated stream that powers dashboards.
            </p>
          </div>
          <div className="rounded-2xl border border-stone-200 bg-stone-50 px-4 py-3 text-sm text-stone-600">
            Role: <span className="font-semibold text-stone-900">{user?.role}</span>
          </div>
        </div>

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

      <section className="grid gap-6 xl:grid-cols-[0.9fr_1.1fr]">
        <div className="rounded-[2rem] border border-stone-200 bg-white p-6 shadow-sm">
          <p className="text-xs uppercase tracking-[0.24em] text-stone-500">API keys</p>
          <h3 className="mt-1 text-xl font-semibold text-stone-950">Generate and rotate credentials</h3>
          <div className="mt-5 flex gap-3">
            <input
              className="flex-1 rounded-2xl border border-stone-200 px-4 py-3"
              value={apiKeyName}
              onChange={(event) => setApiKeyName(event.target.value)}
            />
            <button className="rounded-2xl bg-stone-950 px-4 py-3 text-sm font-semibold text-white" onClick={createApiKey}>
              Create
            </button>
          </div>

          <label className="mt-5 block text-sm font-medium text-stone-700">Current ingestion secret</label>
          <input
            className="mt-2 w-full rounded-2xl border border-stone-200 px-4 py-3 font-mono text-sm"
            placeholder="Paste a full API key secret here"
            value={ingestionSecret}
            onChange={(event) => setIngestionSecret(event.target.value)}
          />

          <div className="mt-5 space-y-3">
            {apiKeys.map((apiKey) => (
              <div key={apiKey.id} className="rounded-2xl border border-stone-200 bg-stone-50 p-4">
                <div className="flex items-center justify-between gap-3">
                  <div>
                    <p className="font-semibold text-stone-950">{apiKey.name}</p>
                    <p className="mono text-xs text-stone-500">{apiKey.secret ?? apiKey.prefix}</p>
                  </div>
                  <span className={`rounded-full px-3 py-1 text-xs ${apiKey.revoked_at ? "bg-rose-100 text-rose-700" : "bg-emerald-100 text-emerald-700"}`}>
                    {apiKey.revoked_at ? "Revoked" : "Active"}
                  </span>
                </div>
                <div className="mt-4 flex gap-3">
                  <button className="rounded-2xl border border-stone-300 px-4 py-2 text-sm" onClick={() => rotateApiKey(apiKey.id)}>
                    Rotate
                  </button>
                  <button className="rounded-2xl border border-rose-200 px-4 py-2 text-sm text-rose-700" onClick={() => revokeApiKey(apiKey.id)}>
                    Revoke
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="space-y-6">
          <div className="rounded-[2rem] border border-stone-200 bg-white p-6 shadow-sm">
            <p className="text-xs uppercase tracking-[0.24em] text-stone-500">Single event</p>
            <h3 className="mt-1 text-xl font-semibold text-stone-950">Send a test payload</h3>
            <textarea
              className="mt-5 h-56 w-full rounded-2xl border border-stone-200 px-4 py-3 font-mono text-sm"
              value={samplePayload}
              onChange={(event) => setSamplePayload(event.target.value)}
            />
            <button
              className="mt-4 rounded-2xl bg-orange-500 px-4 py-3 text-sm font-semibold text-white"
              onClick={sendSampleEvent}
            >
              Submit sample event
            </button>
          </div>

          <div className="rounded-[2rem] border border-stone-200 bg-white p-6 shadow-sm">
            <p className="text-xs uppercase tracking-[0.24em] text-stone-500">CSV upload</p>
            <h3 className="mt-1 text-xl font-semibold text-stone-950">Bulk import events</h3>
            <p className="mt-2 text-sm text-stone-600">
              Expected columns: <span className="mono">event_name,timestamp,user_id,properties</span>
            </p>
            <input className="mt-4 block w-full text-sm" type="file" accept=".csv" onChange={handleCsvChange} />
            <button className="mt-4 rounded-2xl bg-stone-950 px-4 py-3 text-sm font-semibold text-white" onClick={uploadCsv}>
              Upload CSV
            </button>
          </div>
        </div>
      </section>

      <section className="grid gap-6 xl:grid-cols-[1fr_1fr]">
        <div className="rounded-[2rem] border border-stone-200 bg-white p-6 shadow-sm">
          <p className="text-xs uppercase tracking-[0.24em] text-stone-500">API reference</p>
          <h3 className="mt-1 text-xl font-semibold text-stone-950">Sample request</h3>
          <pre className="mt-5 overflow-auto rounded-2xl bg-stone-950 p-4 text-sm text-stone-100">{sampleCurl}</pre>
        </div>

        <div className="rounded-[2rem] border border-stone-200 bg-white p-6 shadow-sm">
          <p className="text-xs uppercase tracking-[0.24em] text-stone-500">Recent events</p>
          <h3 className="mt-1 text-xl font-semibold text-stone-950">Organization event stream</h3>
          <div className="mt-5 space-y-3">
            {recentEvents.length > 0 ? (
              recentEvents.map((event) => (
                <div key={event.id} className="rounded-2xl border border-stone-200 bg-stone-50 p-4">
                  <div className="flex items-start justify-between gap-4">
                    <div>
                      <p className="font-semibold text-stone-950">{event.event_name}</p>
                      <p className="mono mt-1 text-xs text-stone-500">{event.user_id}</p>
                    </div>
                    <span className="rounded-full bg-white px-3 py-1 text-xs text-stone-600">{event.source}</span>
                  </div>
                  <p className="mt-3 text-xs text-stone-500">{new Date(event.timestamp).toLocaleString()}</p>
                </div>
              ))
            ) : (
              <div className="rounded-2xl border border-dashed border-stone-300 p-5 text-sm text-stone-600">
                No events ingested yet. Send a sample event or upload a CSV to populate this stream.
              </div>
            )}
          </div>
        </div>
      </section>
    </div>
  );
}
