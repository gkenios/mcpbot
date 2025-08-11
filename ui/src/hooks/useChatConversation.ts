import { useState, useEffect, useRef } from 'react';

import { MessageItem, getConversations, createConversation, getMessages } from '../backend';
import { onChatEvent, broadcastClearHistory } from '../utils';

interface UseChatConversationResult {
  conversationId: string;
  setConversationId: React.Dispatch<React.SetStateAction<string>>;
  chatHistory: Partial<MessageItem>[];
  setChatHistory: React.Dispatch<React.SetStateAction<Partial<MessageItem>[]>>;
  loadingConversation: boolean;
  conversationError: string | null;
}

const useChatConversation = (): UseChatConversationResult => {
  const [conversationId, setConversationId] = useState<string>("");
  const [chatHistory, setChatHistory] = useState<Partial<MessageItem>[]>([]);
  const [loadingConversation, setLoadingConversation] = useState<boolean>(true);
  const [conversationError, setConversationError] = useState<string | null>(null);
  const hasInitialized = useRef(false);

  useEffect(() => {
    if (hasInitialized.current) return;
    hasInitialized.current = true;

    const initializeConversation = async () => {
      setLoadingConversation(true);
      setConversationError(null);

      try {
        const conversations = await getConversations();

        // If there are existing conversations, use the latest one
        if (conversations && conversations.length > 0) {
          const latest = conversations[conversations.length - 1];
          setConversationId(latest.id);
          const messages = await getMessages(latest.id);
          setChatHistory(messages);
        }

        // If no conversations exist, create a new one
        else {
          const newConv = await createConversation();
          setConversationId(newConv.id);
          setChatHistory([]);
          broadcastClearHistory(newConv.id);
        }
      } catch (error) {
        console.error("Failed to initialize conversation:", error);
        setConversationError(error.message || "Failed to initialize conversation");
      } finally {
        setLoadingConversation(false);
      }
    };

    initializeConversation();
  }, []);

  // 🔁 Real-time update of conversation from other tabs (broadcast)
  useEffect(() => {
    const handleEvent = (
      data: {
        type: "new-message" | "clear-history"
        conversationId: string
        payload?: Partial<MessageItem>
      }
    ) => {
      if (data.conversationId !== conversationId) return;

      if (data.type === "new-message" && data.payload) {
        setChatHistory(prev => [...prev, data.payload!]);
      }

      if (data.type === "clear-history") {
        setChatHistory([]);
      }
    };

    onChatEvent(handleEvent);
  }, [conversationId]);

  return {
    conversationId,
    setConversationId,
    chatHistory,
    setChatHistory,
    loadingConversation,
    conversationError
  };
};

export default useChatConversation;
