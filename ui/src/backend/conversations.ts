import { type OrderBy, fetchWithToken} from "./common";

type ConversationItem = {
    id: string;
    user_id: string;
    created_at: string;
    last_message_at: string;
};

async function createConversation(): Promise<ConversationItem> {
    const url = "/conversations";
    return fetchWithToken<ConversationItem>({
        url: url,
        method: "POST",
        parseJson: true,
    });
}

async function getConversations(
    orderBy: OrderBy = 'DESC',
): Promise<ConversationItem[]> {
    const url = "/conversations";
    const params = new URLSearchParams({order_by: orderBy});
    return fetchWithToken<ConversationItem[]>({
        url: `${url}?${params.toString()}`,
        method: "GET",
        parseJson: true
    });
}

async function deleteConversation(conversation_id: string): Promise<void> {
    const url = `/conversations/${conversation_id}`;
    fetchWithToken({
        url: url,
        method: "DELETE"
    });
}

export {
    type ConversationItem,
    createConversation,
    deleteConversation,
    getConversations,
};
