// ChatBox.jsx
import { useEffect, useMemo, useRef, useState } from "react";
import { useParams } from "react-router-dom";
import { FaUser, FaRobot, FaPaperPlane, FaSpinner } from "react-icons/fa";
import { useChats } from "./ChatsContext.jsx";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import "../App.css";

export default function ChatBox() {
  const { chats, updateChatById } = useChats();
  const { chatId } = useParams();

  const chat = useMemo(() => {
    if (!chats.length) return null;
    return chatId ? chats.find((c) => c.id === chatId) : chats[0];
  }, [chats, chatId]);

  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const chatEndRef = useRef(null);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [chat?.messages?.length, loading]);

  // Convert plain paragraphs/sentences to Markdown bullets if not already a list.
  const bulletize = (text) => {
  if (!text) return "";
  let t = text.trim();

  // If it's already a list, keep it
  if (/^\s*([-*]|\d+\.)\s+/m.test(t)) return t;

  // Use a rare placeholder to protect dots we DON'T want to split on
  const PLACE = "\u2236"; // ratio symbol

  // Common abbreviations you don’t want to break
  const ABBRS = [
    "Mr.", "Mrs.", "Ms.", "Dr.", "Prof.", "Sr.", "Jr.", "St.",
    "vs.", "etc.", "No.", "Inc.", "Ltd.", "Co.", "Corp.",
    "e.g.", "i.e."
  ];
  const esc = (s) => s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");

  const protect = (s) => {
    // protect decimals like 2.5 or version 1.2
    let out = s.replace(/(\d)\.(\d)/g, `$1${PLACE}$2`);
    // protect known abbreviations
    ABBRS.forEach((a) => {
      const re = new RegExp(esc(a), "gi");
      const safe = a.replace(/\./g, PLACE);
      out = out.replace(re, safe);
    });
    return out;
  };
  const restore = (s) => s.replaceAll(PLACE, ".");

  // Protect, split, restore
  t = protect(t);
  const parts = t.match(/[^.!?]+[.!?]+|[^.!?]+$/g) || [t];

  return parts
    .map((p) => restore(p).trim())
    .filter(Boolean)
    .map((p) => `- ${p}`)
    .join("\n");
};

  const handleSend = async () => {
    const text = query.trim();
    if (!text || !chat || loading) return;
    setLoading(true);

    // optimistic user message
    updateChatById(chat.id, (c) => ({
      messages: [...c.messages, { role: "user", text }],
    }));

    try {
      const res = await fetch("http://localhost:8000/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: text, top_k: 3 }),
      });
      const data = await res.json();

      const title =
        chat.messages.length === 0
          ? text.slice(0, 40) + (text.length > 40 ? "…" : "")
          : chat.title;

      updateChatById(chat.id, (c) => ({
        title,
        messages: [
          ...c.messages,
          {
            role: "assistant",
            text: bulletize(data.answer || "No answer returned."),
          },
        ],
        candidates: data.candidates || [],
      }));
    } catch {
      updateChatById(chat.id, (c) => ({
        messages: [
          ...c.messages,
          { role: "assistant", text: "⚠️ Something went wrong. Please try again." },
        ],
      }));
    } finally {
      setQuery(""); // reset input after send
      setLoading(false);
    }
  };

  if (!chat) return null;

  return (
    <>
      {/* Header */}
      <header className="flex items-center gap-3 px-6 py-4">
        <div className="flex items-center gap-3">
          <FaRobot className="text-indigo-600 text-2xl" />
          <div>
            <h1 className="text-xl md:text-2xl font-bold font-heading">HR Assistant</h1>
            <p className="text-xs md:text-sm font-paragraph">
              Smart candidate search • Role matching • Availability checks
            </p>
          </div>
        </div>
      </header>

      {/* Chat body */}
      <section className="flex-1 overflow-y-auto px-4 md:px-8 py-4 md:py-6">
        {chat.messages.length === 0 && !loading && (
          <div className="max-w-2xl mx-auto mt-16 text-center">
            <h2 className="text-3xl font-semibold mb-3 font-heading">Introducing your HR Copilot</h2>
            <p className="font-paragraph">
              Ask for “Senior React dev in healthcare”, “Data scientist with NLP + AWS”, or paste a JD to get curated matches.
            </p>
          </div>
        )}

        <div className="max-w-3xl mx-auto space-y-4">
          {chat.messages.map((m, i) => (
            <div key={i} className={`flex items-start gap-3 ${m.role === "user" ? "justify-end" : ""}`}>
              {m.role !== "user" && <FaRobot className="text-indigo-600 mt-1" />}

              <div
                className={`max-w-[85%] md:max-w-[75%] px-4 py-3 rounded-2xl shadow-sm ${
                  m.role === "user" ? "bg-indigo-600 font-paragraph1 text-white" : "bg-white font-paragraph2"
                }`}
              >
                {m.role === "assistant" ? (
                  <ReactMarkdown
                    remarkPlugins={[remarkGfm]}
                    components={{
                      ul: (props) => <ul className="list-disc pl-6 space-y-1" {...props} />,
                      ol: (props) => <ol className="list-decimal pl-6 space-y-1" {...props} />,
                      li: (props) => <li className="leading-relaxed" {...props} />,
                      p: (props) => <p className="mb-2" {...props} />,
                      strong: (props) => <strong className="font-semibold" {...props} />,
                    }}
                  >
                    {m.text}
                  </ReactMarkdown>
                ) : (
                  m.text
                )}
              </div>

              {m.role === "user" && <FaUser className="text-gray-600 mt-1" />}
            </div>
          ))}

          {loading && (
            <div className="flex items-center gap-2 font-paragraph">
              <FaSpinner className="animate-spin" /> Thinking…
            </div>
          )}

          <div ref={chatEndRef} />
        </div>
      </section>

      {/* Composer */}
      <footer className="px-4 md:px-8 py-4 border-t bg-white/70 backdrop-blur">
        <div className="max-w-3xl mx-auto flex items-end gap-2">
          <div className="flex-1 relative">
            <input
              className="w-full rounded-2xl md:rounded-3xl border font-paragraph border-gray-300 bg-white px-4 py-3 pr-12 focus:outline-none focus:ring-2 focus:ring-indigo-500"
              placeholder="Ask anything about roles, skills, or candidates…"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleSend()}
              disabled={loading}
            />
            <button
              onClick={handleSend}
              disabled={loading || !query.trim()}
              className="absolute right-2 bottom-2 h-9 w-9 rounded-full flex items-center justify-center bg-indigo-600 text-white hover:bg-indigo-700 disabled:opacity-50"
              title="Send"
            >
              {loading ? <FaSpinner className="animate-spin" /> : <FaPaperPlane />}
            </button>
          </div>
        </div>
        <div className="max-w-3xl mx-auto mt-2 text-xs font-paragraph">
          Press Enter or click the arrow to send • Use the sidebar to switch chats or create a new one
        </div>
      </footer>
    </>
  );
}
