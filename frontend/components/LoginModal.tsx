'use client';
import { useState } from 'react';
import { auth, setToken } from '@/lib/api';
import { useRouter } from 'next/navigation';

export default function LoginModal({ onClose }: { onClose?: () => void }) {
  const [mode, setMode] = useState<'login' | 'register'>('login');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const router = useRouter();

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setError(''); setLoading(true);
    try {
      const res = mode === 'login'
        ? await auth.login(email, password)
        : await auth.register(email, password);
      setToken(res.access_token);
      onClose?.();
      router.push('/dashboard');
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Something went wrong');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div style={{
      position: 'fixed', inset: 0,
      background: 'rgba(14,15,18,0.6)',
      backdropFilter: 'blur(12px)',
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      zIndex: 100,
    }}>
      <div style={{
        width: 520, background: 'var(--bg)', borderRadius: 20, padding: 40,
        boxShadow: '0 30px 80px rgba(0,0,0,0.3)',
      }}>
        {/* Brand */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, fontWeight: 500, fontSize: 17 }}>
          <span style={{ width: 16, height: 16, borderRadius: '50%', background: 'var(--accent)', display: 'inline-block' }} />
          Veridian
        </div>

        <h2 style={{ fontSize: 32, fontWeight: 500, letterSpacing: '-0.02em', margin: '14px 0 8px' }}>
          {mode === 'login' ? 'Welcome back.' : 'Create account.'}
        </h2>
        <p style={{ color: 'var(--muted)', fontSize: 15, marginBottom: 26 }}>
          {mode === 'login'
            ? 'Sign in to continue. Your bot has been running while you were away.'
            : 'Start trading in minutes with your Binance account.'}
        </p>

        <form onSubmit={submit}>
          <label style={{ display: 'block', fontFamily: 'Geist Mono', fontSize: 11, letterSpacing: '0.1em', textTransform: 'uppercase', color: 'var(--muted)', marginBottom: 8 }}>Email</label>
          <input
            type="email" value={email} onChange={e => setEmail(e.target.value)} required
            style={{ width: '100%', padding: '14px 16px', fontSize: 15, background: '#fff', border: '1px solid var(--line)', borderRadius: 10, fontFamily: 'inherit', outline: 'none' }}
          />

          <label style={{ display: 'block', fontFamily: 'Geist Mono', fontSize: 11, letterSpacing: '0.1em', textTransform: 'uppercase', color: 'var(--muted)', marginBottom: 8, marginTop: 18 }}>Password</label>
          <input
            type="password" value={password} onChange={e => setPassword(e.target.value)} required
            style={{ width: '100%', padding: '14px 16px', fontSize: 15, background: '#fff', border: '1px solid var(--line)', borderRadius: 10, fontFamily: 'inherit', outline: 'none' }}
          />

          {error && <p style={{ color: 'var(--red)', fontSize: 13, fontFamily: 'Geist Mono', marginTop: 12 }}>{error}</p>}

          <button
            type="submit" disabled={loading}
            style={{
              width: '100%', marginTop: 28, padding: 16, background: 'var(--ink)', color: '#fff',
              border: 0, borderRadius: 12, fontSize: 15, fontWeight: 500, cursor: 'pointer',
              opacity: loading ? 0.7 : 1,
            }}>
            {loading ? 'Loading...' : mode === 'login' ? 'Sign in & start trading' : 'Create account'}
          </button>
        </form>

        <div style={{ textAlign: 'center', fontSize: 12, color: 'var(--muted)', marginTop: 22, fontFamily: 'Geist Mono' }}>
          {mode === 'login'
            ? <span>No account? <button onClick={() => setMode('register')} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--ink)', textDecoration: 'underline', fontSize: 12, fontFamily: 'Geist Mono' }}>Create one</button></span>
            : <span>Already have an account? <button onClick={() => setMode('login')} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--ink)', textDecoration: 'underline', fontSize: 12, fontFamily: 'Geist Mono' }}>Sign in</button></span>
          }
        </div>
      </div>
    </div>
  );
}
