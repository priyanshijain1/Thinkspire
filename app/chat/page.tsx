"use client";
import React, { useEffect, useRef, useState } from 'react';
import { useRouter } from 'next/navigation';

type Message = {
  id: string;
  from: 'user' | 'ai';
  text: string;
};

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000';

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const scroller = useRef<HTMLDivElement | null>(null);
  const router = useRouter();

  const getToken = () => localStorage.getItem('access_token');
  const getRefresh = () => localStorage.getItem('refresh_token');

  const refreshAccessToken = async () => {
    const refresh = getRefresh();
    if (!refresh) return null;
    
    try {
      const res = await fetch(`${API_URL}/api/v1/auth/refresh`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh_token: refresh }),
      });
      
      if (!res.ok) return null;
      
      const data = await res.json();
      localStorage.setItem('access_token', data.access_token);
      localStorage.setItem('refresh_token', data.refresh_token);
      return data.access_token;
    } catch {
      return null;
    }
  };

  const logout = async () => {
    const token = getToken();
    if (token) {
      try {
        await fetch(`${API_URL}/api/v1/auth/logout`, {
          method: 'POST',
          headers: { 'Authorization': `Bearer ${token}` },
        });
      } catch {}
    }
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    router.push('/login');
  };

  useEffect(() => {
    const token = getToken();
    if (!token) {
      router.push('/login');
      return;
    }
    if (scroller.current) scroller.current.scrollTop = scroller.current.scrollHeight;
  }, [router]);

  useEffect(() => {
    if (messages.length === 0) {
      setMessages([{ id: 'welcome', from: 'ai', text: 'Hi! Describe your problem - let\'s solve it together.' }]);
    }
  }, []);

  const sendMessage = async (e?: React.FormEvent) => {
    e?.preventDefault();
    const text = input.trim();
    if (!text) return;

    let token = getToken();
    if (!token) {
      router.push('/login');
      return;
    }

    const userMsg: Message = { id: Date.now().toString(), from: 'user', text };
    setMessages((m) => [...m, userMsg]);
    setInput('');
    setError(null);
    setLoading(true);

    try {
      const res = await fetch(`${API_URL}/api/v1/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({ message: text, session_id: sessionId }),
      });

      // Token expired - try refresh
      if (res.status === 401) {
        token = await refreshAccessToken();
        if (!token) {
          router.push('/login');
          return;
        }
        
        const retryRes = await fetch(`${API_URL}/api/v1/chat`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`,
          },
          body: JSON.stringify({ message: text, session_id: sessionId }),
        });
        
        if (!retryRes.ok) {
          throw new Error('Request failed');
        }
        
        const data = await retryRes.json();
        if (data.session_id) setSessionId(data.session_id);
        const aiMsg: Message = { id: Date.now().toString(), from: 'ai', text: data.reply };
        setMessages((m) => [...m, aiMsg]);
        setLoading(false);
        return;
      }

      if (!res.ok) {
        throw new Error('Request failed');
      }

      const data = await res.json();
      if (data.session_id) setSessionId(data.session_id);
      const aiMsg: Message = { id: Date.now().toString(), from: 'ai', text: data.reply };
      setMessages((m) => [...m, aiMsg]);
    } catch (err) {
      const errMsg = (err as Error)?.message ?? 'Unknown error';
      setError(errMsg);
      setMessages((m) => [...m, { id: Date.now().toString(), from: 'ai', text: `Error: ${errMsg}` }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container" style={{ paddingTop: 20, paddingBottom: 20 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 }}>
        <h2>Ask Think</h2>
        <button onClick={logout} style={{ padding: '8px 16px' }}>Logout</button>
      </div>
      <div className="chat-container" style={{ height: '70vh' }}>
        <div className="message-area" ref={scroller} aria-label="messages">
          {messages.map((m) => (
            <div key={m.id} className={`message ${m.from}`}>
              <div className="bubble">{m.text}</div>
            </div>
          ))}
          {loading && (
            <div className="message ai">
              <div className="bubble">Thinking...</div>
            </div>
          )}
        </div>
        <form className="input-area" onSubmit={sendMessage}>
          <input
            className="input-box"
            placeholder="Describe your problem..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            disabled={loading}
          />
          <button className="send-btn" type="submit" disabled={loading || !input.trim()}>
            Send
          </button>
        </form>
      </div>
    </div>
  );
}