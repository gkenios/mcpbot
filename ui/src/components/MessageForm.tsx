import { FC, FormEvent, useRef, useState } from 'react';

import { MessageItem, Role, sendMessage } from '../backend';
import { useAutoScroll } from "../hooks";
import { broadcastNewMessage } from '../utils';

interface MessageFormProps {
  conversationId: string;
  setChatHistory: React.Dispatch<React.SetStateAction<Partial<MessageItem>[]>>;
  chatBodyRef: React.RefObject<HTMLDivElement | null>;
}

const MessageForm: FC<MessageFormProps> = ({ conversationId, setChatHistory, chatBodyRef }) => {
  const inputRef = useRef<HTMLInputElement>(null);
  const [isSending, setIsSending] = useState(false);

  useAutoScroll(chatBodyRef, [isSending]);

  const handleFormSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const input = inputRef.current;
    if (!input) return;

    // Disable the button and input while sending
    setIsSending(true);
    const message = input.value.trim();
    if (!message) return;

    // Clear the input field
    input.value = "";
    let full_response: string = "";

    // Update chat history with the human message and start loading AI message
    setChatHistory(history => [...history, {text: message, role: Role.Human}]);
    broadcastNewMessage(conversationId, {text: message, role: Role.Human});
    setChatHistory(history => [...history, {text: "__loading__", role: Role.AI}]);

    // AI streaming message
    for await (const chunk of sendMessage(message,conversationId)) {
      full_response += chunk.ai.text;
      if (full_response.length > 0) {
        setChatHistory(history => {
          const newHistory = [...history];
          newHistory[newHistory.length - 1] = {text: full_response, role: Role.AI};
          return newHistory;
        });
      }
    }
    broadcastNewMessage(conversationId, {text: full_response, role: Role.AI});

    // Unblock the button and input after sending
    setIsSending(false);
    // Set the cursor to the input field
    requestAnimationFrame(() => {
      inputRef.current?.focus();
    });
  };

  return (
    <form onSubmit={handleFormSubmit} className="chat-form">
      <input
        ref={inputRef}
        disabled={isSending}
        type="text"
        placeholder="Type your message..."
        className="message-input"
        required
      />
      <button
        disabled={isSending}
        type="submit"
        className="material-symbols-rounded"
      >
        send
      </button>
    </form>
  );
};

export default MessageForm;
