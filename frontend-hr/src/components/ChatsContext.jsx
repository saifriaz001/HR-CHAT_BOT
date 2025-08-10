// ChatsContext.jsx
import { createContext, useContext, useEffect, useState } from "react";

const ChatsCtx = createContext(null);

export const useChats = () => {
  const ctx = useContext(ChatsCtx);
  if (!ctx) throw new Error("useChats must be used inside <ChatsProvider>");
  return ctx;
};

function uid() { return Math.random().toString(36).slice(2, 10); }
const EMPTY_CHAT = () => ({ id: uid(), title: "New chat", messages: [], candidates: [], createdAt: Date.now() });

export function ChatsProvider({ children }) {
  const [chats, setChats] = useState(() => {
    const saved = localStorage.getItem("hr_chats_v1");
    return saved ? JSON.parse(saved) : [EMPTY_CHAT()];
  });

  useEffect(() => {
    localStorage.setItem("hr_chats_v1", JSON.stringify(chats));
  }, [chats]);

  const createChat = () => {
    const c = EMPTY_CHAT();
    setChats((prev) => [c, ...prev]);
    return c.id;
  };

  // Always keep at least one chat; return the next active id
  const deleteChat = (id) => {
    let nextId = null;
    setChats((prev) => {
      const idx = prev.findIndex((c) => c.id === id);
      const filtered = prev.filter((c) => c.id !== id);

      if (filtered.length === 0) {
        const nc = EMPTY_CHAT();
        nextId = nc.id;
        return [nc];
      }

      const neighbor = filtered[Math.max(0, idx - 1)] || filtered[0];
      nextId = neighbor.id;
      return filtered;
    });
    return nextId;
  };

  const updateChatById = (id, updater) =>
    setChats((prev) => prev.map((c) => (c.id === id ? { ...c, ...updater(c) } : c)));

  return (
    <ChatsCtx.Provider value={{ chats, createChat, deleteChat, updateChatById }}>
      {children}
    </ChatsCtx.Provider>
  );
}
