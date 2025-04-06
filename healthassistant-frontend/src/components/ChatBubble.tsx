interface ChatBubbleProps {
    role: "user" | "assistant";
    content: string;
    avatar: string;
    className?: string;
  }
  
  const ChatBubble = ({ role, content, avatar, className }: ChatBubbleProps) => {
    return (
      <div className={className}>
        <img
          src={avatar}
          alt={`${role} avatar`}
          style={{
            width: "28px",
            height: "28px",
            borderRadius: "50%",
            marginRight: "0.75rem",
          }}
        />
        <div>
          <p style={{ fontWeight: "bold", marginBottom: "0.25rem" }}>
            {role === "assistant" ? "Assistant" : "You"}
          </p>
          <p style={{ whiteSpace: "pre-wrap", lineHeight: 1.5 }}>{content}</p>
        </div>
      </div>
    );
  };
  
  export default ChatBubble;
  