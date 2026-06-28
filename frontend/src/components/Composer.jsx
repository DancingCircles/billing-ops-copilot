import { ArrowUp, Paperclip } from "lucide-react";
import { useEffect, useRef, useState } from "react";

export function Composer({ disabled = false, onSend }) {
  const [value, setValue] = useState("");
  const inputRef = useRef(null);

  useEffect(() => {
    focusInput();
  }, [disabled]);

  function focusInput() {
    const input = inputRef.current;
    if (!input) return;

    input.focus({ preventScroll: true });
    window.requestAnimationFrame?.(() => inputRef.current?.focus({ preventScroll: true }));
  }

  function submit() {
    if (!value.trim() || disabled) return;
    onSend(value);
    setValue("");
    focusInput();
  }

  return (
    <form
      className="composer"
      onSubmit={(event) => {
        event.preventDefault();
        submit();
      }}
    >
      <button className="attach-button" type="button" aria-label="Attach file">
        <Paperclip size={23} strokeWidth={1.65} />
      </button>
      <input
        aria-label="Message AI Agent"
        ref={inputRef}
        placeholder="Message AI Agent..."
        value={value}
        onChange={(event) => setValue(event.target.value)}
      />
      <button className="send-button" type="submit" aria-label="Send message" disabled={disabled || !value.trim()}>
        <ArrowUp size={25} strokeWidth={1.75} />
      </button>
    </form>
  );
}
