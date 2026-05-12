"use client";
import React, { useEffect, useRef, useState } from 'react';
import { useRouter } from 'next/navigation';

type Message = {
  id: string;
  from: 'user' | 'ai';
  text: string;
  time?: string;
};

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000';

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const scroller = useRef<HTMLDivElement | null>(null);
  const router = useRouter();

  const getToken = () => localStorage.getItem('access_token');
  const getRefresh = () => localStorage.getItem('refresh_token');

  const getTime = () => {
    const now = new Date();
    return now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

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
    }
  }, [router]);

  useEffect(() => {
    if (scroller.current) {
      scroller.current.scrollTop = scroller.current.scrollHeight;
    }
  }, [messages]);

  useEffect(() => {
    if (messages.length === 0) {
      setMessages([{ 
        id: 'welcome', 
        from: 'ai', 
        text: 'Welcome to Thinkspire! I&apos;m here to help you explore ideas and solve problems. What would you like to think about today?',
        time: getTime()
      }]);
    }
  }, []);

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
  };

  const sendMessage = async (e?: React.FormEvent) => {
    e?.preventDefault();
    const text = input.trim();
    if (!text) return;

    let token = getToken();
    if (!token) {
      router.push('/login');
      return;
    }

    const userMsg: Message = { 
      id: Date.now().toString(), 
      from: 'user', 
      text,
      time: getTime()
    };
    setMessages((m) => [...m, userMsg]);
    setInput('');
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
        
        if (!retryRes.ok) throw new Error('Request failed');
        
        const data = await retryRes.json();
        if (data.session_id) setSessionId(data.session_id);
        const aiMsg: Message = { 
          id: Date.now().toString(), 
          from: 'ai', 
          text: data.reply,
          time: getTime()
        };
        setMessages((m) => [...m, aiMsg]);
        setLoading(false);
        return;
      }

      if (!res.ok) throw new Error('Request failed');

      const data = await res.json();
      if (data.session_id) setSessionId(data.session_id);
      const aiMsg: Message = { 
        id: Date.now().toString(), 
        from: 'ai', 
        text: data.reply,
        time: getTime()
      };
      setMessages((m) => [...m, aiMsg]);
    } catch {
      setMessages((m) => [...m, { 
        id: Date.now().toString(), 
        from: 'ai', 
        text: '❌ Something went wrong. Please try again.',
        time: getTime()
      }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="chat-page">
      <header className="chat-header-bar">
        <h2>Thinkspire Chat</h2>
        <div className="header-actions">
          {sessionId && <span className="session-badge">Active Session</span>}
          <button onClick={logout} className="logout-btn">Sign Out</button>
        </div>
      </header>

      <div className="chat-wrapper">
        <div className="chat-container">
          <div className="message-area" ref={scroller}>
            {messages.map((m) => (
              <div key={m.id} className={`message ${m.from}`}>
                <div className="message-content">
                  <div className="bubble">{m.text}</div>
                  {m.time && <span className="timestamp">{m.time}</span>}
                </div>
                <button 
                  className="copy-btn" 
                  onClick={() => copyToClipboard(m.text)}
                  title="Copy"
                >
                  📋
                </button>
              </div>
            ))}
            {loading && (
              <div className="message ai">
                <div className="message-content">
                  <div className="bubble typing">
                    <span className="dot"></span>
                    <span className="dot"></span>
                    <span className="dot"></span>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>

        <form className="input-area" onSubmit={sendMessage}>
          <input
            className="input-box"
            placeholder="Share your thoughts..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            disabled={loading}
          />
          <button 
            className="send-btn" 
            type="submit" 
            disabled={loading || !input.trim()}
          >
            ➤
          </button>
        </form>
      </div>
    </div>
  );
}
