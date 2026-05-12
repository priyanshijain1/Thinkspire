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
        <div className="nav-menu">
          <a href="#features" className="nav-link">Features</a>
          <a href="#how-it-works" className="nav-link">How It Works</a>
          <a href="#usecases" className="nav-link">Use Cases</a>
          <a href="#contact" className="nav-link">Contact</a>
        </div>
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

      <section className="features-section" id="features">
        <h2>Why Choose Thinkspire?</h2>
        <div className="features-grid">
          <div className="feature-card">
            <div className="feature-icon">⚡</div>
            <h3>Instant Breakthroughs</h3>
            <p>Stop being stuck. Get sharp, intelligent analysis and fresh perspectives on your toughest challenges in seconds, not hours</p>
          </div>
          <div className="feature-card">
            <div className="feature-icon">🧠</div>
            <h3>Intelligent Collaboration</h3>
            <p>Work through complex problems with an AI partner that understands context, asks the right questions, and guides you toward solutions</p>
          </div>
          <div className="feature-card">
            <div className="feature-icon">🎯</div>
            <h3>Solutions That Stick</h3>
            <p>Build lasting understanding and real confidence through deep exploration, not quick fixes. Get insights you can actually implement</p>
          </div>
        </div>
      </section>

      <section className="how-it-works-section" id="how-it-works">
        <div className="how-it-content">
          <h2>How Thinkspire Works</h2>
          <div className="steps">
            <div className="step">
              <div className="step-number">1</div>
              <h4>Share Your Thoughts</h4>
              <p>Describe the challenge, question, or idea you&apos;re working on. The more detail you provide, the better insights we can offer you.</p>
            </div>
            <div className="step">
              <div className="step-number">2</div>
              <h4>Receive Expert Analysis</h4>
              <p>Get instant, thoughtful analysis with structured frameworks, proven methodologies, and fresh perspectives you haven&apos;t considered.</p>
            </div>
            <div className="step">
              <div className="step-number">3</div>
              <h4>Explore & Refine</h4>
              <p>Dig deeper through natural conversation. Ask follow-up questions, explore alternatives, and develop solutions with confidence and clarity.</p>
            </div>
          </div>
        </div>
        <div className="how-it-image">
          <Image
            src="/collaboration-ui.jpg"
            alt="Thinkspire intelligent chat interface showing AI collaboration"
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
            alt="Mind expanding with brilliant ideas and innovation"
            width={550}
            height={400}
            className="showcase-img"
          />
        </div>
        <div className="showcase-content">
          <h2>Unlock Your Full Thinking Potential</h2>
          <p>Thinkspire fundamentally transforms how you approach complex challenges. Whether you&apos;re architecting business strategy, uncovering hidden patterns in data, advancing research frontiers, or building the next generation of products, our intelligent AI partner empowers you to think deeper, analyze faster, and solve smarter than ever before.</p>
          <ul className="benefits-list">
            <li>Real-time collaboration with contextual AI insights</li>
            <li>Proven thinking frameworks and methodologies</li>
            <li>Deep exploration across any industry or domain</li>
            <li>Actionable, implementable solutions backed by analysis</li>
            <li>Continuous learning through every conversation</li>
          </ul>
          <Link href="/login" className="cta-button secondary">
            Explore All Features
          </Link>
        </div>
      </section>

      <section className="use-cases-section" id="usecases">
        <h2>Perfect For Every Field</h2>
        <div className="use-case-grid">
          <div className="use-case-card">
            <span className="use-case-icon">💼</span>
            <h4>Business Strategy</h4>
            <p>Navigate market complexity with intelligent analysis, competitive intelligence, and strategic decision-making support</p>
          </div>
          <div className="use-case-card">
            <span className="use-case-icon">📊</span>
            <h4>Data Science</h4>
            <p>Extract meaningful patterns, uncover hidden insights, and build data-driven strategies with AI guidance</p>
          </div>
          <div className="use-case-card">
            <span className="use-case-icon">🔬</span>
            <h4>Research & Development</h4>
            <p>Accelerate discovery, explore new frontiers, and transform research insights into breakthrough innovations</p>
          </div>
          <div className="use-case-card">
            <span className="use-case-icon">💡</span>
            <h4>Product Innovation</h4>
            <p>Design solutions that matter, solve customer problems creatively, and bring breakthrough products to life</p>
          </div>
        </div>
      </section>

      <section className="cta-final" id="contact">
        <h2>Ready to Think Bolder?</h2>
        <p>Join thousands of professionals, entrepreneurs, and innovators transforming how they approach challenges and achieve breakthrough results</p>
        <Link href="/login" className="cta-button primary-large">
          Start Your Free Journey
        </Link>
      </section>

      <footer className="footer">
        <p>© 2026 Thinkspire. Think Deeper. Solve Faster.</p>
      </footer>
    </div>
  );
}
