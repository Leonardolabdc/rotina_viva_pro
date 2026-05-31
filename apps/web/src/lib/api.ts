/** Base da API: local directo; na Vercel (ou qualquer host público) usa proxy same-origin. */
export function getApiBase(): string {
  if (typeof window !== "undefined") {
    const host = window.location.hostname;
    if (host !== "localhost" && host !== "127.0.0.1") {
      return "/api-proxy";
    }
  }
  if (process.env.NEXT_PUBLIC_VERCEL === "1" || process.env.VERCEL === "1") {
    return "/api-proxy";
  }
  return (
    process.env.NEXT_PUBLIC_ROTINA_API_URL?.replace(/\/$/, "") || "http://127.0.0.1:8000"
  );
}

/** @deprecated use getApiBase() — valor fixo no load do módulo falha na Vercel sem env explícita */
export const API_BASE = getApiBase();

export const TOKEN_KEY = "rotina_access_token";

export type RotinaRole = "gestao" | "educador" | "familia";

export interface UserProfile {
  username: string;
  role: RotinaRole;
  displayName: string;
  studentId?: number | null;
  allowMutations?: boolean;
}

export interface AuthSession {
  accessToken: string;
  expiresAt?: string | null;
  user: UserProfile;
}

export interface ChatMessage {
  role: "user" | "assistant" | "system";
  content: string;
  createdAt?: string;
  guardrail?: GuardrailVerdict | null;
}

export interface ChatSession {
  id: string;
  messages: ChatMessage[];
  dataSourceMode?: string;
  crewAiEnabled?: boolean;
  predictiveMlEnabled?: boolean;
}

export interface GuardrailVerdict {
  allowed: boolean;
  stage: "input" | "output";
  reason?: string;
  scanner?: string;
  riskScore?: number;
  engine?: string;
  message?: string;
  audit?: { scores?: Record<string, number> };
}

export interface LlmGuardHealth {
  enabled?: boolean;
  available?: boolean;
  active?: boolean;
  inputScanners?: string[];
  outputScanners?: string[];
}

export interface HealthResponse {
  status?: string;
  phase?: string;
  llmGuard?: LlmGuardHealth;
}

export interface ApiErrorBody {
  error?: string;
  message?: string;
  code?: number;
  stage?: string;
  used?: number;
  limit?: number;
  engine?: string;
  scanner?: string;
  riskScore?: number;
  allowed?: boolean;
}

export class ApiError extends Error {
  status: number;
  body: ApiErrorBody;

  constructor(status: number, body: ApiErrorBody, fallback = "Erro na API") {
    super(body.message || body.error || fallback);
    this.status = status;
    this.body = body;
  }
}

async function parseError(res: Response): Promise<ApiError> {
  let body: ApiErrorBody = {};
  try {
    const data = await res.json();
    if (typeof data === "object" && data !== null) {
      if ("detail" in data && typeof data.detail === "object" && data.detail) {
        body = data.detail as ApiErrorBody;
      } else {
        body = data as ApiErrorBody;
      }
    }
  } catch {
    body = { message: res.statusText };
  }
  return new ApiError(res.status, body);
}

export async function apiFetch<T>(
  path: string,
  options: RequestInit = {},
  token?: string | null,
): Promise<T> {
  const headers = new Headers(options.headers);
  if (!headers.has("Content-Type") && options.body) {
    headers.set("Content-Type", "application/json");
  }
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  const res = await fetch(`${getApiBase()}${path}`, { ...options, headers });
  if (!res.ok) {
    throw await parseError(res);
  }
  if (res.status === 204) {
    return undefined as T;
  }
  return (await res.json()) as T;
}

export async function login(username: string, password: string): Promise<AuthSession> {
  return apiFetch<AuthSession>("/auth/login", {
    method: "POST",
    body: JSON.stringify({ username, password }),
  });
}

export async function getCurrentUser(token: string): Promise<UserProfile> {
  return apiFetch<UserProfile>("/auth/me", {}, token);
}

export async function getHealth(): Promise<HealthResponse> {
  return apiFetch<HealthResponse>("/health");
}

export async function createChatSession(token: string): Promise<ChatSession> {
  return apiFetch<ChatSession>(
    "/chat/sessions",
    {
      method: "POST",
      body: JSON.stringify({ dataSourceMode: "auto", crewAiEnabled: false }),
    },
    token,
  );
}

export async function getChatSession(token: string, sessionId: string): Promise<ChatSession> {
  return apiFetch<ChatSession>(`/chat/sessions/${sessionId}`, {}, token);
}

