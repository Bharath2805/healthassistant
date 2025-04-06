import { useState } from "react";
import styles from "../styles/sidebar.module.scss";
import { FaTrash, FaPen } from "react-icons/fa";

interface Session {
  session_id: string;
  session_name: string;
}

interface Props {
  sessions: Session[];
  onNewChat: () => void;
  onSelectSession: (id: string) => void;
  onRename: (id: string, name: string) => void;
  onDelete: (id: string) => void;
  onNextPage: () => void;
  hasMoreSessions: boolean;
}

const SessionSidebar = ({
  sessions,
  onNewChat,
  onSelectSession,
  onRename,
  onDelete,
  onNextPage,
  hasMoreSessions,
}: Props) => {
  const [editingId, setEditingId] = useState<string | null>(null);
  const [renameValue, setRenameValue] = useState("");

  const handleRenameSubmit = (id: string) => {
    if (renameValue.trim()) {
      onRename(id, renameValue.trim());
      setEditingId(null);
    }
  };

  return (
    <div className={styles.sidebar}>
      <button className={styles.newChat} onClick={onNewChat}>+ New Chat</button>

      <div className={styles.sessionList}>
        {sessions.map((s) => (
          <div key={s.session_id} className={styles.sessionItem}>
            {editingId === s.session_id ? (
              <input
                className={styles.renameInput}
                value={renameValue}
                autoFocus
                onChange={(e) => setRenameValue(e.target.value)}
                onBlur={() => handleRenameSubmit(s.session_id)}
                onKeyDown={(e) => {
                  if (e.key === "Enter") handleRenameSubmit(s.session_id);
                  if (e.key === "Escape") setEditingId(null);
                }}
              />
            ) : (
              <span
                className={styles.sessionTitle}
                onClick={() => onSelectSession(s.session_id)}
              >
                {s.session_name}
              </span>
            )}

            <div className={styles.actions}>
              <FaPen
                size={14}
                color="#aaa"
                onClick={() => {
                  setEditingId(s.session_id);
                  setRenameValue(s.session_name);
                }}
              />
              <FaTrash
                size={14}
                color="#e76e6e"
                onClick={() => onDelete(s.session_id)}
              />
            </div>
          </div>
        ))}

        {hasMoreSessions && (
          <button
            onClick={onNextPage}
            style={{
              marginTop: "1rem",
              color: "#ccc",
              background: "transparent",
              border: "1px solid #333",
              borderRadius: "8px",
              padding: "0.5rem",
            }}
          >
            Load More
          </button>
        )}
      </div>
    </div>
  );
};

export default SessionSidebar;
