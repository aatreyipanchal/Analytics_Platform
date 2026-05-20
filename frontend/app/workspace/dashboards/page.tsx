"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";

import { WidgetPanel } from "@/components/widget-panel";
import { apiRequest, getApiBase, getStoredToken } from "@/lib/api";
import { Dashboard, DashboardTemplate, Widget, WidgetData } from "@/lib/types";

type Notice = {
  tone: "info" | "success" | "error";
  text: string;
};

export default function DashboardsPage() {
  const router = useRouter();
  const [token, setToken] = useState<string | null>(null);
  const [dashboards, setDashboards] = useState<Dashboard[]>([]);
  const [templates, setTemplates] = useState<DashboardTemplate[]>([]);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [widgetData, setWidgetData] = useState<WidgetData[]>([]);
  const [notice, setNotice] = useState<Notice>({
    tone: "info",
    text: "Create a dashboard or start from a template, then attach widgets to the event names you ingest.",
  });
  const [dashboardForm, setDashboardForm] = useState({
    name: "Conversion overview",
    description: "Track signups and event mix",
    is_public: false,
  });
  const [widgetForm, setWidgetForm] = useState({
    title: "Daily signups",
    type: "line" as Widget["type"],
    event_name: "signup_completed",
  });
  const [rangeHours, setRangeHours] = useState(168);
  const [loading, setLoading] = useState(true);

  const selectedDashboard = useMemo(
    () => dashboards.find((dashboard) => dashboard.id === selectedId) ?? null,
    [dashboards, selectedId],
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
        const [nextDashboards, nextTemplates] = await Promise.all([
          apiRequest<Dashboard[]>("/dashboards", {}, stored),
          apiRequest<DashboardTemplate[]>("/dashboards/templates", {}, stored),
        ]);
        setDashboards(nextDashboards);
        setTemplates(nextTemplates);
        const firstId = nextDashboards[0]?.id ?? null;
        setSelectedId(firstId);
        if (firstId) {
          const data = await apiRequest<WidgetData[]>(`/dashboards/${firstId}/data?hours=${rangeHours}`, {}, stored);
          setWidgetData(data);
        }
      } catch (error) {
        setNotice({ tone: "error", text: (error as Error).message });
      } finally {
        setLoading(false);
      }
    }

    void load();
  }, [router]);

  useEffect(() => {
    if (!token || !selectedId || !selectedDashboard) {
      return;
    }
    const intervalMs = Math.max((selectedDashboard.refresh_interval_seconds || 60) * 1000, 30_000);
    const timer = window.setInterval(() => {
      void loadWidgetData(selectedId, token, rangeHours);
    }, intervalMs);
    return () => window.clearInterval(timer);
  }, [token, selectedId, selectedDashboard, rangeHours]);

  async function refreshDashboards(currentToken = token) {
    if (!currentToken) {
      return;
    }
    const nextDashboards = await apiRequest<Dashboard[]>("/dashboards", {}, currentToken);
    setDashboards(nextDashboards);
    if (!selectedId && nextDashboards[0]) {
      setSelectedId(nextDashboards[0].id);
    }
  }

  async function loadWidgetData(dashboardId: number, currentToken = token, hours = rangeHours) {
    if (!currentToken) {
      return;
    }
    const data = await apiRequest<WidgetData[]>(`/dashboards/${dashboardId}/data?hours=${hours}`, {}, currentToken);
    setWidgetData(data);
  }

  async function createDashboard() {
    if (!token) {
      return;
    }
    const created = await apiRequest<Dashboard>(
      "/dashboards",
      {
        method: "POST",
        body: JSON.stringify({
          ...dashboardForm,
          refresh_interval_seconds: 60,
        }),
      },
      token,
    );
    await refreshDashboards(token);
    setSelectedId(created.id);
    await loadWidgetData(created.id, token);
    setNotice({ tone: "success", text: `Dashboard "${created.name}" created.` });
  }

  async function createFromTemplate(slug: string) {
    if (!token) {
      return;
    }
    const created = await apiRequest<Dashboard>(`/dashboards/templates/${slug}`, { method: "POST" }, token);
    await refreshDashboards(token);
    setSelectedId(created.id);
    await loadWidgetData(created.id, token);
    setNotice({ tone: "success", text: `Dashboard template "${created.name}" provisioned.` });
  }

  async function updateDashboard(patch: Partial<Dashboard>) {
    if (!token || !selectedDashboard) {
      return;
    }
    const updated = await apiRequest<Dashboard>(`/dashboards/${selectedDashboard.id}`, {
      method: "PATCH",
      body: JSON.stringify(patch),
    }, token);
    setDashboards((current) => current.map((item) => (item.id === updated.id ? updated : item)));
    setNotice({ tone: "success", text: `Dashboard "${updated.name}" updated.` });
  }

  async function createWidget() {
    if (!token || !selectedDashboard) {
      return;
    }
    const widget = await apiRequest<Widget>(
      `/dashboards/${selectedDashboard.id}/widgets`,
      {
        method: "POST",
        body: JSON.stringify({
          title: widgetForm.title,
          type: widgetForm.type,
          position: selectedDashboard.widgets.length,
          configuration: {
            event_name: widgetForm.event_name,
            bucket: widgetForm.type === "bar" ? "hour" : "day",
          },
        }),
      },
      token,
    );
    setDashboards((current) =>
      current.map((dashboard) =>
        dashboard.id === selectedDashboard.id ? { ...dashboard, widgets: [...dashboard.widgets, widget] } : dashboard,
      ),
    );
    await loadWidgetData(selectedDashboard.id, token);
    setNotice({ tone: "success", text: `Widget "${widget.title}" added.` });
  }

  if (loading) {
    return <div className="p-8 text-sm text-stone-500">Loading dashboards...</div>;
  }

  return (
    <div className="space-y-8 p-6 lg:p-10">
      <section className="rounded-[2rem] border border-stone-200 bg-white p-6 shadow-sm">
        <p className="text-xs uppercase tracking-[0.28em] text-orange-500">Dashboards</p>
        <h2 className="mt-2 text-3xl font-semibold text-stone-950">Saved queries and reporting surfaces</h2>
        <p className="mt-2 max-w-3xl text-sm leading-6 text-stone-600">
          Build dashboards from scratch or apply templates, then attach widgets that query event volume over configurable time ranges.
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

      <section className="grid gap-6 xl:grid-cols-[0.9fr_1.1fr]">
        <div className="space-y-6">
          <div className="rounded-[2rem] border border-stone-200 bg-white p-6 shadow-sm">
            <p className="text-xs uppercase tracking-[0.24em] text-stone-500">New dashboard</p>
            <div className="mt-4 space-y-3">
              <input
                className="w-full rounded-2xl border border-stone-200 px-4 py-3"
                value={dashboardForm.name}
                onChange={(event) => setDashboardForm({ ...dashboardForm, name: event.target.value })}
              />
              <input
                className="w-full rounded-2xl border border-stone-200 px-4 py-3"
                value={dashboardForm.description}
                onChange={(event) => setDashboardForm({ ...dashboardForm, description: event.target.value })}
              />
              <label className="flex items-center gap-3 text-sm text-stone-700">
                <input
                  type="checkbox"
                  checked={dashboardForm.is_public}
                  onChange={(event) => setDashboardForm({ ...dashboardForm, is_public: event.target.checked })}
                />
                Public read-only link
              </label>
              <button className="rounded-2xl bg-stone-950 px-4 py-3 text-sm font-semibold text-white" onClick={createDashboard}>
                Create blank dashboard
              </button>
            </div>
          </div>

          <div className="rounded-[2rem] border border-stone-200 bg-white p-6 shadow-sm">
            <p className="text-xs uppercase tracking-[0.24em] text-stone-500">Templates</p>
            <div className="mt-4 space-y-3">
              {templates.map((template) => (
                <div key={template.slug} className="rounded-2xl border border-stone-200 bg-stone-50 p-4">
                  <p className="font-semibold text-stone-950">{template.name}</p>
                  <p className="mt-1 text-sm text-stone-600">{template.description}</p>
                  <button
                    className="mt-4 rounded-2xl bg-orange-500 px-4 py-2 text-sm font-semibold text-white"
                    onClick={() => createFromTemplate(template.slug)}
                  >
                    Use template
                  </button>
                </div>
              ))}
            </div>
          </div>

          <div className="rounded-[2rem] border border-stone-200 bg-white p-6 shadow-sm">
            <p className="text-xs uppercase tracking-[0.24em] text-stone-500">Dashboards</p>
            <div className="mt-4 space-y-3">
              {dashboards.map((dashboard) => (
                <button
                  key={dashboard.id}
                  className={`w-full rounded-2xl border p-4 text-left ${
                    dashboard.id === selectedId ? "border-stone-950 bg-stone-950 text-white" : "border-stone-200 bg-stone-50 text-stone-900"
                  }`}
                  onClick={async () => {
                    setSelectedId(dashboard.id);
                    await loadWidgetData(dashboard.id, token);
                  }}
                >
                  <p className="font-semibold">{dashboard.name}</p>
                  <p className={`mt-1 text-xs ${dashboard.id === selectedId ? "text-stone-300" : "text-stone-500"}`}>
                    {dashboard.is_public ? "Public" : "Team-only"} · {dashboard.widgets.length} widgets
                  </p>
                </button>
              ))}
            </div>
          </div>
        </div>

        <div className="space-y-6">
          <div className="rounded-[2rem] border border-stone-200 bg-white p-6 shadow-sm">
            <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
              <div>
                <p className="text-xs uppercase tracking-[0.24em] text-stone-500">Selected dashboard</p>
                <h3 className="mt-1 text-xl font-semibold text-stone-950">
                  {selectedDashboard?.name ?? "Choose a dashboard"}
                </h3>
              </div>
              <div className="flex items-center gap-3">
                <select
                  className="rounded-2xl border border-stone-200 px-4 py-3 text-sm"
                  value={rangeHours}
                  onChange={async (event) => {
                    const hours = Number(event.target.value);
                    setRangeHours(hours);
                    if (selectedId) {
                      await loadWidgetData(selectedId, token, hours);
                    }
                  }}
                >
                  <option value={24}>24 hours</option>
                  <option value={168}>7 days</option>
                  <option value={720}>30 days</option>
                </select>
                {selectedDashboard ? (
                  <button
                    className="rounded-2xl border border-stone-300 px-4 py-3 text-sm"
                    onClick={() => updateDashboard({ is_public: !selectedDashboard.is_public })}
                  >
                    {selectedDashboard.is_public ? "Make private" : "Make public"}
                  </button>
                ) : null}
              </div>
            </div>

            {selectedDashboard ? (
              <div className="mt-5 space-y-4">
                <div className="rounded-2xl border border-stone-200 bg-stone-50 p-4 text-sm text-stone-700">
                  <p>{selectedDashboard.description || "No description provided."}</p>
                  <p className="mono mt-2 text-xs text-stone-500">
                    Public URL:{" "}
                    {selectedDashboard.is_public
                      ? `${getApiBase().replace("/api/v1", "")}/api/v1/dashboards/public/${selectedDashboard.id}`
                      : "disabled"}
                  </p>
                </div>

                <div className="grid gap-3 md:grid-cols-[1fr_160px_1fr_auto]">
                  <input
                    className="rounded-2xl border border-stone-200 px-4 py-3"
                    value={widgetForm.title}
                    onChange={(event) => setWidgetForm({ ...widgetForm, title: event.target.value })}
                  />
                  <select
                    className="rounded-2xl border border-stone-200 px-4 py-3"
                    value={widgetForm.type}
                    onChange={(event) => setWidgetForm({ ...widgetForm, type: event.target.value as Widget["type"] })}
                  >
                    <option value="line">Line</option>
                    <option value="bar">Bar</option>
                    <option value="pie">Pie</option>
                    <option value="kpi">KPI</option>
                    <option value="table">Table</option>
                  </select>
                  <input
                    className="rounded-2xl border border-stone-200 px-4 py-3"
                    value={widgetForm.event_name}
                    onChange={(event) => setWidgetForm({ ...widgetForm, event_name: event.target.value })}
                  />
                  <button className="rounded-2xl bg-orange-500 px-4 py-3 text-sm font-semibold text-white" onClick={createWidget}>
                    Add widget
                  </button>
                </div>
              </div>
            ) : (
              <div className="mt-5 rounded-2xl border border-dashed border-stone-300 p-5 text-sm text-stone-600">
                Create or select a dashboard to configure widgets.
              </div>
            )}
          </div>

          <div className="grid gap-4 md:grid-cols-2">
            {widgetData.length > 0 ? (
              widgetData.map((widget) => (
                <article key={widget.widget_id} className="rounded-[2rem] border border-stone-200 bg-white p-5 shadow-sm">
                  <p className="text-xs uppercase tracking-[0.24em] text-stone-500">{widget.widget_type}</p>
                  <h4 className="mt-1 text-lg font-semibold text-stone-950">{widget.title}</h4>
                  <div className="mt-4 h-64">
                    <WidgetPanel widget={widget} />
                  </div>
                </article>
              ))
            ) : (
              <div className="rounded-[2rem] border border-dashed border-stone-300 bg-white p-6 text-sm text-stone-600 md:col-span-2">
                {selectedDashboard
                  ? "No widget data yet. Add widgets that match ingested event names or expand the time range."
                  : "Choose a dashboard to preview widgets and data."}
              </div>
            )}
          </div>
        </div>
      </section>
    </div>
  );
}
