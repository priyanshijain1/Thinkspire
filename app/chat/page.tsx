"use client";
import React, { useEffect, useMemo, useRef, useState } from 'react';

type Message = {
  id: string;
  from: 'user' | 'ai';
  text: string;
};

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(false);
  const scroller = useRef<HTMLDivElement | null>(null);

  // Auto-scroll to bottom on new message
  useEffect(() => {
    if (scroller.current) {
      scroller.current.scrollTop = scroller.current.scrollHeight;
    }
  }, [messages.length]);

  const sendMessage = async (e?: React.FormEvent) => {
    e?.preventDefault();
    const text = input.trim();
    if (!text) return;
    const userMsg: Message = { id: Date.now().toString(), from: 'user', text };
    setMessages((m) => [...m, userMsg]);
    setInput('');
    setLoading(true);
    try {
      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text }),
      });
      const data = await res.json();
      const aiMsg: Message = { id: Date.now().toString(), from: 'ai', text: data.reply };
      setMessages((m) => [...m, aiMsg]);
    } catch (err) {
      const aiMsg: Message = { id: Date.now().toString(), from: 'ai', text: 'Error: could not reach AI service.' };
      setMessages((m) => [...m, aiMsg]);
    } finally {
      setLoading(false);
    }
  };

  // Simple initial greeting to demonstrate UI
  useEffect(() => {
    if (messages.length === 0) {
      // seed a friendly prompt from AI
      const welcome: Message = { id: 'welcome', from: 'ai', text: 'Hi there! How can I help you today?' };
      setMessages([welcome]);
    }
  }, []);

  const isInputDisabled = loading;

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
        </div>
        <form className="input-area" onSubmit={sendMessage} aria-label="chat-input">
          <input
            className="input-box"
            placeholder="Type a message..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            disabled={isInputDisabled}
            autoComplete="off"
          />
          <button className="send-btn" type="submit" disabled={isInputDisabled || input.trim().length === 0}>
            Send
          </button>
        </form>
      </div>
    </div>
  );
}
