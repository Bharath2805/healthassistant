import { FormEvent } from "react";

interface ChatInputProps {
  input: string;
  setInput: (val: string) => void;
  onSend: () => void;
  loading?: boolean;
  className?: string;
  sendButtonClass?: string;
}

const ChatInput = ({
  input,
  setInput,
  onSend,
  loading,
  className,
  sendButtonClass,
}: ChatInputProps) => {
  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    if (input.trim()) {
      onSend();
    }
  };

  return (
    <form onSubmit={handleSubmit} className={className}>
      <input
        type="text"
        value={input}
        onChange={(e) => setInput(e.target.value)}
        placeholder="Ask something health-related..."
        disabled={loading}
      />
      <button
        type="submit"
        className={sendButtonClass}
        disabled={!input.trim() || loading}
      >
        Send
      </button>
    </form>
  );
};

export default ChatInput;
