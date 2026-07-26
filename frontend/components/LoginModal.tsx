'use client';
import { useEffect, useState } from 'react';
import { auth, setToken, isLoggedIn } from '@/lib/api';
import { useRouter } from 'next/navigation';

const inputStyle = {
  width: '100%', padding: '13px 16px', fontSize: 15,
  background: '#fff', border: '1px solid var(--line)', borderRadius: 10,
  fontFamily: 'inherit', outline: 'none', letterSpacing: '-0.005em',
} as const;

const labelStyle = {
  display: 'block', fontFamily: 'Geist Mono', fontSize: 11,
  letterSpacing: '0.1em', textTransform: 'uppercase' as const,
  color: 'var(--muted)', marginBottom: 8, marginTop: 16,
};

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return <div><label style={labelStyle}>{label}</label>{children}</div>;
}

export default function LoginModal() {
  const router = useRouter();
  const [setupMode, setSetupMode] = useState(false); // true = first-run owner creation
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirm, setConfirm] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (isLoggedIn()) { router.replace('/dashboard'); return; }
    // Offer account creation only if this instance has no owner yet.
    auth.setupNeeded()
      .then(r => setSetupMode(r.setup_needed))
      .catch(() => setSetupMode(false));
  }, [router]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(''); setLoading(true);
    try {
      if (setupMode) {
        if (password.length < 8) { setError('Password must be at least 8 characters.'); setLoading(false); return; }
        if (password !== confirm) { setError('Passwords do not match.'); setLoading(false); return; }
        const res = await auth.register(email, password);
        setToken(res.access_token);
      } else {
        const res = await auth.login(email, password);
        setToken(res.access_token);
      }
      router.push('/dashboard');
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : setupMode ? 'Could not create account' : 'Invalid credentials');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', background: 'var(--bg)', padding: 24 }}>
      <div style={{ width: '100%', maxWidth: 420 }}>
        {/* Brand */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, fontWeight: 500, fontSize: 17, marginBottom: 8 }}>
          <span style={{ width: 16, height: 16, borderRadius: '50%', background: 'var(--accent)', display: 'inline-block' }} />
          Veridian
        </div>

        <h2 style={{ fontSize: 34, fontWeight: 500, letterSpacing: '-0.02em', margin: '18px 0 8px' }}>
          {setupMode ? <>Set up your <span className="serif">cockpit.</span></> : <>Welcome <span className="serif">back.</span></>}
        </h2>
        <p style={{ color: 'var(--muted)', fontSize: 15, margin: 0 }}>
          {setupMode ? 'Create the owner account for this instance.' : 'Sign in to your trading dashboard.'}
        </p>

        <form onSubmit={handleSubmit}>
          <Field label="Email">
            <input type="email" value={email} onChange={e => setEmail(e.target.value)} required autoComplete="email" style={inputStyle} />
          </Field>
          <Field label="Password">
            <input type="password" value={password} onChange={e => setPassword(e.target.value)} required
              minLength={setupMode ? 8 : undefined}
              autoComplete={setupMode ? 'new-password' : 'current-password'} style={inputStyle} />
          </Field>
          {setupMode && (
            <Field label="Confirm password">
              <input type="password" value={confirm} onChange={e => setConfirm(e.target.value)} required autoComplete="new-password" style={inputStyle} />
            </Field>
          )}
          {error && <p style={{ color: 'var(--red)', fontFamily: 'Geist Mono', fontSize: 12, marginTop: 14 }}>{error}</p>}
          <button type="submit" disabled={loading} style={{ width: '100%', marginTop: 28, padding: 16, background: 'var(--ink)', color: '#fff', border: 0, borderRadius: 12, fontSize: 15, fontWeight: 500, cursor: 'pointer', opacity: loading ? 0.7 : 1 }}>
            {loading ? (setupMode ? 'Creating…' : 'Signing in…') : (setupMode ? 'Create account & continue' : 'Sign in')}
          </button>
        </form>
      </div>
    </div>
  );
}
