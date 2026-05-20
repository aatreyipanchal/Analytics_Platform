"use client";

export function getWsBase() {
  const explicit = process.env.NEXT_PUBLIC_WS_BASE_URL;
  if (explicit) {
    return explicit.replace(/\/$/, "");
  }
  const api = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api/v1";
  const origin = api.replace(/\/api\/v1\/?$/, "");
  return origin.replace(/^https:/, "wss:").replace(/^http:/, "ws:");
}

export function openOrgEventsSocket(accessToken: string, onMessage: (payload: unknown) => void) {
  const url = `${getWsBase()}/api/v1/realtime/events?token=${encodeURIComponent(accessToken)}`;
  const socket = new WebSocket(url);

  socket.onmessage = (event) => {
    try {
      onMessage(JSON.parse(event.data as string));
    } catch {
      onMessage(event.data);
    }
  };

  return socket;
}

export function openOrgAlertsSocket(accessToken: string, onMessage: (payload: unknown) => void) {
  const url = `${getWsBase()}/api/v1/realtime/alerts?token=${encodeURIComponent(accessToken)}`;
  const socket = new WebSocket(url);

  socket.onmessage = (event) => {
    try {
      onMessage(JSON.parse(event.data as string));
    } catch {
      onMessage(event.data);
    }
  };

  return socket;
}
