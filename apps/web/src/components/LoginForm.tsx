"use client";

import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";

import { ApiError } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";

export function LoginForm() {
  const { login } = useAuth();
  const router = useRouter();
  const [username, setUsername] = useState("gestao.demo");
  const [password, setPassword] = useState("demo123");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await login(username.trim(), password);
      router.replace("/chat");
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else if (err instanceof TypeError) {
        setError(
          "Não foi possível ligar à API. Em local: arranque .\\scripts\\start_api_dev.ps1. Na Vercel: confirme ROTINA_API_URL no projecto.",
        );
      } else {
        setError("Não foi possível entrar. Verifique se a API está a correr.");
      }
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form onSubmit={onSubmit} className="flex w-full max-w-md flex-col gap-4">
      <div>
        <label htmlFor="username" className="mb-1 block text-sm text-muted">
          Utilizador
        </label>
        <input
          id="username"
          name="username"
          autoComplete="username"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          className="w-full rounded-lg border border-border bg-surface px-3 py-2.5 text-foreground outline-none focus:border-primary"
          required
        />
      </div>
      <div>
        <label htmlFor="password" className="mb-1 block text-sm text-muted">
          Palavra-passe
        </label>
        <input
          id="password"
          name="password"
          type="password"
          autoComplete="current-password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          className="w-full rounded-lg border border-border bg-surface px-3 py-2.5 text-foreground outline-none focus:border-primary"
          required
        />
      </div>
      {error ? (
        <p className="rounded-lg border border-danger/40 bg-danger/10 px-3 py-2 text-sm text-danger">
          {error}
        </p>
      ) : null}
      <button
        type="submit"
        disabled={submitting}
        className="rounded-lg bg-primary px-4 py-2.5 font-medium text-white transition hover:bg-primary-hover disabled:opacity-60"
      >
        {submitting ? "A entrar…" : "Entrar"}
      </button>
      <p className="text-center text-xs text-muted">
        Demo: gestao.demo · professor.demo · pai.demo — palavra-passe demo123
      </p>
    </form>
  );
}
