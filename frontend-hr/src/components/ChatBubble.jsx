// src/components/ChatBubble.jsx
export default function ChatBubble({ type, text }) {
  const isUser = type === "user";

  return (
    <div className={`p-3 rounded ${isUser ? "bg-blue-100 text-right ml-auto" : "bg-gray-100 text-left mr-auto"}`}>
      <p className="font-paragraph text-sm">{text}</p>
    </div>
  );
}
