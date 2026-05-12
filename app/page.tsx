"use client";
import Link from 'next/link';
import Image from 'next/image';
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

      <main className="hero-section">
        <div className="hero-content">
          <h1>Think <span>Bolder</span>,<br />Solve <span>Faster</span></h1>
          <p className="tagline">
            Your AI-powered thinking partner for breakthrough ideas. Explore complex problems with intelligent guidance and unlock solutions you never thought possible.
          </p>
          <Link href="/login" className="cta-button">
            Start Exploring
          </Link>
        </div>
        <div className="hero-image">
          <Image
            src="/hero-illustration.jpg"
            alt="Collaborative thinking and AI partnership"
            width={600}
            height={500}
            priority
            className="hero-img"
          />
        </div>
      </main>

      <section className="features-section">
        <h2>Why Choose Thinkspire?</h2>
        <div className="features-grid">
          <div className="feature-card">
            <div className="feature-icon">⚡</div>
            <h3>Instant Breakthroughs</h3>
            <p>Get sharp analysis and fresh perspectives on your toughest challenges in seconds</p>
          </div>
          <div className="feature-card">
            <div className="feature-icon">🧠</div>
            <h3>Collaborative Thinking</h3>
            <p>Work through problems with intelligent guidance tailored to your unique needs</p>
          </div>
          <div className="feature-card">
            <div className="feature-icon">🎯</div>
            <h3>Solutions That Stick</h3>
            <p>Build real understanding and confidence through deep exploration and learning</p>
          </div>
        </div>
      </section>

      <section className="how-it-works-section">
        <div className="how-it-content">
          <h2>How Thinkspire Works</h2>
          <div className="steps">
            <div className="step">
              <div className="step-number">1</div>
              <h4>Share Your Ideas</h4>
              <p>Describe the problem or concept you&apos;re exploring in your own words</p>
            </div>
            <div className="step">
              <div className="step-number">2</div>
              <h4>Get Intelligent Guidance</h4>
              <p>Receive thoughtful analysis, structured frameworks, and fresh perspectives instantly</p>
            </div>
            <div className="step">
              <div className="step-number">3</div>
              <h4>Build Deep Understanding</h4>
              <p>Continue the conversation to explore deeper and develop lasting solutions</p>
            </div>
          </div>
        </div>
        <div className="how-it-image">
          <Image
            src="/collaboration-ui.jpg"
            alt="Thinkspire chat interface"
            width={550}
            height={450}
            className="how-img"
          />
        </div>
      </section>

      <section className="showcase-section">
        <div className="showcase-image">
          <Image
            src="/thinking-concept.jpg"
            alt="Mind expanding with ideas"
            width={550}
            height={400}
            className="showcase-img"
          />
        </div>
        <div className="showcase-content">
          <h2>Unlock Your Full Thinking Potential</h2>
          <p>Thinkspire transforms how you approach complex challenges. Whether you&apos;re developing business strategy, analyzing data, conducting research, or innovating products, our AI partner helps you think deeper and solve smarter.</p>
          <ul className="benefits-list">
            <li>Real-time collaboration with AI insights</li>
            <li>Structured thinking frameworks</li>
            <li>Deep exploration across any domain</li>
            <li>Actionable solutions you can implement</li>
          </ul>
          <Link href="/login" className="cta-button secondary">
            Explore Features
          </Link>
        </div>
      </section>

      <section className="use-cases-section">
        <h2>Perfect For Every Field</h2>
        <div className="use-case-grid">
          <div className="use-case-card">
            <span className="use-case-icon">💼</span>
            <h4>Business Strategy</h4>
            <p>Market analysis, competitive intelligence, and strategic planning</p>
          </div>
          <div className="use-case-card">
            <span className="use-case-icon">📊</span>
            <h4>Data Science</h4>
            <p>Complex analytics, pattern recognition, and data-driven insights</p>
          </div>
          <div className="use-case-card">
            <span className="use-case-icon">🔬</span>
            <h4>Research & Development</h4>
            <p>Deep exploration, discovery, and innovation acceleration</p>
          </div>
          <div className="use-case-card">
            <span className="use-case-icon">💡</span>
            <h4>Product Innovation</h4>
            <p>Creative problem-solving and breakthrough solution design</p>
          </div>
        </div>
      </section>

      <section className="cta-final">
        <h2>Ready to Think Bolder?</h2>
        <p>Join thousands of professionals and innovators transforming how they solve problems</p>
        <Link href="/login" className="cta-button primary-large">
          Get Started Free
        </Link>
      </section>

      <footer className="footer">
        <p>© 2026 Thinkspire. Think Deeper. Solve Faster.</p>
      </footer>
    </div>
  );
}
