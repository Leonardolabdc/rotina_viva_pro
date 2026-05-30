"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useRef, useState } from "react";

import { ChatInput } from "@/components/ChatInput";
import { MessageBubble, StreamingBubble } from "@/components/MessageBubble";
import {
  ApiError,
  ChatMessage,
  createChatSession,
  getChatSession,
  roleLabel,
  statusLabel,
  streamChatMessage,
} from "@/lib/api";
import { useAuth } from "@/lib/auth-context";

const SESSION_KEY = "rotina_chat_session_id";

export function ChatPage() {
  const { token, user, logout } = useAuth();
  const router = useRouter();
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [streaming, setStreaming] = useState("");
  const [status, setStatus] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [booting, setBooting] = useState(true);
  const bottomRef = useRef<HTMLDivElement>(null);
  const abortRef = useRef<AbortController | null>(null);

  useEffect(() => {
    if (!token) {
      router.replace("/login");
    }
  }, [token, router]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, streaming, status]);

  useEffect(() => {
    if (!token) return;

    const authToken = token;
    let cancelled = false;

    async function boot() {
      setBooting(true);
      setError(null);
      try {
        const stored = sessionStorage.getItem(SESSION_KEY);
        if (stored) {
          try {
            const session = await getChatSession(authToken, stored);
            if (!cancelled) {
              setSessionId(session.id);
              setMessages(session.messages || []);
              setBooting(false);
              return;
            }
          } catch {
            sessionStorage.removeItem(SESSION_KEY);
          }
        }
        const created = await createChatSession(authToken);
        if (!cancelled) {
          sessionStorage.setItem(SESSION_KEY, created.id);
          setSessionId(created.id);
          setMessages(created.messages || []);
        }
      } catch (err) {
        if (!cancelled) {
          setError(
            err instanceof ApiError
              ? err.message
              : "Não foi possível iniciar o chat. Confirme que a API está activa.",
          );
        }
      } finally {
        if (!cancelled) setBooting(false);
      }
    }

    boot();
    return () => {
      cancelled = true;
    };
  }, [token]);

  const handleSend = useCallback(
    async (content: string) => {
      if (!token || !sessionId || busy) return;

      setError(null);
      setBusy(true);
      setStreaming("");
      setStatus("A enviar…");

      const userMsg: ChatMessage = { role: "user", content };
      setMessages((prev) => [...prev, userMsg]);

      abortRef.current?.abort();
      const controller = new AbortController();
      abortRef.current = controller;

      let draft = "";

      try {
        await streamChatMessage(
          token,
          sessionId,
          content,
          {
            onStatus: (phase) => setStatus(statusLabel(phase)),
            onToken: (text) => {
              draft += text;
              setStreaming(draft);
              setStatus(null);
            },
            onDone: (finalContent) => {
              const assistant: ChatMessage = {
                role: "assistant",
                content: finalContent || draft,
              };
              setMessages((prev) => [...prev, assistant]);
              setStreaming("");
              setStatus(null);
            },
            onError: (streamErr) => {
              setError(streamErr.message);
              setStreaming("");
              setStatus(null);
            },
          },
          controller.signal,
        );
      } catch (err) {
        if ((err as Error).name === "AbortError") return;
        if (err instanceof ApiError) {
          setError(err.message);
        } else if (err instanceof Error && err.message) {
          setError(err.message);
        } else {
          setError("Falha ao comunicar com a API.");
        }
        setStreaming("");
        setStatus(null);
      } finally {
        setBusy(false);
      }
    },
    [token, sessionId, busy],
  );

  function handleNewSession() {
    sessionStorage.removeItem(SESSION_KEY);
    setSessionId(null);
    setMessages([]);
    setStreaming("");
    setStatus(null);
    setError(null);
    setBooting(true);
    if (token) {
      createChatSession(token)
        .then((s) => {
          sessionStorage.setItem(SESSION_KEY, s.id);
          setSessionId(s.id);
          setMessages(s.messages || []);
        })
        .catch((err) => {
          setError(err instanceof ApiError ? err.message : "Erro ao criar sessão.");
        })
        .finally(() => setBooting(false));
    }
  }

  if (!token || !user) {
    return null;
  }

  return (
    <div className="flex min-h-dvh flex-col">
      <header className="flex items-center justify-between border-b border-border bg-surface-muted px-4 py-3">
        <div>
          <Link href="/chat" className="text-lg font-semibold text-primary">
            Rotina Viva
          </Link>
          <p className="text-xs text-muted">
            {user.displayName} · {roleLabel(user.role)}
          </p>
        </div>
        <div className="flex gap-2">
          <button
            type="button"
            onClick={handleNewSession}
            className="rounded-lg border border-border px-3 py-1.5 text-xs hover:border-primary"
          >
            Nova sessão
          </button>
          <button
            type="button"
            onClick={() => {
              logout();
              router.replace("/login");
            }}
            className="rounded-lg border border-border px-3 py-1.5 text-xs hover:border-primary"
          >
            Sair
          </button>
        </div>
      </header>

      <main className="mx-auto flex w-full max-w-3xl flex-1 flex-col">
        {booting ? (
          <div className="flex flex-1 items-center justify-center text-sm text-muted">
            A preparar conversa…
          </div>
        ) : (
          <div className="flex flex-1 flex-col gap-3 overflow-y-auto px-4 py-6">
            {messages.length === 0 && !streaming ? (
              <div className="rounded-xl border border-dashed border-border bg-surface/50 p-6 text-center text-sm text-muted">
                Olá! Pergunte sobre alunos, rotina diária ou documentos da escola.
              </div>
            ) : null}
            {messages.map((m, i) => (
              <MessageBubble key={`${m.role}-${i}-${m.content.slice(0, 24)}`} message={m} />
            ))}
            {streaming ? <StreamingBubble content={streaming} /> : null}
            {status ? (
              <p className="text-center text-xs text-muted animate-pulse-dot">{status}</p>
            ) : null}
            {error ? (
              <p className="rounded-lg border border-danger/40 bg-danger/10 px-3 py-2 text-sm text-danger">
                {error}
              </p>
            ) : null}
            <div ref={bottomRef} />
          </div>
        )}
        <ChatInput disabled={booting || busy || !sessionId} onSend={handleSend} />
      </main>
    </div>
  );
}
