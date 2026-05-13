"use client";
import { useState, useEffect } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000';

export default function LoginPage() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [passwordStrength, setPasswordStrength] = useState({ strength: '', valid: false, message: '' });
  const [rateLimitError, setRateLimitError] = useState('');
  const router = useRouter();
  const searchParams = useSearchParams();
  const isSignup = searchParams.get('mode') === 'signup';

  useEffect(() => {
    if (isSignup && password.length > 0) {
      checkPasswordStrength(password);
    } else {
      setPasswordStrength({ strength: '', valid: false, message: '' });
    }
  }, [password, isSignup]);

  const checkPasswordStrength = async (pwd: string) => {
    try {
      const res = await fetch(`${API_URL}/api/v1/auth/validate-password`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ password: pwd }),
      });
      if (res.ok) {
        const data = await res.json();
        setPasswordStrength(data);
      }
    } catch {}
  };

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setRateLimitError('');
    setLoading(true);

    try {
      const params = new URLSearchParams();
      params.append('username', username);
      params.append('password', password);

      const res = await fetch(`${API_URL}/api/v1/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: params,
      });

      if (res.status === 429) {
        const data = await res.json();
        const retryAfter = res.headers.get('Retry-After') || '60';
        setRateLimitError(`Too many attempts. Try again in ${retryAfter} seconds.`);
        setLoading(false);
        return;
      }

      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.detail || 'Login failed');
      }

      const data = await res.json();
      localStorage.setItem('access_token', data.access_token);
      localStorage.setItem('refresh_token', data.refresh_token);
      router.push('/chat');
    } catch (err) {
      setError((err as Error).message || 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  const handleSignup = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setRateLimitError('');
    setLoading(true);

    try {
      const res = await fetch(`${API_URL}/api/v1/auth/signup`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password }),
      });

      if (res.status === 429) {
        const data = await res.json();
        const retryAfter = res.headers.get('Retry-After') || '60';
        setRateLimitError(`Too many attempts. Try again in ${retryAfter} seconds.`);
        setLoading(false);
        return;
      }

      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.detail || 'Signup failed');
      }

      const data = await res.json();
      alert(`Welcome ${data.username}! Now login.`);
      router.push('/login');
    } catch (err) {
      setError((err as Error).message || 'Signup failed');
    } finally {
      setLoading(false);
    }
  };

  const getStrengthColor = () => {
    switch (passwordStrength.strength) {
      case 'weak': return '#ef4444';
      case 'medium': return '#f59e0b';
      case 'strong': return '#10b981';
      default: return '#e5e7eb';
    }
  };

  const getStrengthBar = () => {
    const widths = { weak: '33%', medium: '66%', strong: '100%' };
    return widths[passwordStrength.strength as keyof typeof widths] || '0%';
  };

  return (
    <div className="login-container">
      <div className="login-box">
        <h1>{isSignup ? 'Create Account' : 'Welcome Back'}</h1>
        <p className="subtitle">{isSignup ? 'Join Thinkspire and start exploring' : 'Sign in to continue thinking'}</p>

        {rateLimitError && (
          <div className="rate-limit-error">
            ⚠️ {rateLimitError}
          </div>
        )}

        <form onSubmit={isSignup ? handleSignup : handleLogin}>
          <div className="form-group">
            <label>Username</label>
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="Enter username"
              required
            />
          </div>

          <div className="form-group">
            <label>Password</label>
            <div className="password-input">
              <input
                type={showPassword ? 'text' : 'password'}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Enter password"
                required
              />
              <button type="button" className="toggle-password" onClick={() => setShowPassword(!showPassword)}>
                {showPassword ? '🙈' : '👁️'}
              </button>
            </div>

            {isSignup && password && (
              <div className="password-strength">
                <div className="strength-bar">
                  <div className="strength-fill" style={{ 
                    width: getStrengthBar(), 
                    backgroundColor: getStrengthColor() 
                  }}></div>
                </div>
                <span className="strength-label" style={{ color: getStrengthColor() }}>
                  {passwordStrength.strength ? `${passwordStrength.strength.charAt(0).toUpperCase() + passwordStrength.strength.slice(1)} password` : ''}
                </span>
                {passwordStrength.message && (
                  <span className="strength-hint">
                    {!passwordStrength.valid && passwordStrength.message}
                  </span>
                )}
              </div>
            )}
          </div>

          {error && <p className="error">{error}</p>}

          <button 
            type="submit" 
            disabled={loading || (isSignup && !passwordStrength.valid)} 
            className="submit-btn"
          >
            {loading ? (
              <span className="spinner"></span>
            ) : (
              isSignup ? 'Create Account' : 'Sign In'
            )}
          </button>
        </form>

        <p className="hint">
          {isSignup ? (
            <>Already have an account? <a href="/login">Sign In</a></>
          ) : (
            <>Don&apos;t have an account? <a href="/login?mode=signup">Create One</a></>
          )}
        </p>
      </div>

      <style jsx>{`
        .password-strength {
          margin-top: 12px;
        }
        .strength-bar {
          height: 3px;
          background: #e8e8e8;
          border-radius: 2px;
          overflow: hidden;
          margin-bottom: 6px;
        }
        .strength-fill {
          height: 100%;
          transition: width 0.3s ease, background-color 0.3s ease;
        }
        .strength-label {
          font-size: 12px;
          display: block;
          margin-bottom: 3px;
          font-weight: 500;
        }
        .strength-hint {
          font-size: 11px;
          color: #ef4444;
          display: block;
          margin-top: 3px;
        }
      `}</style>
    </div>
  );
}
