"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import { apiRequest, getStoredToken } from "@/lib/api";
import { Alert, Notification } from "@/lib/types";
import { openOrgAlertsSocket } from "@/lib/ws";

export default function AlertsPage() {
  const router = useRouter();
  const [token, setToken] = useState<string | null>(null);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [liveMessage, setLiveMessage] = useState<string | null>(null);
  const [form, setForm] = useState({
    name: "High error volume",
    event_name: "error_logged",
    threshold: 5,
    window_minutes: 10,
    webhook_url: "",
    notify_email: "",
  });

  async function load(currentToken: string) {
    const [nextAlerts, nextNotifications] = await Promise.all([
      apiRequest<Alert[]>("/alerts", {}, currentToken),
      apiRequest<Notification[]>("/alerts/notifications/list", {}, currentToken),
    ]);
    setAlerts(nextAlerts);
    setNotifications(nextNotifications);
  }

  useEffect(() => {
    const stored = getStoredToken();
    if (!stored) {
      router.replace("/");
      return;
    }
    setToken(stored);
    void load(stored);

    const socket = openOrgAlertsSocket(stored, (payload) => {
      const data = payload as { type?: string; message?: string; name?: string };
      if (data.type === "alert_triggered") {
        setLiveMessage(`Alert triggered: ${data.name ?? "unknown"}`);
        void load(stored);
      }
      if (data.type === "alert_resolved") {
        setLiveMessage(`Alert resolved: ${data.name ?? "unknown"}`);
        void load(stored);
      }
    });

    return () => socket.close();
  }, [router]);

  async function createAlert() {
    if (!token) return;
    await apiRequest<Alert>(
      "/alerts",
      {
        method: "POST",
        body: JSON.stringify({
          ...form,
          webhook_url: form.webhook_url || null,
          notify_email: form.notify_email || null,
        }),
      },
      token,
    );
    await load(token);
  }

  async function muteAlert(alertId: number) {
    if (!token) return;
    await apiRequest<Alert>(`/alerts/${alertId}/mute`, { method: "POST", body: JSON.stringify({ minutes: 60 }) }, token);
    await load(token);
  }

  return (
    <div className="space-y-8 p-6 lg:p-10">
      <section className="rounded-[2rem] border border-stone-200 bg-white p-6 shadow-sm">
        <p className="text-xs uppercase tracking-[0.28em] text-orange-500">Alerts</p>
        <h2 className="mt-2 text-3xl font-semibold text-stone-950">Threshold monitoring</h2>
        <p className="mt-2 text-sm text-stone-600">
          Alerts evaluate every minute via Celery Beat. Triggered alerts create in-app notifications and optional webhooks.
        </p>
        {liveMessage ? (
          <p className="mt-4 rounded-2xl border border-orange-200 bg-orange-50 px-4 py-3 text-sm text-orange-900">{liveMessage}</p>
        ) : null}
      </section>

      <section className="grid gap-6 xl:grid-cols-2">
        <div className="rounded-[2rem] border border-stone-200 bg-white p-6 shadow-sm">
          <p className="text-xs uppercase tracking-[0.24em] text-stone-500">New alert rule</p>
          <div className="mt-4 space-y-3">
            <input className="w-full rounded-2xl border border-stone-200 px-4 py-3" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} placeholder="Name" />
            <input className="w-full rounded-2xl border border-stone-200 px-4 py-3" value={form.event_name} onChange={(e) => setForm({ ...form, event_name: e.target.value })} placeholder="Event name" />
            <div className="grid grid-cols-2 gap-3">
              <input type="number" className="rounded-2xl border border-stone-200 px-4 py-3" value={form.threshold} onChange={(e) => setForm({ ...form, threshold: Number(e.target.value) })} placeholder="Threshold" />
              <input type="number" className="rounded-2xl border border-stone-200 px-4 py-3" value={form.window_minutes} onChange={(e) => setForm({ ...form, window_minutes: Number(e.target.value) })} placeholder="Window (min)" />
            </div>
            <input className="w-full rounded-2xl border border-stone-200 px-4 py-3" value={form.webhook_url} onChange={(e) => setForm({ ...form, webhook_url: e.target.value })} placeholder="Webhook URL (Slack-compatible)" />
            <button className="rounded-2xl bg-stone-950 px-4 py-3 text-sm font-semibold text-white" onClick={createAlert}>
              Create alert
            </button>
          </div>
        </div>

        <div className="rounded-[2rem] border border-stone-200 bg-white p-6 shadow-sm">
          <p className="text-xs uppercase tracking-[0.24em] text-stone-500">Active rules</p>
          <div className="mt-4 space-y-3">
            {alerts.map((alert) => (
              <div key={alert.id} className="rounded-2xl border border-stone-200 bg-stone-50 p-4">
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <p className="font-semibold text-stone-950">{alert.name}</p>
                    <p className="mt-1 text-sm text-stone-600">
                      {alert.event_name} &gt; {alert.threshold} in {alert.window_minutes}m
                    </p>
                  </div>
                  <span className="rounded-full bg-stone-200 px-3 py-1 text-xs font-medium uppercase">{alert.status}</span>
                </div>
                {alert.status !== "muted" ? (
                  <button className="mt-3 text-sm text-orange-600" onClick={() => muteAlert(alert.id)}>
                    Mute 1 hour
                  </button>
                ) : null}
              </div>
            ))}
            {alerts.length === 0 ? <p className="text-sm text-stone-500">No alerts configured yet.</p> : null}
          </div>
        </div>
      </section>

      <section className="rounded-[2rem] border border-stone-200 bg-white p-6 shadow-sm">
        <p className="text-xs uppercase tracking-[0.24em] text-stone-500">In-app notifications</p>
        <div className="mt-4 space-y-3">
          {notifications.map((item) => (
            <div key={item.id} className={`rounded-2xl border p-4 ${item.read ? "border-stone-200 bg-stone-50" : "border-orange-200 bg-orange-50"}`}>
              <p className="font-semibold text-stone-950">{item.title}</p>
              <p className="mt-1 text-sm text-stone-600">{item.message}</p>
            </div>
          ))}
          {notifications.length === 0 ? <p className="text-sm text-stone-500">No notifications yet.</p> : null}
        </div>
      </section>
    </div>
  );
}
