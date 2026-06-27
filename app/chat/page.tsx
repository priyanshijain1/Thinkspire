"use client";
import React, { useEffect, useRef, useState, useCallback } from 'react';
import { useRouter } from 'next/navigation';

type Message = {
  id: string;
  from: 'user' | 'ai';
  text: string;
  time?: string;
  mode?: string;
};

type Session = {
  id: string;
  preview: string;
  time: string;
};

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000';
const STORAGE_KEY = 'thinkspire_chat_session';
const SESSIONS_KEY = 'thinkspire_sessions';

const SUGGESTIONS = [
  "Explain async/await in JavaScript",
  "What is Big O notation?",
  "Help me debug a Python error",
  "Practice problem: binary search",
];

function formatMarkdown(text: string): string {
  return text
    .replace(/```(\w*)\n([\s\S]*?)```/g, '<pre><code>$2</code></pre>')
    .replace(/`([^`]+)`/g, '<code>$1</code>')
    .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
    .replace(/\*([^*]+)\*/g, '<em>$1</em>')
    .replace(/^\s*[-*]\s+(.+)$/gm, '<li>$1</li>')
    .replace(/(<li>.*<\/li>)/s, '<ul>$1</ul>')
    .replace(/\n\n/g, '</p><p>')
    .replace(/^(.+)$/m, '<p>$1</p>')
    .replace(/<p></g, '<')
    .replace(/><\/p>/g, '>');
}

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [streamingText, setStreamingText] = useState<string>('');
  const [currentMode, setCurrentMode] = useState<string>('');
  const [sessions, setSessions] = useState<Session[]>([]);
  const scroller = useRef<HTMLDivElement | null>(null);
  const router = useRouter();
  const abortRef = useRef<AbortController | null>(null);

  const getToken = () => localStorage.getItem('access_token');
  const getRefresh = () => localStorage.getItem('refresh_token');

  const getTime = () => new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

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
    } catch { return null; }
  };

  const logout = async () => {
    const token = getToken();
    if (token) {
      try { await fetch(`${API_URL}/api/v1/auth/logout`, { method: 'POST', headers: { Authorization: `Bearer ${token}` } }); } catch {}
    }
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem(STORAGE_KEY);
    router.push('/login');
  };

  const loadSessions = useCallback(() => {
    try {
      const saved = localStorage.getItem(SESSIONS_KEY);
      if (saved) setSessions(JSON.parse(saved));
    } catch {}
  }, []);

  const saveSession = useCallback((sid: string, preview: string) => {
    setSessions(prev => {
      const exists = prev.find(s => s.id === sid);
      if (exists) return prev;
      const updated = [{ id: sid, preview: preview.slice(0, 40), time: getTime() }, ...prev].slice(0, 10);
      localStorage.setItem(SESSIONS_KEY, JSON.stringify(updated));
      return updated;
    });
  }, []);

  useEffect(() => {
    const token = getToken();
    if (!token) { router.push('/login'); return; }

    loadSessions();
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved) {
      try {
        const data = JSON.parse(saved);
        if (data.messages?.length > 0) {
          setMessages(data.messages);
          setSessionId(data.sessionId || null);
          return;
        }
      } catch {}
    }
    setMessages([{ id: 'welcome', from: 'ai', text: "Welcome to Thinkspire! What would you like to explore today?", time: getTime() }]);
  }, [router, loadSessions]);

  useEffect(() => {
    if (messages.length > 0) localStorage.setItem(STORAGE_KEY, JSON.stringify({ messages, sessionId }));
  }, [messages, sessionId]);

  useEffect(() => {
    if (scroller.current) scroller.current.scrollTop = scroller.current.scrollHeight;
  }, [messages, streamingText]);

  const copyToClipboard = (text: string) => navigator.clipboard.writeText(text);

  const streamMessage = async (text: string, token: string, sid: string | null): Promise<void> => {
    const controller = new AbortController();
    abortRef.current = controller;
    const aiMsgId = Date.now().toString() + '-ai';
    setStreamingText('');
    let finalized = false;

    try {
      const res = await fetch(`${API_URL}/api/v1/chat/stream`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify({ message: text, session_id: sid }),
        signal: controller.signal,
      });

      if (res.status === 401) {
        const newToken = await refreshAccessToken();
        if (!newToken) { router.push('/login'); return; }
        return streamMessage(text, newToken, sid);
      }
      if (!res.ok || !res.body) throw new Error('Stream failed');

      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';
      let fullText = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (!line.startsWith('data: ')) continue;
          try {
            const data = JSON.parse(line.slice(6));
            if (data.type === 'meta') {
              if (data.session_id) { setSessionId(data.session_id); saveSession(data.session_id, text); }
              if (data.teaching_mode) setCurrentMode(data.teaching_mode);
            } else if (data.type === 'token') {
              fullText += data.content;
              setStreamingText(fullText);
            } else if (data.type === 'done') {
              finalized = true;
              setMessages(m => [...m, { id: aiMsgId, from: 'ai', text: fullText, time: getTime(), mode: currentMode || undefined }]);
              setStreamingText('');
            } else if (data.type === 'error') {
              throw new Error(data.content || 'AI error');
            }
          } catch (e) { if (e instanceof SyntaxError) continue; throw e; }
        }
      }

      if (fullText && !finalized) {
        setMessages(m => [...m, { id: aiMsgId, from: 'ai', text: fullText, time: getTime() }]);
        setStreamingText('');
      }
    } finally {
      abortRef.current = null;
    }
  };

  const sendMessage = async (msgText?: string) => {
    const text = (msgText || input).trim();
    if (!text || loading) return;

    let token = getToken();
    if (!token) { router.push('/login'); return; }

    setMessages(m => [...m, { id: Date.now().toString() + '-user', from: 'user', text, time: getTime() }]);
    setInput('');
    setLoading(true);

    try {
      await streamMessage(text, token, sessionId);
    } catch {
      setStreamingText('');
      setMessages(m => [...m, { id: Date.now().toString() + '-err', from: 'ai', text: 'Something went wrong. Please try again.', time: getTime() }]);
    } finally {
      setLoading(false);
    }
  };

  const stopStreaming = () => {
    if (abortRef.current) {
      abortRef.current.abort();
      abortRef.current = null;
      setLoading(false);
      if (streamingText) {
        setMessages(m => [...m, { id: Date.now().toString() + '-stopped', from: 'ai', text: streamingText, time: getTime() }]);
        setStreamingText('');
      }
    }
  };

  const newChat = () => {
    setMessages([{ id: 'welcome', from: 'ai', text: "New session started. What would you like to explore?", time: getTime() }]);
    setSessionId(null);
    setCurrentMode('');
    localStorage.removeItem(STORAGE_KEY);
  };

  const modeClass = currentMode ? currentMode.toLowerCase() : '';

  return (
    <div className="chat-page">
      {/* Sidebar */}
      <aside className="chat-sidebar">
        <div className="sidebar-header">
          <span className="sidebar-logo">Thinkspire</span>
          <button className="sidebar-new-btn" onClick={newChat}>+ New</button>
        </div>
        <div className="sidebar-session-list">
          {sessions.length === 0 ? (
            <div style={{ padding: '16px 12px', fontSize: '12px', color: 'var(--muted)' }}>No saved sessions yet</div>
          ) : (
            sessions.map(s => (
              <div
                key={s.id}
                className={`sidebar-session ${s.id === sessionId ? 'active' : ''}`}
                onClick={() => { setSessionId(s.id); router.push('/chat'); }}
              >
                {s.preview}
              </div>
            ))
          )}
        </div>
        <div className="sidebar-footer">
          <button className="sidebar-logout" onClick={logout}>Sign Out</button>
        </div>
      </aside>

      {/* Main chat */}
      <div className="chat-main">
        <header className="chat-header-bar">
          <h2>Chat</h2>
          <div className="header-actions">
            {currentMode && <span className={`mode-badge ${modeClass}`}>{currentMode}</span>}
            {sessionId && <span className="session-badge">Active</span>}
          </div>
        </header>

        <div className="chat-wrapper">
          <div className="chat-container">
            <div className="message-area" ref={scroller}>
              {messages.length <= 1 && !loading && !streamingText && (
                <div className="chat-empty">
                  <div className="chat-empty-icon">💡</div>
                  <h3>Start your learning journey</h3>
                  <p>Ask anything - I adapt to your level</p>
                  <div className="chat-suggestions">
                    {SUGGESTIONS.map(s => (
                      <button key={s} className="chat-suggestion" onClick={() => sendMessage(s)}>{s}</button>
                    ))}
                  </div>
                </div>
              )}

              {messages.map(m => (
                <div key={m.id} className={`message ${m.from}`}>
                  <div className="message-avatar">{m.from === 'user' ? 'U' : 'AI'}</div>
                  <div className="message-body">
                    {m.mode && <span className={`mode-badge ${m.mode.toLowerCase()}`} style={{ marginBottom: '4px', display: 'inline-block' }}>{m.mode}</span>}
                    {m.from === 'ai' ? (
                      <div className="bubble" dangerouslySetInnerHTML={{ __html: formatMarkdown(m.text) }} />
                    ) : (
                      <div className="bubble">{m.text}</div>
                    )}
                    {m.time && <span className="timestamp">{m.time}</span>}
                    <button className="copy-btn" onClick={() => copyToClipboard(m.text)} title="Copy">📋</button>
                  </div>
                </div>
              ))}

              {streamingText && (
                <div className="message ai">
                  <div className="message-avatar">AI</div>
                  <div className="message-body">
                    <div className="bubble" dangerouslySetInnerHTML={{ __html: formatMarkdown(streamingText) + '<span class="streaming-cursor"></span>' }} />
                  </div>
                </div>
              )}

              {loading && !streamingText && (
                <div className="message ai">
                  <div className="message-avatar">AI</div>
                  <div className="message-body">
                    <div className="bubble">
                      <div className="typing">
                        <span className="dot"></span>
                        <span className="dot"></span>
                        <span className="dot"></span>
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>

          <form className="input-area" onSubmit={e => { e.preventDefault(); sendMessage(); }}>
            <input
              className="input-box"
              placeholder="Share your thoughts..."
              value={input}
              onChange={e => setInput(e.target.value)}
              disabled={loading}
              autoComplete="off"
            />
            {loading ? (
              <button type="button" className="stop-btn" onClick={stopStreaming} title="Stop">■</button>
            ) : (
              <button className="send-btn" type="submit" disabled={!input.trim()}>➤</button>
            )}
          </form>
        </div>
      </div>
    </div>
  );
}
