export type User = {
  id: number;
  email: string;
  role: string;
  organization_id: number;
  is_active: boolean;
  created_at: string;
};

export type Organization = {
  id: number;
  name: string;
  slug: string;
  created_at: string;
};

export type ApiKey = {
  id: number;
  name: string;
  prefix: string;
  revoked_at: string | null;
  last_used_at: string | null;
  created_at: string;
  secret?: string;
};

export type Invitation = {
  id: number;
  email: string;
  role: string;
  invite_link: string;
  expires_at: string;
  accepted_at: string | null;
};

export type Widget = {
  id: number;
  dashboard_id: number;
  type: "line" | "bar" | "pie" | "kpi" | "table";
  title: string;
  position: number;
  configuration: Record<string, unknown>;
  created_at: string;
};

export type Dashboard = {
  id: number;
  name: string;
  description: string | null;
  is_public: boolean;
  refresh_interval_seconds: number;
  organization_id: number;
  created_at: string;
  widgets: Widget[];
};

export type WidgetData = {
  widget_id: number;
  widget_type: Widget["type"];
  title: string;
  data: Array<Record<string, string | number>>;
};

export type EventRecord = {
  id: number;
  event_name: string;
  timestamp: string;
  user_id: string;
  source: string;
  organization_id: number;
  created_at: string;
  properties: Record<string, unknown>;
};

export type Alert = {
  id: number;
  organization_id: number;
  name: string;
  event_name: string;
  threshold: number;
  window_minutes: number;
  status: "active" | "triggered" | "resolved" | "muted";
  muted_until: string | null;
  webhook_url: string | null;
  notify_email: string | null;
  created_at: string;
};

export type Notification = {
  id: number;
  organization_id: number;
  user_id: number | null;
  title: string;
  message: string;
  read: boolean;
  alert_id: number | null;
  created_at: string;
};

export type DashboardTemplate = {
  slug: string;
  name: string;
  description: string;
  widgets: Array<{
    title: string;
    type: Widget["type"];
    configuration: Record<string, unknown>;
  }>;
};
