import { useEffect, useMemo, useState } from "react";
import {
  createCase,
  deleteCase,
  getCase,
  listCases,
  sendMessage,
  updateCaseTitle,
} from "./api/client.js";
import { ChatCanvas } from "./components/ChatCanvas.jsx";
import { Sidebar } from "./components/Sidebar.jsx";
import { user } from "./data/mockData.js";

export function App() {
  const [activeId, setActiveId] = useState("new-chat");
  const [conversations, setConversations] = useState([]);
  const [messages, setMessages] = useState([]);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [isSending, setIsSending] = useState(false);
  const [statusText, setStatusText] = useState("Ready");
  const [pendingCustomerId, setPendingCustomerId] = useState(null);
  const [verifiedCustomerId, setVerifiedCustomerId] = useState(null);

  const activeCase = useMemo(
    () => conversations.find((conversation) => conversation.id === activeId),
    [activeId, conversations],
  );

  useEffect(() => {
    refreshCases();
  }, []);

  useEffect(() => {
    if (activeId === "new-chat") {
      setVerifiedCustomerId(null);
      return;
    }
    if (activeCase) {
      setVerifiedCustomerId(activeCase.verified_customer_id ?? null);
    }
  }, [activeId, activeCase?.verified_customer_id]);

  async function refreshCases() {
    try {
      const cases = await listCases();
      setConversations(cases);
      setStatusText("Ready");
    } catch (error) {
      setStatusText(error.message);
    }
  }

  async function ensureActiveCase() {
    if (activeId !== "new-chat") {
      return activeId;
    }

    const created = await createCase("New billing case");
    setConversations((current) => [created, ...current]);
    setActiveId(created.id);
    setVerifiedCustomerId(created.verified_customer_id);
    return created.id;
  }

  async function handleSend(text) {
    const value = text.trim();
    if (!value) return;

    const userMessage = {
      id: crypto.randomUUID(),
      role: "user",
      body: value,
      created_at: new Date().toISOString(),
    };
    setPendingCustomerId(detectCustomerIdentifier(value, Boolean(verifiedCustomerId)));
    setMessages((current) => [
      ...current,
      userMessage,
    ]);

    setIsSending(true);
    setStatusText("Running billing agents...");
    try {
      const caseId = await ensureActiveCase();
      const response = await sendMessage(caseId, value);
      setMessages(response.case.messages);
      setVerifiedCustomerId(response.verified_customer_id ?? response.case.verified_customer_id);
      setPendingCustomerId(null);
      setConversations((current) => upsertCaseSummary(current, response.case));
      setStatusText(response.tools_used?.length ? `Used ${response.tools_used.join(", ")}` : "Ready");
    } catch (error) {
      setMessages((current) => [
        ...current,
        {
          id: crypto.randomUUID(),
          role: "assistant",
          body: error.message,
          created_at: new Date().toISOString(),
        },
      ]);
      setStatusText(error.message);
    } finally {
      setPendingCustomerId(null);
      setIsSending(false);
    }
  }

  function handleNewChat() {
    setActiveId("new-chat");
    setMessages([]);
    setPendingCustomerId(null);
    setVerifiedCustomerId(null);
    setStatusText("Ready");
  }

  async function handleSelect(id) {
    try {
      const selectedCase = await getCase(id);
      setActiveId(id);
      setMessages(selectedCase.messages);
      setPendingCustomerId(null);
      setVerifiedCustomerId(selectedCase.verified_customer_id);
      setConversations((current) => upsertCaseSummary(current, selectedCase));
      setSidebarOpen(false);
      setStatusText("Ready");
    } catch (error) {
      setStatusText(error.message);
    }
  }

  async function handleRename(id, title) {
    try {
      const updated = await updateCaseTitle(id, title);
      setConversations((current) => upsertCaseSummary(current, updated));
    } catch (error) {
      setStatusText(error.message);
    }
  }

  async function handleDelete(id) {
    try {
      await deleteCase(id);
      setConversations((current) => current.filter((conversation) => conversation.id !== id));
      if (activeId === id) {
        handleNewChat();
      }
    } catch (error) {
      setStatusText(error.message);
    }
  }

  return (
    <main className="app-shell">
      <Sidebar
        activeId={activeId}
        conversations={conversations}
        isOpen={sidebarOpen}
        user={user}
        onClose={() => setSidebarOpen(false)}
        onDelete={handleDelete}
        onNewChat={handleNewChat}
        onRename={handleRename}
        onSelect={handleSelect}
      />
      <ChatCanvas
        activeCase={activeCase}
        isSending={isSending}
        messages={messages}
        onMenuClick={() => setSidebarOpen(true)}
        onSend={handleSend}
        pendingCustomerId={pendingCustomerId}
        statusText={statusText}
        verifiedCustomerId={verifiedCustomerId}
      />
    </main>
  );
}

function detectCustomerIdentifier(message, hasVerifiedCustomer) {
  const explicitMatch = message.match(/\b(?:customer\s*id|customer|id)\s*(?:is|:|#)?\s*(\d+)\b/i);
  if (explicitMatch) return explicitMatch[1];

  const emailMatch = message.match(/[\w.+-]+@[\w-]+(?:\.[\w-]+)+/);
  if (emailMatch) return emailMatch[0];

  const phoneMatch = message.match(/\+?\d[\d\s().-]{5,}\d/);
  if (phoneMatch) return phoneMatch[0];

  if (!hasVerifiedCustomer) {
    const numericMatch = message.match(/\b\d+\b/);
    if (numericMatch) return numericMatch[0];
  }

  return null;
}

function upsertCaseSummary(cases, nextCase) {
  const summary = {
    id: nextCase.id,
    title: nextCase.title,
    group: nextCase.group,
    created_at: nextCase.created_at,
    updated_at: nextCase.updated_at,
    verified_customer_id: nextCase.verified_customer_id,
    message_count: nextCase.message_count,
  };
  const without = cases.filter((item) => item.id !== summary.id);
  return [summary, ...without].sort((a, b) => new Date(b.updated_at) - new Date(a.updated_at));
}
