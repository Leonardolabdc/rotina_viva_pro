"use client";

import { useRouter } from "next/navigation";
import { useEffect } from "react";

import { LoginForm } from "@/components/LoginForm";
import { useAuth } from "@/lib/auth-context";

export default function LoginPage() {
  const { token, loading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!loading && token) {
      router.replace("/chat");
    }
  }, [loading, token, router]);

  if (loading) {
    return (
      <div className="flex min-h-dvh items-center justify-center text-sm text-muted">
        A carregar…
      </div>
    );
  }

  return (
    <div className="flex min-h-dvh flex-col items-center justify-center px-4 py-10">
      <div className="mb-8 text-center">
        <h1 className="text-3xl font-bold text-primary">Rotina Viva</h1>
        <p className="mt-2 text-sm text-muted">Comunicação escolar com assistente IA</p>
      </div>
      <LoginForm />
    </div>
  );
}
