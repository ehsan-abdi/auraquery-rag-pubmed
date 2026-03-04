import { Injectable } from '@angular/core';

export interface ChatRequest {
    query: string;
    session_id: string;
}

export interface StreamEvent {
    type: 'status' | 'token';
    message?: string;
    content?: string;
}

@Injectable({
    providedIn: 'root'
})
export class ChatService {
    // Hardcoded for local RAG execution; move to environment.ts for production
    private apiUrl = 'https://auraquery-api-79181789355.us-central1.run.app/api';

    async *streamMessage(query: string, sessionId: string): AsyncGenerator<StreamEvent, void, unknown> {
        const payload: ChatRequest = { query, session_id: sessionId };

        const response = await fetch(`${this.apiUrl}/chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(payload)
        });

        if (!response.ok || !response.body) {
            throw new Error(`Connection Error: ${response.statusText}`);
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder('utf-8');
        let buffer = '';

        while (true) {
            const { value, done } = await reader.read();
            if (done) break;

            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split('\n\n');

            // Keep the last incomplete chunk in the buffer
            buffer = lines.pop() || '';

            for (const line of lines) {
                if (line.trim()) {
                    try {
                        const data: StreamEvent = JSON.parse(line.trim());
                        yield data;
                    } catch (e) {
                        console.warn('Failed to parse SSE line:', line);
                    }
                }
            }
        }
    }
}
