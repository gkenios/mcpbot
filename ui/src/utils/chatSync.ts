import { MessageItem } from "../backend";

const channel = new BroadcastChannel("chat-sync");

export function broadcastNewMessage(
  conversationId: string,
  message: Partial<MessageItem>
) {
  channel.postMessage({
    type: "new-message",
    conversationId,
    payload: message
  });
}

export function broadcastClearHistory(conversationId: string) {
  channel.postMessage({ type: "clear-history", conversationId });
}

export function onChatEvent(
  callback: (
    data: {
      type: "new-message" | "clear-history",
      conversationId: string,
      payload?: Partial<MessageItem>,
    }
  ) => void
) {
  channel.onmessage = (event) => {
    if (event.data?.type && event.data?.conversationId) {
      callback(event.data);
    }
  };
}
