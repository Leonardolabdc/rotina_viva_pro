import { ChatMessage } from "@/lib/api";

interface MessageBubbleProps {
  message: ChatMessage;
}

export function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === "user";

  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
      <div
        className={`max-w-[85%] rounded-2xl px-4 py-3 text-sm leading-relaxed whitespace-pre-wrap ${
          isUser
            ? "rounded-br-md bg-primary text-white"
            : "rounded-bl-md border border-border bg-surface text-foreground"
        }`}
      >
        {message.content}
      </div>
    </div>
  );
}

interface StreamingBubbleProps {
  content: string;
}

export function StreamingBubble({ content }: StreamingBubbleProps) {
  return (
    <div className="flex justify-start">
      <div className="max-w-[85%] rounded-2xl rounded-bl-md border border-border bg-surface px-4 py-3 text-sm leading-relaxed whitespace-pre-wrap">
        {content}
        <span className="ml-1 inline-block h-4 w-1 animate-pulse-dot bg-primary align-middle" />
      </div>
    </div>
  );
}
