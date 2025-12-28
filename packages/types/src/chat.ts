export interface ChatSession {
    id: string;
    paper_id?: string;
    title: string;
    created_at: string | null;
    updated_at: string | null;
    message_count: number;
    tenant_id?: string;
}

export interface ChatMessage {
    id?: string;
    role: 'user' | 'assistant' | 'system';
    content: string;
    parts?: MessagePart[];
}

export interface MessagePart {
    type: 'text' | 'image' | 'tool-call' | 'tool-result';
    text?: string;
}

export interface SessionsResponse {
    sessions: ChatSession[];
}
