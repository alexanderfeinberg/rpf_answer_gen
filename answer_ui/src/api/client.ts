export type ApiBases = {
  docApiBase: string;
  answerApiBase: string;
};

export function getApiBases(): ApiBases {
  // Single-port mode: both document and answer APIs resolve to the same base.
  const port =
    (import.meta.env.VITE_DOCUMENT_API_PORT as string | undefined) ||
    (import.meta.env.DOCUMENT_API_PORT as string | undefined) ||
    (import.meta.env.VITE_DOC_API_PORT as string | undefined) ||
    (import.meta.env.VITE_ANSWER_API_PORT as string | undefined) ||
    (import.meta.env.ANSWER_API_PORT as string | undefined) ||
    "9001";

  const base = (import.meta.env.VITE_DOC_API_BASE as string | undefined) ||
    (import.meta.env.VITE_ANSWER_API_BASE as string | undefined) ||
    `http://localhost:${port}`;

  return {
    docApiBase: base,
    answerApiBase: base,
  };
}

async function readErrorBody(resp: Response): Promise<string> {
  // Normalize backend errors so UI alerts can show useful messages.
  const contentType = resp.headers.get("content-type") || "";
  try {
    if (contentType.includes("application/json")) {
      const data = (await resp.json()) as { error?: string; detail?: string };
      return data.error || data.detail || JSON.stringify(data);
    }
    return await resp.text();
  } catch {
    return `${resp.status} ${resp.statusText}`;
  }
}

export async function getJson<T>(url: string): Promise<T> {
  const resp = await fetch(url, { method: "GET" });
  if (!resp.ok) throw new Error(await readErrorBody(resp));
  return (await resp.json()) as T;
}

export async function postForm<T>(url: string, form: FormData): Promise<T> {
  const resp = await fetch(url, { method: "POST", body: form });
  if (!resp.ok) throw new Error(await readErrorBody(resp));
  return (await resp.json()) as T;
}

export async function postJson<T>(url: string, body: unknown): Promise<T> {
  // Shared JSON POST helper for answer generation endpoints.
  const resp = await fetch(url, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!resp.ok) throw new Error(await readErrorBody(resp));
  return (await resp.json()) as T;
}
