"use client";
import React, { useEffect, useRef, useState } from 'react';

type Message = {
  id: string;
  from: 'user' | 'ai';
  text: string;
};

type ChatApiResponse = {
  reply: string;
  session_id?: string;
  intent?: string;
  hint_level?: number;
};

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const scroller = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    if (scroller.current) scroller.current.scrollTop = scroller.current.scrollHeight;
  }, [messages.length]);

  // Seed welcome if no messages yet
  useEffect(() => {
    if (messages.length === 0) {
      const welcome: Message = { id: 'welcome', from: 'ai', text: 'Hi there! How can I help you today?' };
      setMessages([welcome]);
    }
  }, []);

  const sendMessage = async (e?: React.FormEvent) => {
    e?.preventDefault();
    const text = input.trim();
    if (!text) return;
    const userMsg: Message = { id: Date.now().toString(), from: 'user', text };
    setMessages((m) => [...m, userMsg]);
    setInput('');
    setError(null);
    setLoading(true);
    try {
      const res = await fetch('http://127.0.0.1:8000/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text, session_id: sessionId }),
      });
      if (!res.ok) {
        const errText = await res.text();
        throw new Error(`Server error: ${errText || res.status}`);
      }
      const data: ChatApiResponse = await res.json();
      if (data.session_id) setSessionId(data.session_id);
      const aiMsg: Message = { id: Date.now().toString(), from: 'ai', text: data.reply };
      setMessages((m) => [...m, aiMsg]);
    } catch (err) {
      const errMsg = (err as Error)?.message ?? 'Unknown error';
      setError(errMsg);
      const aiMsg: Message = { id: Date.now().toString(), from: 'ai', text: `Error: ${errMsg}` };
      setMessages((m) => [...m, aiMsg]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container" style={{ paddingTop: 20, paddingBottom: 20 }}>
      <div className="chat-container" style={{ height: '70vh' }}>
        <div className="chat-header">AI Chat</div>
        <div className="message-area" ref={scroller} aria-label="messages" role="log">
          {messages.map((m) => (
            <div key={m.id} className={`message ${m.from}`}>
              <div className="bubble">{m.text}</div>
            </div>
          ))}
          {loading && (
            <div className="message ai">
              <div className="bubble"><span className="typing" />Typing...</div>
            </div>
          )}
          {error && (
            <div className="message ai">
              <div className="bubble" style={{ color: '#b00020' }}>{error}</div>
            </div>
          )}
        </div>
        <form className="input-area" onSubmit={sendMessage} aria-label="chat-input">
          <input
            className="input-box"
            placeholder="Type a message..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            disabled={loading}
            autoComplete="off"
          />
          <button className="send-btn" type="submit" disabled={loading || input.trim().length === 0}>
            Send
          </button>
        </form>
      </div>
    </div>
  );
}
