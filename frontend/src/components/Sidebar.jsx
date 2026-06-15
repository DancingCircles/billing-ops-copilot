import { ExternalLink, MessageSquare, X } from "lucide-react";
import logoPaint from "../assets/brand/aiagent-selected.svg";
import navPaint from "../assets/brand/nav-new-chat-selected.svg";
import { ConversationList } from "./ConversationList.jsx";

export function Sidebar({
  activeId,
  conversations,
  isOpen,
  user,
  onClose,
  onDelete,
  onNewChat,
  onRename,
  onSelect,
}) {
  return (
    <>
      <aside className={`sidebar ${isOpen ? "is-open" : ""}`}>
        <div className="sidebar-header">
          <a className="brand-mark" href="/" aria-label="AI Agent home">
            <img src={logoPaint} alt="" aria-hidden="true" />
            <span>AI AGENT</span>
          </a>
          <button className="icon-control desktop-only" type="button" aria-label="Open in new window">
            <ExternalLink size={21} strokeWidth={1.8} />
          </button>
          <button className="icon-control mobile-only" type="button" aria-label="Close menu" onClick={onClose}>
            <X size={22} strokeWidth={1.9} />
          </button>
        </div>

        <nav className="primary-nav" aria-label="Main navigation">
          <button
            className={`nav-item ${activeId === "new-chat" ? "is-selected" : ""}`}
            type="button"
            onClick={onNewChat}
          >
            <img src={navPaint} alt="" aria-hidden="true" />
            <MessageSquare size={21} strokeWidth={1.75} />
            <span>New Chat</span>
          </button>
        </nav>

        <ConversationList
          activeId={activeId}
          conversations={conversations}
          onDelete={onDelete}
          onRename={onRename}
          onSelect={onSelect}
        />

        <div className="profile-row">
          <span className="profile-dot" aria-hidden="true" />
          <div>
            <strong>{user.name}</strong>
            <span>{user.email}</span>
          </div>
        </div>
      </aside>
      <button
        className={`sidebar-scrim ${isOpen ? "is-open" : ""}`}
        type="button"
        aria-label="Close menu overlay"
        onClick={onClose}
      />
    </>
  );
}
