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
        <div className="logo">Think Inspire</div>
        <div className="nav-buttons">
          {isLoggedIn ? (
            <>
              <Link href="/chat" className="btn btn-primary">Ask Think</Link>
              <button onClick={logout} className="btn btn-outline">Logout</button>
            </>
          ) : (
            <>
              <Link href="/login" className="btn btn-outline">Login</Link>
              <Link href="/login?mode=signup" className="btn btn-primary">Sign Up</Link>
            </>
          )}
        </div>
      </nav>

      <main className="hero">
        <h1>Solve Problems with AI Assistance</h1>
        <p className="tagline">
          Your AI-powered problem-solving partner
        </p>
        
        <div className="features">
          <div className="feature">
            <span className="icon">🔍</span>
            <h3>Debug Together</h3>
            <p>Stuck on code or errors? Get guided help instantly</p>
          </div>
          <div className="feature">
            <span className="icon">💡</span>
            <h3>Solve It, Not Just Copy</h3>
            <p>Work through problems with hints, not answers</p>
          </div>
          <div className="feature">
            <span className="icon">📚</span>
            <h3>Learn by Doing</h3>
            <p>Practice problems to master concepts</p>
          </div>
        </div>

        <Link href="/login" className="cta-button">
          Start Solving
        </Link>

        <div className="how-it-works">
          <h2>How It Works</h2>
          <ol>
            <li><strong>Describe your problem</strong> - Paste code, error, or question</li>
            <li><strong>Get unstuck</strong> - Receive hints or explanations</li>
            <li><strong> Solve it yourself</strong> - Work through with AI guidance</li>
          </ol>
        </div>

        <div className="use-cases">
          <h2>What Can You Solve?</h2>
          <div className="use-case-grid">
            <div className="use-case">
              <span className="icon">🐛</span>
              <h4>Bug Debugging</h4>
              <p>Fix broken code</p>
            </div>
            <div className="use-case">
              <span className="icon">📝</span>
              <h4>Code Reviews</h4>
              <p>Improve your code</p>
            </div>
            <div className="use-case">
              <span className="icon">🤔</span>
              <h4>Concept Help</h4>
              <p>Understand anything</p>
            </div>
            <div className="use-case">
              <span className="icon">💻</span>
              <h4>Write Code</h4>
              <p>Get started</p>
            </div>
          </div>
        </div>
      </main>

      <footer className="footer">
        <p>© 2026 Think Inspire. Solve Harder.</p>
      </footer>
    </div>
  );
}