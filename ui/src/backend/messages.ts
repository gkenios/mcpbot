import { type OrderBy, fetchWithToken } from "./common";

enum Role {
  Human = "human",
  AI = "ai",
};

type MessageItem = {
  id: string;
  conversation_id: string;
  user_id: string;
  role: Role;
  text: string;
  created_at: string;
};

type CreateMessageResponse = {
  human: MessageItem;
  ai: MessageItem;
}

function findJsonObjectEnd(str: string): number {
  let depth = 0;
  let inString = false;
  for (let i = 0; i < str.length; i++) {
    const char = str[i];
    if (char === '"' && str[i - 1] !== '\\') inString = !inString;
    if (inString) continue;
    if (char === '{') depth++;
    if (char === '}') {
      depth--;
      if (depth === 0) return i;
    }
  }
  return -1;
}

async function* sendMessage(
  message: string,
  conversationId: string,
): AsyncGenerator<CreateMessageResponse> {
  const url = `/conversations/${conversationId}/messages`;
  const body = {message: message};
  const response = await fetchWithToken({
    url: url,
    method: "POST",
    body: body
  }) as Response;

  if (!response.body) {
    throw new Error('Response body is null');
  }
  const reader = response.body.getReader();
  const decoder = new TextDecoder('utf-8');
  let buffer = '';

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });

    let endIdx;
    while ((endIdx = findJsonObjectEnd(buffer)) !== -1) {
      const jsonStr = buffer.slice(0, endIdx + 1);
      buffer = buffer.slice(endIdx + 1);

      try {
        const chunk = JSON.parse(jsonStr) as CreateMessageResponse;
        yield chunk;
      } catch (err) {
        console.warn('Failed to parse chunk:', jsonStr, err);
      }
    }
  }

  // Try to parse any remaining buffer
  if (buffer.trim()) {
    try {
      const chunk = JSON.parse(buffer) as CreateMessageResponse;
      yield chunk;
    } catch (err) {
      console.warn('Failed to parse trailing buffer:', buffer, err);
    }
  }
}


async function* editMessage(
  message: string,
  messageId: string,
  conversationId: string,
): AsyncGenerator<CreateMessageResponse> {
  const url = `/conversations/${conversationId}/messages/${messageId}`;
  const body = {message: message};
  const response = await fetchWithToken({
    url: url,
    method: "PATCH",
    body: body
  }) as Response;

  if (!response.body) {
    throw new Error('Response body is null');
  }
  const reader = response.body.getReader();
  const decoder = new TextDecoder('utf-8');
  let buffer = '';

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });

    let endIdx;
    while ((endIdx = findJsonObjectEnd(buffer)) !== -1) {
      const jsonStr = buffer.slice(0, endIdx + 1);
      buffer = buffer.slice(endIdx + 1);

      try {
        const chunk = JSON.parse(jsonStr) as CreateMessageResponse;
        yield chunk;
      } catch (err) {
        console.warn('Failed to parse chunk:', jsonStr, err);
      }
    }
  }

  // Try to parse any remaining buffer
  if (buffer.trim()) {
    try {
      const chunk = JSON.parse(buffer) as CreateMessageResponse;
      yield chunk;
    } catch (err) {
      console.warn('Failed to parse trailing buffer:', buffer, err);
    }
  }
}

async function getMessages(
  conversation_id: string,
  orderBy: OrderBy = 'ASC',
): Promise<MessageItem[]> {
  const url = `/conversations/${conversation_id}/messages`
  const params = new URLSearchParams({order_by: orderBy});
  return fetchWithToken<MessageItem[]>({
    url: `${url}?${params.toString()}`,
    method: "GET",
    parseJson: true
  });
}

export { type MessageItem, Role, editMessage, getMessages, sendMessage};
