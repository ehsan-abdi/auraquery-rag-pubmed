import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface ChatRequest {
    query: string;
    session_id: string;
}

export interface ChatResponse {
    answer: string;
}

@Injectable({
    providedIn: 'root'
})
export class ChatService {
    // Hardcoded for local RAG execution; move to environment.ts for production
    private apiUrl = 'https://auraquery-api-79181789355.us-central1.run.app/api';

    constructor(private http: HttpClient) { }

    sendMessage(query: string, sessionId: string): Observable<ChatResponse> {
        const payload: ChatRequest = { query, session_id: sessionId };
        return this.http.post<ChatResponse>(`${this.apiUrl}/chat`, payload);
    }
}
