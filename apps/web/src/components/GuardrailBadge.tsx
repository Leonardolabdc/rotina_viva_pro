import { GuardrailVerdict } from "@/lib/api";

function engineLabel(engine: string | undefined): string {
  switch (engine) {
    case "llm-guard":
      return "LLM Guard (ML)";
    case "hybrid":
      return "LLM Guard + regras";
    case "rule-based":
      return "Guardrails (regras)";
    default:
      return engine || "Guardrails";
  }
}

function formatRisk(score: number | undefined): string | null {
  if (score === undefined || score === null || Number.isNaN(score)) return null;
  return `${Math.round(score * 100)}%`;
}

function topScores(audit: GuardrailVerdict["audit"], limit = 2): string[] {
  const scores = audit?.scores;
  if (!scores || typeof scores !== "object") return [];
  return Object.entries(scores)
    .sort((a, b) => b[1] - a[1])
    .slice(0, limit)
    .map(([name, val]) => `${name} ${Math.round(val * 100)}%`);
}

interface GuardrailBadgeProps {
  guardrail: GuardrailVerdict;
  variant?: "message" | "blocked";
}

export function GuardrailBadge({ guardrail, variant = "message" }: GuardrailBadgeProps) {
  const engine = guardrail.engine;
  const isMl = engine === "llm-guard" || engine === "hybrid";
  const risk = formatRisk(guardrail.riskScore);
  const scores = topScores(guardrail.audit);

  if (variant === "blocked") {
    return (
      <div className="mt-2 rounded-lg border border-amber-500/40 bg-amber-500/10 px-3 py-2 text-xs text-amber-900 dark:text-amber-100">
        <p className="font-semibold">
          Bloqueado · {engineLabel(engine)}
          {guardrail.scanner ? ` · ${guardrail.scanner}` : ""}
        </p>
        {guardrail.message ? <p className="mt-1 opacity-90">{guardrail.message}</p> : null}
      </div>
    );
  }

  return (
    <div
      className={`mt-2 flex flex-wrap items-center gap-1.5 text-[11px] leading-tight ${
        isMl ? "text-emerald-700 dark:text-emerald-300" : "text-muted"
      }`}
    >
      <span
        className={`inline-flex items-center gap-1 rounded-full border px-2 py-0.5 font-medium ${
          isMl
            ? "border-emerald-500/40 bg-emerald-500/10"
            : "border-border bg-surface-muted"
        }`}
      >
        {isMl ? "🛡" : "✓"} {engineLabel(engine)}
      </span>
      {risk ? (
        <span className="rounded-full border border-border px-2 py-0.5 text-muted">
          risco {risk}
        </span>
      ) : null}
      {scores.map((s) => (
        <span key={s} className="rounded-full border border-border px-2 py-0.5 text-muted">
          {s}
        </span>
      ))}
      {guardrail.stage ? (
        <span className="text-muted/80">· {guardrail.stage === "input" ? "entrada" : "saída"}</span>
      ) : null}
    </div>
  );
}

interface LlmGuardStatusBannerProps {
  active: boolean;
  inputScanners?: string[];
  outputScanners?: string[];
}

export function LlmGuardStatusBanner({
  active,
  inputScanners = [],
  outputScanners = [],
}: LlmGuardStatusBannerProps) {
  if (!active) return null;

  const scanners = [...new Set([...inputScanners, ...outputScanners])].filter(Boolean);

  return (
    <div className="border-b border-emerald-500/30 bg-emerald-500/10 px-4 py-2 text-center text-xs text-emerald-800 dark:text-emerald-200">
      <span className="font-semibold">LLM Guard activo</span>
      {scanners.length ? (
        <span className="text-emerald-700/90 dark:text-emerald-300/90">
          {" "}
          · scanners: {scanners.join(", ")}
        </span>
      ) : null}
      <span className="block text-[10px] opacity-80">
        Cada resposta mostra o motor de segurança abaixo da mensagem
      </span>
    </div>
  );
}
