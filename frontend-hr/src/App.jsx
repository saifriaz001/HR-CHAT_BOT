import { Routes, Route, Navigate } from "react-router-dom";
import { ChatsProvider } from "./components/ChatsContext.jsx";
import ChatLayout from "./components/ChatLayout.jsx";
import ChatBox from "./components/ChatBox.jsx";

export default function App() {
  return (
    <ChatsProvider>
      <Routes>
        <Route element={<ChatLayout />}>
          <Route index element={<Navigate to="chat" replace />} />
          <Route path="chat" element={<ChatBox />} />             {/* default /chat uses first chat */}
          <Route path="chat/:chatId" element={<ChatBox />} />     {/* specific chat */}
        </Route>
        <Route path="*" element={<Navigate to="/chat" replace />} />
      </Routes>
    </ChatsProvider>
  );
}
