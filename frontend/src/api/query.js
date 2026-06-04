import { ApiError } from "./databases";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "";

export async function runQuestion({ question, databaseId }) {
  const response = await fetch(`${API_BASE_URL}/api/query`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      question,
      database_id: databaseId,
    }),
  });

  const body = await response.json().catch(() => null);
  if (!response.ok) {
    throw new ApiError(body?.message ?? "query failed", {
      code: body?.code,
      detail: body?.detail,
      status: response.status,
    });
  }

  return body;
}

export function streamQuestion({ question, databaseId, onEvent, onError, onDone }) {
  const params = new URLSearchParams({
    question,
    database_id: databaseId,
  });
  const eventSource = new EventSource(`${API_BASE_URL}/api/query/stream?${params.toString()}`);

  for (const eventName of ["model_delta", "sql", "result", "error", "done"]) {
    eventSource.addEventListener(eventName, (event) => {
      let payload = {};
      try {
        payload = JSON.parse(event.data || "{}");
      } catch {
        eventSource.close();
        onError?.({ message: "stream payload parse failed" });
        return;
      }

      onEvent({ type: eventName, ...payload });
      if (eventName === "error") {
        eventSource.close();
        onError?.(payload);
      }
      if (eventName === "done") {
        eventSource.close();
        onDone?.();
      }
    });
  }

  eventSource.onerror = () => {
    eventSource.close();
    onError?.({ message: "stream connection failed" });
  };

  return () => eventSource.close();
}
