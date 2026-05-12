"use client";
import Link from 'next/link';
import { useState, useEffect } from 'react';

export default function LandingPage() {
  const [isLoggedIn, setIsLoggedIn] = useState(false);

  useEffect(() => {
    const token = localStorage.getItem('auth_token');
    setIsLoggedIn(!!token);
  }, []);

  const logout = () => {
    localStorage.removeItem('auth_token');
    setIsLoggedIn(false);
  };

  return (
    <div className="landing">
      <nav className="navbar">
        <div className="logo">Thinkspire</div>
        <div className="nav-buttons">
          {isLoggedIn ? (
            <>
              <Link href="/chat" className="btn btn-primary">Start Thinking</Link>
              <button onClick={logout} className="btn btn-outline">Logout</button>
            </>
          ) : (
            <>
              <Link href="/login" className="btn btn-outline">Log In</Link>
              <Link href="/login?mode=signup" className="btn btn-primary">Get Started</Link>
            </>
          )}
        </div>
      </nav>

      <main className="hero">
        <h1>Think <span>Bolder</span>,<br />Solve <span>Faster</span></h1>
        <p className="tagline">
          Your AI-powered thinking partner for breakthrough ideas. Explore complex problems with intelligent guidance and unlock solutions you never thought possible.
        </p>
        
        <div className="features">
          <div className="feature">
            <span className="icon">⚡</span>
            <h3>Instant Breakthroughs</h3>
            <p>Get sharp analysis and fresh perspectives on your toughest challenges</p>
          </div>
          <div className="feature">
            <span className="icon">🧠</span>
            <h3>Collaborative Thinking</h3>
            <p>Work through problems with intelligent guidance every step of the way</p>
          </div>
          <div className="feature">
            <span className="icon">🎯</span>
            <h3>Solutions That Stick</h3>
            <p>Build real understanding and confidence through deep exploration</p>
          </div>
        </div>

        <Link href="/login" className="cta-button">
          Start Exploring
        </Link>

        <div className="how-it-works">
          <h2>How It Works</h2>
          <ol>
            <li><strong>Share your thoughts</strong> - Describe the problem or idea you&apos;re exploring</li>
            <li><strong>Receive guidance</strong> - Get intelligent insights and structured thinking</li>
            <li><strong>Explore deeper</strong> - Continue the conversation to build understanding</li>
          </ol>
        </div>

        <div className="use-cases">
          <h2>Solve Across Any Domain</h2>
          <div className="use-case-grid">
            <div className="use-case">
              <span className="icon">💼</span>
              <h4>Business Strategy</h4>
              <p>Market analysis & planning</p>
            </div>
            <div className="use-case">
              <span className="icon">📊</span>
              <h4>Data Science</h4>
              <p>Complex analytics & insights</p>
            </div>
            <div className="use-case">
              <span className="icon">🔬</span>
              <h4>Research & Development</h4>
              <p>Deep exploration & discovery</p>
            </div>
            <div className="use-case">
              <span className="icon">💡</span>
              <h4>Product Innovation</h4>
              <p>Creative problem-solving</p>
            </div>
          </div>
        </div>
      </main>

      <footer className="footer">
        <p>© 2026 Thinkspire. Think Deeper.</p>
      </footer>
    </div>
  );
}
