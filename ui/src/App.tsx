import { useState, useRef } from "react";

import { createConversation, deleteConversation } from "./backend";
import { Message, MessageForm } from "./components";
import { BotIcon } from "./components/icons";
import { CHATBOT_NAME, POPUP_OPEN_AT_START} from "./constants";
import { useAutoScroll, useChatConversation } from "./hooks";
import { broadcastClearHistory } from "./utils";

function App() {
  const [showChatbot, setShowChatbot] = useState<boolean>(POPUP_OPEN_AT_START);
  const chatBodyRef = useRef<HTMLDivElement>(null);

  // Custom hooks
  const {
    conversationId,
    setConversationId,
    chatHistory,
    setChatHistory,
    loadingConversation,
  } = useChatConversation();
  useAutoScroll(chatBodyRef, [chatHistory.length]);

  if (loadingConversation) return null;

  return (
    <div className={`container chat-${showChatbot ? "open" : "closed"}`}>
      <button onClick={() => setShowChatbot(prev => !prev)} id="chatbot-toggler">
        <span className="material-symbols-rounded">mode_comment</span>
        <span className="material-symbols-rounded">close</span>
      </button>

      <div className="chatbot-popup">

        {/* Chatbot Header */}
        <div className="chat-header">
          <div className="header-info">
            <BotIcon />
            <h2 className="logo-text">{CHATBOT_NAME}</h2>
          </div>
          <div className="chat-header-buttons">
            <button
              onClick={async () => {
                await deleteConversation(conversationId);
                const newConv = await createConversation();
                setConversationId(newConv.id);
                setChatHistory([]);
                broadcastClearHistory(newConv.id);
              }}
              className="material-symbols-rounded"
            >add
            </button>
            <button
              onClick={() => setShowChatbot((prev) => !prev)}
              className="material-symbols-rounded"
            >close
            </button>
          </div>
        </div>

        {/* Chatbot Body */}
        <div ref={chatBodyRef} className="chat-body">
          {chatHistory.map((chat, index) => (
            chatHistory.length &&
            <Message
              key={index}
              chat={chat}
            />
          ))}
        </div>

        {/* Chatbot Footer */}
        <div className="chat-footer">
          <MessageForm
            conversationId={conversationId}
            setChatHistory={setChatHistory}
            chatBodyRef={chatBodyRef}
          />
        </div>
      </div>
    </div>
  )
}
export default App;
