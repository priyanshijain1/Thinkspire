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
        <h1>Think Deeper, Solve Smarter</h1>
        <p className="tagline">
          Your AI-powered thinking partner for collaborative problem-solving
        </p>
        
        <div className="features">
          <div className="feature">
            <span className="icon">✨</span>
            <h3>Instant Insights</h3>
            <p>Get thoughtful analysis and perspective on complex problems</p>
          </div>
          <div className="feature">
            <span className="icon">🎯</span>
            <h3>Guided Thinking</h3>
            <p>Work through challenges with intelligent step-by-step guidance</p>
          </div>
          <div className="feature">
            <span className="icon">🚀</span>
            <h3>Learn & Grow</h3>
            <p>Develop deeper understanding through collaborative exploration</p>
          </div>
        </div>

        <Link href="/login" className="cta-button">
          Begin Your Journey
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
          <h2>What Can You Explore?</h2>
          <div className="use-case-grid">
            <div className="use-case">
              <span className="icon">💼</span>
              <h4>Business Strategy</h4>
              <p>Strategic planning</p>
            </div>
            <div className="use-case">
              <span className="icon">📊</span>
              <h4>Data Analysis</h4>
              <p>Insights & trends</p>
            </div>
            <div className="use-case">
              <span className="icon">🔬</span>
              <h4>Research</h4>
              <p>Deep exploration</p>
            </div>
            <div className="use-case">
              <span className="icon">💡</span>
              <h4>Innovation</h4>
              <p>Creative solutions</p>
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
