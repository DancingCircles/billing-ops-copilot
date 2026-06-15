import { Copy, ThumbsDown, ThumbsUp } from "lucide-react";
import { useState } from "react";
import aiAvatar from "../assets/images/ai-avatar-collage.png";

export function MessageBubble({ message }) {
  const [reaction, setReaction] = useState(null);
  const [copied, setCopied] = useState(false);

  async function copyMessage() {
    await navigator.clipboard?.writeText(message.body);
    setCopied(true);
    window.setTimeout(() => setCopied(false), 1200);
  }

  if (message.role === "user") {
    return (
      <article className="message-row user-message">
        <div className="message-card user-card">{message.body}</div>
        <span className="message-orb" aria-hidden="true" />
      </article>
    );
  }

  if (message.pending) {
    return (
      <article className="message-row assistant-message pending-message">
        <span className="assistant-avatar" aria-hidden="true">
          <img src={aiAvatar} alt="" />
        </span>
        <ThinkingBloom label={message.body} />
      </article>
    );
  }

  return (
    <article className="message-row assistant-message">
      <span className="assistant-avatar" aria-hidden="true">
        <img src={aiAvatar} alt="" />
      </span>
      <div>
        <div className="message-card assistant-card">
          <MessageContent body={message.body} />
        </div>
        <div className="message-actions" aria-label="Message actions">
          <button
            className={copied ? "is-active" : ""}
            type="button"
            aria-label={copied ? "Copied response" : "Copy response"}
            onClick={copyMessage}
          >
            <Copy size={18} strokeWidth={1.55} />
          </button>
          <button
            className={reaction === "up" ? "is-active" : ""}
            type="button"
            aria-label="Like response"
            onClick={() => setReaction(reaction === "up" ? null : "up")}
          >
            <ThumbsUp size={18} strokeWidth={1.55} />
          </button>
          <button
            className={reaction === "down" ? "is-active" : ""}
            type="button"
            aria-label="Dislike response"
            onClick={() => setReaction(reaction === "down" ? null : "down")}
          >
            <ThumbsDown size={18} strokeWidth={1.55} />
          </button>
        </div>
      </div>
    </article>
  );
}

function ThinkingBloom({ label }) {
  const petals = ["0deg", "72deg", "144deg", "216deg", "288deg"];

  return (
    <div className="inline-loading" aria-label={label || "Generating response"}>
      <span className="thinking-bloom" aria-hidden="true">
        <span className="bloom-mark">
          {petals.map((angle, index) => (
            <span
              className="bloom-petal"
              key={angle}
              style={{
                "--angle": angle,
                "--delay": `${index * 92}ms`,
              }}
            />
          ))}
          <span className="bloom-core" />
        </span>
      </span>
    </div>
  );
}

function MessageContent({ body }) {
  return <div className="message-body">{renderBlocks(body)}</div>;
}

function renderBlocks(body) {
  const lines = String(body || "").replace(/\r\n/g, "\n").split("\n");
  const blocks = [];
  let index = 0;

  while (index < lines.length) {
    const line = lines[index];
    if (!line.trim()) {
      index += 1;
      continue;
    }

    if (line.trim().startsWith("```")) {
      const codeLines = [];
      index += 1;
      while (index < lines.length && !lines[index].trim().startsWith("```")) {
        codeLines.push(lines[index]);
        index += 1;
      }
      index += 1;
      blocks.push(
        <pre className="message-code" key={`code-${index}`}>
          <code>{codeLines.join("\n")}</code>
        </pre>,
      );
      continue;
    }

    if (isTableStart(lines, index)) {
      const tableLines = [];
      while (index < lines.length && isTableLine(lines[index])) {
        tableLines.push(lines[index]);
        index += 1;
      }
      blocks.push(<MessageTable key={`table-${index}`} lines={tableLines} />);
      continue;
    }

    if (/^#{1,3}\s+/.test(line.trim())) {
      const level = line.trim().match(/^#+/)?.[0].length ?? 2;
      const text = line.trim().replace(/^#{1,3}\s+/, "");
      const Heading = level === 1 ? "h2" : "h3";
      blocks.push(<Heading key={`heading-${index}`}>{renderInline(text)}</Heading>);
      index += 1;
      continue;
    }

    if (/^\s*[-*]\s+/.test(line)) {
      const items = [];
      while (index < lines.length && /^\s*[-*]\s+/.test(lines[index])) {
        items.push(lines[index].replace(/^\s*[-*]\s+/, ""));
        index += 1;
      }
      blocks.push(
        <ul key={`ul-${index}`}>
          {items.map((item, itemIndex) => (
            <li key={`${item}-${itemIndex}`}>{renderInline(item)}</li>
          ))}
        </ul>,
      );
      continue;
    }

    if (/^\s*\d+\.\s+/.test(line)) {
      const items = [];
      while (index < lines.length && /^\s*\d+\.\s+/.test(lines[index])) {
        items.push(lines[index].replace(/^\s*\d+\.\s+/, ""));
        index += 1;
      }
      blocks.push(
        <ol key={`ol-${index}`}>
          {items.map((item, itemIndex) => (
            <li key={`${item}-${itemIndex}`}>{renderInline(item)}</li>
          ))}
        </ol>,
      );
      continue;
    }

    const paragraph = [line.trim()];
    index += 1;
    while (
      index < lines.length &&
      lines[index].trim() &&
      !isTableStart(lines, index) &&
      !/^#{1,3}\s+/.test(lines[index].trim()) &&
      !/^\s*[-*]\s+/.test(lines[index]) &&
      !/^\s*\d+\.\s+/.test(lines[index]) &&
      !lines[index].trim().startsWith("```")
    ) {
      paragraph.push(lines[index].trim());
      index += 1;
    }
    blocks.push(<p key={`p-${index}`}>{renderInline(paragraph.join(" "))}</p>);
  }

  return blocks.length ? blocks : <p>{body}</p>;
}

function MessageTable({ lines }) {
  const rows = lines
    .filter((line, index) => index !== 1 || !isSeparatorRow(line))
    .map(splitTableRow)
    .filter((row) => row.length > 0);
  const [head = [], ...bodyRows] = rows;

  return (
    <div className="message-table-wrap">
      <table>
        <thead>
          <tr>
            {head.map((cell, index) => (
              <th key={`${cell}-${index}`}>{renderInline(cell)}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {bodyRows.map((row, rowIndex) => (
            <tr key={`row-${rowIndex}`}>
              {row.map((cell, cellIndex) => (
                <td key={`${cell}-${cellIndex}`}>{renderInline(cell)}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function renderInline(text) {
  const parts = String(text).split(/(`[^`]+`|\*\*[^*]+\*\*)/g).filter(Boolean);
  return parts.map((part, index) => {
    if (part.startsWith("`") && part.endsWith("`")) {
      return <code key={`${part}-${index}`}>{part.slice(1, -1)}</code>;
    }
    if (part.startsWith("**") && part.endsWith("**")) {
      return <strong key={`${part}-${index}`}>{part.slice(2, -2)}</strong>;
    }
    return part;
  });
}

function isTableStart(lines, index) {
  return isTableLine(lines[index]) && isSeparatorRow(lines[index + 1] || "");
}

function isTableLine(line) {
  return /^\s*\|.*\|\s*$/.test(line);
}

function isSeparatorRow(line) {
  return /^\s*\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)+\|?\s*$/.test(line);
}

function splitTableRow(line) {
  return line
    .trim()
    .replace(/^\|/, "")
    .replace(/\|$/, "")
    .split("|")
    .map((cell) => cell.trim());
}
