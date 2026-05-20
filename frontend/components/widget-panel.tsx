"use client";

import {
  Bar,
  BarChart,
  Cell,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { WidgetData } from "@/lib/types";

const CHART_COLORS = ["#f97316", "#0f766e", "#1d4ed8", "#dc2626", "#7c3aed"];

export function WidgetPanel({ widget }: { widget: WidgetData }) {
  if (widget.widget_type === "kpi") {
    return (
      <div className="flex h-full items-center justify-center rounded-[1.5rem] bg-stone-950 text-white">
        <div className="text-center">
          <p className="text-xs uppercase tracking-[0.24em] text-stone-400">{String(widget.data[0]?.label ?? "Metric")}</p>
          <p className="mt-3 text-5xl font-semibold">{String(widget.data[0]?.value ?? 0)}</p>
        </div>
      </div>
    );
  }

  if (widget.widget_type === "line") {
    return (
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={widget.data}>
          <XAxis dataKey="label" hide />
          <YAxis allowDecimals={false} />
          <Tooltip />
          <Line type="monotone" dataKey="value" stroke="#f97316" strokeWidth={3} dot={false} />
        </LineChart>
      </ResponsiveContainer>
    );
  }

  if (widget.widget_type === "bar") {
    return (
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={widget.data}>
          <XAxis dataKey="label" hide />
          <YAxis allowDecimals={false} />
          <Tooltip />
          <Bar dataKey="value" fill="#0f766e" radius={[10, 10, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    );
  }

  if (widget.widget_type === "pie") {
    return (
      <ResponsiveContainer width="100%" height="100%">
        <PieChart>
          <Tooltip />
          <Pie data={widget.data} dataKey="value" nameKey="label" innerRadius={52} outerRadius={88} paddingAngle={3}>
            {widget.data.map((entry, index) => (
              <Cell key={`${entry.label}-${index}`} fill={CHART_COLORS[index % CHART_COLORS.length]} />
            ))}
          </Pie>
        </PieChart>
      </ResponsiveContainer>
    );
  }

  return (
    <div className="space-y-3 overflow-auto">
      {widget.data.map((row, index) => (
        <div key={index} className="rounded-2xl border border-stone-200 bg-white p-3 text-sm text-stone-700">
          {Object.entries(row).map(([key, value]) => (
            <div key={key} className="flex items-center justify-between gap-3">
              <span className="text-stone-500">{key}</span>
              <span className="mono text-xs">{String(value)}</span>
            </div>
          ))}
        </div>
      ))}
    </div>
  );
}
