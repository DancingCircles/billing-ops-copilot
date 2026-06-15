import { Check, Pencil, Trash2, X } from "lucide-react";
import { useState } from "react";

export function ConversationList({ activeId, conversations, onDelete, onRename, onSelect }) {
  const [editingId, setEditingId] = useState(null);
  const [draftTitle, setDraftTitle] = useState("");
  const grouped = conversations.reduce((sections, item) => {
    sections[item.group] = sections[item.group] || [];
    sections[item.group].push(item);
    return sections;
  }, {});

  function startEditing(item) {
    setEditingId(item.id);
    setDraftTitle(item.title);
  }

  function cancelEditing() {
    setEditingId(null);
    setDraftTitle("");
  }

  function saveEditing(item) {
    const nextTitle = draftTitle.trim();
    if (nextTitle && nextTitle !== item.title) {
      onRename(item.id, nextTitle);
    }
    cancelEditing();
  }

  return (
    <div className="conversation-list">
      {Object.entries(grouped).map(([group, items]) => (
        <section className="conversation-group" key={group}>
          <h2>{group}</h2>
          {items.map((item) => (
            <div
              className={`conversation-item ${activeId === item.id ? "is-active" : ""}`}
              key={item.id}
            >
              {editingId === item.id ? (
                <form
                  className="conversation-edit-form"
                  onSubmit={(event) => {
                    event.preventDefault();
                    saveEditing(item);
                  }}
                >
                  <input
                    aria-label="Conversation title"
                    autoFocus
                    value={draftTitle}
                    onChange={(event) => setDraftTitle(event.target.value)}
                  />
                  <button type="submit" aria-label="Save title">
                    <Check size={17} strokeWidth={1.7} />
                  </button>
                  <button type="button" aria-label="Cancel title edit" onClick={cancelEditing}>
                    <X size={17} strokeWidth={1.7} />
                  </button>
                </form>
              ) : (
                <>
                  <button className="conversation-select" type="button" onClick={() => onSelect(item.id)}>
                    <span>{item.title}</span>
                  </button>
                  <div className="conversation-actions">
                    <button type="button" aria-label="Rename conversation" onClick={() => startEditing(item)}>
                      <Pencil size={16} strokeWidth={1.7} />
                    </button>
                    <button type="button" aria-label="Delete conversation" onClick={() => onDelete(item.id)}>
                      <Trash2 size={16} strokeWidth={1.7} />
                    </button>
                  </div>
                </>
              )}
            </div>
          ))}
        </section>
      ))}
    </div>
  );
}
