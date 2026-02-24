import { Component, ElementRef, ViewChild, AfterViewChecked, signal, WritableSignal, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { MatCardModule } from '@angular/material/card';
import { MatInputModule } from '@angular/material/input';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { DomSanitizer, SafeHtml } from '@angular/platform-browser';
import { TextFieldModule } from '@angular/cdk/text-field';
import { ChatService } from './services/chat.service';

interface Message {
  role: 'user' | 'ai';
  content: string;
  safeContent?: SafeHtml;
}

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    MatCardModule,
    MatInputModule,
    MatButtonModule,
    MatIconModule,
    MatProgressSpinnerModule,
    TextFieldModule
  ],
  templateUrl: './app.html',
  styleUrl: './app.scss'
})
export class App implements AfterViewChecked {
  @ViewChild('scrollContainer') private scrollContainer!: ElementRef;
  @ViewChild('chatInput') private chatInput!: ElementRef<HTMLInputElement>;

  private sanitizer = inject(DomSanitizer);
  private chatService = inject(ChatService);

  messages: WritableSignal<Message[]> = signal([]);

  userInput = '';
  isThinking = signal(false);
  sessionId = 'aura_session_' + Math.random().toString(36).substring(7);

  constructor() {
    this.messages.set([
      {
        role: 'ai',
        content: 'Hello! I am Dr. Aura, your biomedical research assistant. Ask me anything about the Hereditary hemorrhagic telangiectasia (HHT) disease.',
        safeContent: this.sanitizer.bypassSecurityTrustHtml('Hello! I am Dr. Aura, your biomedical research assistant. Ask me anything about the Hereditary hemorrhagic telangiectasia (HHT) disease.')
      }
    ]);
  }

  ngAfterViewChecked() {
    this.scrollToBottom();
  }

  scrollToBottom(): void {
    try {
      this.scrollContainer.nativeElement.scrollTop = this.scrollContainer.nativeElement.scrollHeight;
    } catch (err) { }
  }

  formatMarkdownAndCitations(text: string): SafeHtml {
    let formattedText = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    formattedText = formattedText.replace(/\n\n/g, '</p><p>');
    formattedText = '<p>' + formattedText + '</p>';

    // Parse Harvard citations [PMID: 12345] to Clickable Links
    // Match the entire citation group: "(Author, Year) [PMID: 12345]"
    const citationRegex = /(\([^)]+\))\s*\[PMID:\s*(\d+)\]/g;
    formattedText = formattedText.replace(citationRegex, (match, authorYear, pmid) => {
      const url = `https://pubmed.ncbi.nlm.nih.gov/${pmid}/`;
      return `<a href="${url}" target="_blank" rel="noopener noreferrer" class="pmid-link">${authorYear}</a>`;
    });

    return this.sanitizer.bypassSecurityTrustHtml(formattedText);
  }

  onEnter(event: Event) {
    event.preventDefault();
    this.sendMessage();
  }

  sendMessage() {
    if (!this.userInput.trim() || this.isThinking()) return;

    const query = this.userInput;
    this.messages.update(msgs => [...msgs, { role: 'user', content: query }]);
    this.userInput = '';
    this.isThinking.set(true);

    this.chatService.sendMessage(query, this.sessionId).subscribe({
      next: (response) => {
        this.messages.update(msgs => [
          ...msgs,
          {
            role: 'ai',
            content: response.answer,
            safeContent: this.formatMarkdownAndCitations(response.answer)
          }
        ]);
        this.isThinking.set(false);
        setTimeout(() => this.chatInput?.nativeElement?.focus(), 50);
      },
      error: (err) => {
        console.error(err);
        this.messages.update(msgs => [
          ...msgs,
          {
            role: 'ai',
            content: 'Connection Error: Unable to reach the backend.',
            safeContent: this.sanitizer.bypassSecurityTrustHtml('<strong>Connection Error:</strong> Unable to reach the backend.')
          }
        ]);
        this.isThinking.set(false);
        setTimeout(() => this.chatInput?.nativeElement?.focus(), 50);
      }
    });
  }
}
