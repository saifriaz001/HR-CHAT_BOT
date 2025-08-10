// ChatLayout.jsx
import { Outlet, Link, useNavigate, useParams } from "react-router-dom";
import { useChats } from "./ChatsContext.jsx";
import { useEffect, useState } from "react";
import { FaBars, FaPlus, FaRobot, FaTrash } from "react-icons/fa";
import { RiChatNewLine } from "react-icons/ri";


export default function ChatLayout() {
    const { chats, createChat, deleteChat } = useChats();
    const { chatId } = useParams();
    const nav = useNavigate();

    const [mobileOpen, setMobileOpen] = useState(false);

    const startNew = () => {
        const id = createChat();
        nav(`/chat/${id}`);
        setMobileOpen(false);
    };

    // Close drawer with Esc
    useEffect(() => {
        const onEsc = (e) => e.key === "Escape" && setMobileOpen(false);
        window.addEventListener("keydown", onEsc);
        return () => window.removeEventListener("keydown", onEsc);
    }, []);

    const SidebarList = ({ closeAfterClick = false }) => (
        <div className="flex-1 overflow-y-auto">
            {chats.map((c) => {
                const active = chatId ? c.id === chatId : c.id === chats[0]?.id;
                return (
                    <div
                        key={c.id}
                        className={`group flex items-center gap-2 px-3 py-3 ${active ? "bg-gray-100" : "hover:bg-gray-50"
                            }`}
                    >
                        <FaRobot className="shrink-0 font-paragraph" />
                        <Link
                            to={`/chat/${c.id}`}
                            onClick={() => closeAfterClick && setMobileOpen(false)}
                            className="flex-1 min-w-0"
                        >
                            <div className="truncate text-sm font-paragraph ">
                                {c.title || "New chat"}
                            </div>
                            <div className="text-xs font-paragraph ">
                                {new Date(c.createdAt).toLocaleString()}
                            </div>
                        </Link>
                        <button
                            className="opacity-0 group-hover:opacity-100 p-2 rounded hover:bg-gray-200"
                            title="Delete"
                            onClick={() => {
                                const nextId = deleteChat(c.id);     // returns the next/created chat id
                                // Only redirect if you deleted the active one
                                const isActive = chatId ? c.id === chatId : c.id === chats[0]?.id;
                                if (isActive && nextId) nav(`/chat/${nextId}`);
                            }}
                        >
                            <FaTrash className="text-gray-600" />
                        </button>

                    </div>
                );
            })}
        </div>
    );

    return (
        <div className="h-screen w-full flex bg-gradient-to-br from-rose-100 via-slate-50 to-indigo-100">
            {/* Mobile hamburger (hidden on md+) */}
            <div className="md:hidden absolute top-6 bg-white left-4 z-50">
                <button
                    onClick={() => setMobileOpen(true)}
                    className="p-2 rounded-lg bg-white/90 border shadow"
                    aria-label="Open sidebar"
                >
                    <FaBars />
                </button>
            </div>

            {/* Desktop sidebar */}
            <aside className="hidden md:flex md:w-72 bg-white/70 backdrop-blur border-r border-gray-200 flex-col">
                <div className="flex flex-col px-4 gap-2  py-4 border-b">
                    <div className="font-bold font-heading">Chats</div>
                    <div className=" flex flex-row ">
                        <button
                            onClick={startNew}
                            className="inline-flex items-center font-paragraph  gap-40  py-2 rounded-xl not-only: hover:opacity-90"
                        >

                            <div>New chat</div>
                            <RiChatNewLine />
                        </button>
                    </div>
                </div>
                <SidebarList />
            </aside>

            {/* Mobile drawer */}
            <aside
                className={`md:hidden fixed inset-y-0 left-0 w-72 bg-white shadow-xl z-50
        transform transition-transform duration-300
        ${mobileOpen ? "translate-x-0" : "-translate-x-full"}`}
                aria-hidden={!mobileOpen}
            >
                <div className="flex items-center gap-2 px-4 py-4 border-b">
                    <div className="font-semibold font-heading">Chats</div>
                    <div className="ml-auto flex gap-2">
                        <button
                            onClick={startNew}
                            className="inline-flex items-center gap-2 px-3 font-paragraph py-2 rounded-xl bg-white "
                        >
                            <RiChatNewLine />
                            <span >New</span>
                        </button>
                        <button
                            onClick={() => setMobileOpen(false)}
                            className="px-3  font-paragraph py-2 rounded-lg  hover:text-black"
                            aria-label="Close sidebar"
                        >
                            ✕
                        </button>
                    </div>
                </div>
                <SidebarList closeAfterClick />
            </aside>

            {/* Backdrop for mobile drawer */}
            {mobileOpen && (
                <div
                    className="md:hidden fixed  inset-0 "
                    onClick={() => setMobileOpen(false)}
                />
            )}

            {/* Main content */}
            <main className="flex-1 flex flex-col relative">
                <Outlet />
            </main>
        </div>
    );
}
