import { Menu } from "lucide-react";
import { useEffect, useRef } from "react";
import { Composer } from "./Composer.jsx";
import { DecorativeLayer } from "./DecorativeLayer.jsx";
import { MessageBubble } from "./MessageBubble.jsx";

export function ChatCanvas({
  isSending,
  messages,
  onMenuClick,
  onSend,
  statusText,
}) {
  const messageViewportRef = useRef(null);
  const hasMessages = messages.length > 0;

  useEffect(() => {
    const viewport = messageViewportRef.current;
    if (!viewport) return;
    viewport.scrollTo({
      top: viewport.scrollHeight,
      behavior: "smooth",
    });
  }, [isSending, messages]);

  return (
    <section className={`chat-canvas ${hasMessages ? "has-messages" : "is-empty"}`} aria-label="AI Agent chat">
      <button className="menu-button" type="button" onClick={onMenuClick}>
        <Menu size={26} strokeWidth={1.8} />
        <span>Menu</span>
      </button>
      <DecorativeLayer />

      {!hasMessages ? (
        <div className="prompt-heading">
          <h1>How can I help you today?</h1>
          <span className="lime-underline" aria-hidden="true" />
        </div>
      ) : null}

      {hasMessages ? (
        <div className="message-viewport" ref={messageViewportRef}>
          <div className="message-stack">
            {messages.map((message) => (
              <MessageBubble key={message.id} message={message} />
            ))}
            {isSending ? (
              <MessageBubble
                message={{
                  id: "assistant-pending",
                  role: "assistant",
                  body: statusText,
                  pending: true,
                }}
              />
            ) : null}
          </div>
        </div>
      ) : null}

      <Composer disabled={isSending} onSend={onSend} />
    </section>
  );
}