export interface StreamHandlers {
  onStatus?: (phase: string, detail?: string) => void;
  onToken?: (text: string) => void;
  onDone?: (content: string, guardrail?: GuardrailVerdict | null) => void;
  onError?: (error: ApiError, guardrail?: GuardrailVerdict | null) => void;
}

function parseGuardrailFromPayload(data: Record<string, unknown>): GuardrailVerdict | null {
  const g = data.guardrail;
  if (!g || typeof g !== "object") return null;
  const o = g as Record<string, unknown>;
  return {
    allowed: Boolean(o.allowed ?? true),
    stage: (o.stage === "input" ? "input" : "output") as "input" | "output",
    reason: o.reason ? String(o.reason) : undefined,
    scanner: o.scanner ? String(o.scanner) : undefined,
    riskScore: typeof o.riskScore === "number" ? o.riskScore : undefined,
    engine: o.engine ? String(o.engine) : undefined,
    message: o.message ? String(o.message) : undefined,
    audit:
      o.audit && typeof o.audit === "object"
        ? (o.audit as GuardrailVerdict["audit"])
        : undefined,
  };
}

function guardrailFromErrorPayload(data: Record<string, unknown>): GuardrailVerdict | null {
  if (!data.engine && !data.scanner && data.allowed !== false) return null;
  return {
    allowed: false,
    stage: data.stage === "output" ? "output" : "input",
    scanner: data.scanner ? String(data.scanner) : undefined,
    riskScore: typeof data.riskScore === "number" ? data.riskScore : undefined,
    engine: data.engine ? String(data.engine) : undefined,
    message: data.message ? String(data.message) : undefined,
  };
}

export async function streamChatMessage(
  token: string,
  sessionId: string,
  content: string,
  handlers: StreamHandlers,
  signal?: AbortSignal,
): Promise<void> {
  const res = await fetch(`${getApiBase()}/chat/sessions/${sessionId}/messages/stream`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
      Accept: "text/event-stream",
    },
    body: JSON.stringify({ content, dataSourceMode: "auto" }),
    signal,
  });

  if (!res.ok) {
    throw await parseError(res);
  }
  if (!res.body) {
    throw new ApiError(502, { message: "Stream indisponível" });
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  const dispatch = (block: string) => {
    const lines = block.split("\n");
    let event = "message";
    let dataLine = "";
    for (const line of lines) {
      if (line.startsWith("event:")) {
        event = line.slice(6).trim();
      } else if (line.startsWith("data:")) {
        dataLine = line.slice(5).trim();
      }
    }
    if (!dataLine) return;

    let data: Record<string, unknown> = {};
    try {
      data = JSON.parse(dataLine) as Record<string, unknown>;
    } catch {
      return;
    }

    if (event === "status") {
      handlers.onStatus?.(String(data.phase || ""), data.detail ? String(data.detail) : undefined);
    } else if (event === "token") {
      handlers.onToken?.(String(data.text || ""));
    } else if (event === "done") {
      handlers.onDone?.(String(data.content || ""), parseGuardrailFromPayload(data));
    } else if (event === "error") {
      const body: ApiErrorBody = {
        message: String(data.message || "Erro no stream"),
        stage: data.stage ? String(data.stage) : undefined,
        used: typeof data.used === "number" ? data.used : undefined,
        limit: typeof data.limit === "number" ? data.limit : undefined,
        engine: data.engine ? String(data.engine) : undefined,
        scanner: data.scanner ? String(data.scanner) : undefined,
        riskScore: typeof data.riskScore === "number" ? data.riskScore : undefined,
        allowed: data.allowed === false ? false : undefined,
      };
      handlers.onError?.(
        new ApiError(Number(data.code) || 500, body),
        guardrailFromErrorPayload(data),
      );
    }
  };

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const parts = buffer.split("\n\n");
    buffer = parts.pop() || "";
    for (const part of parts) {
      if (part.trim()) dispatch(part);
    }
  }
  if (buffer.trim()) dispatch(buffer);
}

export function roleLabel(role: RotinaRole): string {
  switch (role) {
    case "gestao":
      return "Gestão";
    case "educador":
      return "Educador";
    case "familia":
      return "Família";
    default:
      return role;
  }
}

export function statusLabel(phase: string): string {
  switch (phase) {
    case "guardrails":
      return "A verificar segurança (LLM Guard)…";
    case "planning":
      return "A planear resposta…";
    case "sql":
      return "A consultar dados…";
    case "rag":
      return "A pesquisar documentos…";
    case "generating":
      return "A gerar resposta…";
    default:
      return phase ? `A processar (${phase})…` : "";
  }
}
