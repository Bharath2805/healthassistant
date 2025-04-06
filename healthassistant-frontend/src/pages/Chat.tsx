import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import ChatBubble from "../components/ChatBubble";
import ChatInput from "../components/ChatInput";
import SessionSidebar from "../components/Sidebar";
import styles from "../styles/chat.module.scss";
import assistantIcon from "../assets/assistant-icon.png";
import userIcon from "../assets/user-icon.png";
import { ToastContainer, toast } from "react-toastify";
import "react-toastify/dist/ReactToastify.css";

interface Message {
  role: "user" | "assistant";
  content: string;
  suggested_specialty?: string;
  high_severity?: boolean;
}

interface Session {
  session_id: string;
  session_name: string;
}

const Chat = () => {
  const [healthTip, setHealthTip] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([
    { role: "assistant", content: "Hello! How can I assist you today?" },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [fetchingHistory, setFetchingHistory] = useState(false);
  const [sessions, setSessions] = useState<Session[]>([]);
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
  const [page, setPage] = useState(0);
  const [hasMoreSessions, setHasMoreSessions] = useState(true);
  const limit = 10;
  const navigate = useNavigate();

  useEffect(() => {
    const fetchTip = async () => {
      try {
        const res = await fetch("http://127.0.0.1:8000/health/tip");
        const data = await res.json();
        setHealthTip(data.tip);
      } catch (err) {
        console.error("Failed to load health tip", err);
      }
    };
    fetchTip();
  }, []);

  const fetchSessions = async () => {
    if (!hasMoreSessions) return;
    const token = localStorage.getItem("access_token");
    if (!token) return;

    try {
      const res = await fetch(
        `http://127.0.0.1:8000/health/sessions?offset=${page * limit}&limit=${limit}`,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      if (res.ok) {
        const newSessions = await res.json();
        const mapped: Session[] = newSessions.map((s: { id: string; name: string }) => ({
          session_id: s.id,
          session_name: s.name,
        }));

        setSessions((prev) => {
          const seen = new Set(prev.map((s) => s.session_id));
          return [...prev, ...mapped.filter((s: Session) => !seen.has(s.session_id))];
        });

        if (newSessions.length < limit) setHasMoreSessions(false);
      }
    } catch (err) {
      console.error("Failed to fetch sessions:", err);
      toast.error("Failed to load sessions.");
    }
  };

  const fetchChatHistory = async (sessionId: string) => {
    setFetchingHistory(true);
    try {
      const token = localStorage.getItem("access_token");
      const res = await fetch(
        `http://127.0.0.1:8000/health/messages?session_id=${sessionId}`,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      if (!res.ok) throw new Error();
      const data = await res.json();
      setMessages(data);
      setActiveSessionId(sessionId);
    } catch {
      toast.error("Failed to load chat history.");
      setMessages([{ role: "assistant", content: "Failed to load chat history." }]);
    } finally {
      setFetchingHistory(false);
    }
  };

  const handleSend = async () => {
    if (!input.trim()) return;

    const userMessage: Message = { role: "user", content: input };
    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setLoading(true);

    try {
      const token = localStorage.getItem("access_token");
      const url = `http://127.0.0.1:8000/health/general${activeSessionId ? "" : "?force_new=true"}`;
      const res = await fetch(url, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ message: userMessage.content }),
      });

      const data = await res.json();
      console.log("AI Response:", data);

      if (!data.session_id || !data.response) throw new Error();
      setActiveSessionId(data.session_id);

      // Try to extract fallback values from plain text if not present
      const extractSpecialty = (text: string): string | null => {
        const match = text.match(/Recommended Specialist: (.+)/i);
        return match ? match[1].trim() : null;
      };
      const extractSeverity = (text: string): string | null => {
        const match = text.match(/Severity: (.+)/i);
        return match ? match[1].trim().toLowerCase() : null;
      };

      const fallbackSpecialty = extractSpecialty(data.response);
      const fallbackSeverity = extractSeverity(data.response);

      const assistantMessage: Message = {
        role: "assistant",
        content: data.response,
        suggested_specialty: data.suggested_specialty ?? fallbackSpecialty,
        high_severity:
          data.high_severity ??
          (fallbackSeverity ? fallbackSeverity === "high" : false),
      };

      setMessages((prev) => [...prev, assistantMessage]);

      setSessions((prev) => {
        const exists = prev.find((s) => s.session_id === data.session_id);
        if (!exists) {
          return [
            { session_id: data.session_id, session_name: "Untitled Chat" },
            ...prev,
          ];
        }
        return prev;
      });
    } catch (err) {
      toast.error("Failed to send message.");
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: "Something went wrong." },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleNewChat = () => {
    setMessages([{ role: "assistant", content: "Hello! How can I assist you today?" }]);
    setActiveSessionId(null);
    setInput("");
    setFetchingHistory(false);
  };

  const handleRename = async (id: string, name: string) => {
    const token = localStorage.getItem("access_token");
    try {
      await fetch(`http://127.0.0.1:8000/health/sessions/${id}/rename`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ name }),
      });
      setSessions((prev) =>
        prev.map((s) => (s.session_id === id ? { ...s, session_name: name } : s))
      );
    } catch {
      toast.error("Rename failed.");
    }
  };

  const handleDelete = async (id: string) => {
    const token = localStorage.getItem("access_token");
    try {
      await fetch(`http://127.0.0.1:8000/health/sessions/${id}`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${token}` },
      });
      setSessions((prev) => prev.filter((s) => s.session_id !== id));
      if (id === activeSessionId) handleNewChat();
    } catch {
      toast.error("Delete failed.");
    }
  };

  useEffect(() => {
    fetchSessions();
  }, [page]);

  const lastAssistantMsg = [...messages].reverse().find((m) => m.role === "assistant");

  return (
    <div className={styles.chatWrapper}>
      <SessionSidebar
        sessions={sessions}
        onNewChat={handleNewChat}
        onSelectSession={fetchChatHistory}
        onRename={handleRename}
        onDelete={handleDelete}
        onNextPage={() => setPage((p) => p + 1)}
        hasMoreSessions={hasMoreSessions}
      />

      <div className={styles.chatContainer}>
        {healthTip && (
          <div className={styles.healthTipCard}>
            <div className={styles.tipHeader}>💡 Daily Health Tip</div>
            <div className={styles.tipText}>{healthTip}</div>
          </div>
        )}

        <div className={styles.messages}>
          {fetchingHistory ? (
            <p>Loading chat history...</p>
          ) : (
            messages.map((msg, idx) => (
              <ChatBubble
                key={idx + msg.content.slice(0, 5)}
                role={msg.role}
                content={msg.content}
                avatar={msg.role === "assistant" ? assistantIcon : userIcon}
                className={`${styles.chatBubble} ${styles[msg.role]}`}
              />
            ))
          )}
          {loading && (
            <ChatBubble
              role="assistant"
              content="Typing..."
              avatar={assistantIcon}
              className={`${styles.chatBubble} ${styles.loading}`}
            />
          )}

          {lastAssistantMsg?.high_severity && lastAssistantMsg?.suggested_specialty && (
            <button
              className={styles.doctorSuggestButton}
              onClick={() =>
                navigate(
                  `/doctors?specialty=${encodeURIComponent(
                    lastAssistantMsg.suggested_specialty ?? ""
                  )}&location=auto`
                )
              }
            >
              🩺 Find Nearby {lastAssistantMsg.suggested_specialty}
            </button>
          )}
        </div>

        <ChatInput
          input={input}
          setInput={setInput}
          onSend={handleSend}
          loading={loading}
          className={styles.chatInput}
          sendButtonClass={styles.sendButton}
        />
      </div>

      <ToastContainer position="top-right" autoClose={3000} />
    </div>
  );
};

export default Chat;