const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "";

export class ApiError extends Error {
  constructor(message, { code = "UNKNOWN_ERROR", detail = {}, status = 0 } = {}) {
    super(message);
    this.name = "ApiError";
    this.code = code;
    this.detail = detail;
    this.status = status;
  }
}

export async function importDatabase(file) {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(`${API_BASE_URL}/api/databases/import`, {
    method: "POST",
    body: formData,
  });

  const body = await response.json().catch(() => null);
  if (!response.ok) {
    throw new ApiError(body?.message ?? "database import failed", {
      code: body?.code,
      detail: body?.detail,
      status: response.status,
    });
  }

  return body;
}
