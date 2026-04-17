'use client';
import { useState } from 'react';
import { auth, setToken } from '@/lib/api';
import { useRouter } from 'next/navigation';

type Mode = 'login' | 'register-1' | 'register-2';

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

export default function LoginModal({ onClose }: { onClose?: () => void }) {
  const [mode, setMode] = useState<Mode>('login');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const router = useRouter();

  // Login fields
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');

  // Register step 1 — identity
  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');
  const [age, setAge] = useState('');
  const [phone, setPhone] = useState('');

  // Register step 2 — address + credentials
  const [address, setAddress] = useState('');
  const [city, setCity] = useState('');
  const [country, setCountry] = useState('');
  const [regEmail, setRegEmail] = useState('');
  const [regPassword, setRegPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');

  async function handleLogin(e: React.FormEvent) {
    e.preventDefault(); setError(''); setLoading(true);
    try {
      const res = await auth.login(email, password);
      setToken(res.access_token);
      onClose?.();
      router.push('/dashboard');
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Invalid credentials');
    } finally { setLoading(false); }
  }

  function handleStep1(e: React.FormEvent) {
    e.preventDefault(); setError('');
    if (!firstName || !lastName || !age) { setError('Please fill in all required fields.'); return; }
    if (Number(age) < 18) { setError('You must be at least 18 years old.'); return; }
    setMode('register-2');
  }

  async function handleStep2(e: React.FormEvent) {
    e.preventDefault(); setError(''); setLoading(true);
    if (regPassword !== confirmPassword) { setError('Passwords do not match.'); setLoading(false); return; }
    try {
      const res = await auth.register({
        email: regEmail, password: regPassword,
        first_name: firstName, last_name: lastName,
        age: Number(age), phone: phone || undefined,
        address: address || undefined, city: city || undefined, country: country || undefined,
      });
      setToken(res.access_token);
      onClose?.();
      router.push('/dashboard');
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Registration failed');
    } finally { setLoading(false); }
  }

  return (
    <div style={{
      position: 'fixed', inset: 0, background: 'rgba(14,15,18,0.6)',
      backdropFilter: 'blur(12px)', display: 'flex', alignItems: 'center',
      justifyContent: 'center', zIndex: 100, padding: 24,
    }}>
      <div style={{
        width: '100%', maxWidth: 520, background: 'var(--bg)', borderRadius: 20,
        padding: 40, boxShadow: '0 30px 80px rgba(0,0,0,0.3)',
        maxHeight: '90vh', overflowY: 'auto',
      }}>
        {/* Brand */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, fontWeight: 500, fontSize: 17 }}>
          <span style={{ width: 16, height: 16, borderRadius: '50%', background: 'var(--accent)', display: 'inline-block' }} />
          Veridian
        </div>

        {/* ── LOGIN ───────────────────────────────────────────────── */}
        {mode === 'login' && (
          <>
            <h2 style={{ fontSize: 32, fontWeight: 500, letterSpacing: '-0.02em', margin: '14px 0 8px' }}>Welcome back.</h2>
            <p style={{ color: 'var(--muted)', fontSize: 15, marginBottom: 4 }}>Sign in to continue.</p>
            <form onSubmit={handleLogin}>
              <Field label="Email"><input type="email" value={email} onChange={e => setEmail(e.target.value)} required style={inputStyle} /></Field>
              <Field label="Password"><input type="password" value={password} onChange={e => setPassword(e.target.value)} required style={inputStyle} /></Field>
              {error && <p style={{ color: 'var(--red)', fontFamily: 'Geist Mono', fontSize: 12, marginTop: 12 }}>{error}</p>}
              <button type="submit" disabled={loading} style={{ width: '100%', marginTop: 28, padding: 16, background: 'var(--ink)', color: '#fff', border: 0, borderRadius: 12, fontSize: 15, fontWeight: 500, cursor: 'pointer', opacity: loading ? 0.7 : 1 }}>
                {loading ? 'Signing in...' : 'Sign in & start trading'}
              </button>
            </form>
            <div style={{ textAlign: 'center', fontSize: 12, color: 'var(--muted)', marginTop: 20, fontFamily: 'Geist Mono' }}>
              No account?{' '}
              <button onClick={() => setMode('register-1')} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--ink)', textDecoration: 'underline', fontSize: 12, fontFamily: 'Geist Mono' }}>
                Create one
              </button>
            </div>
          </>
        )}

        {/* ── REGISTER STEP 1 — Identity ──────────────────────────── */}
        {mode === 'register-1' && (
          <>
            <h2 style={{ fontSize: 32, fontWeight: 500, letterSpacing: '-0.02em', margin: '14px 0 4px' }}>Create account.</h2>
            <p style={{ color: 'var(--muted)', fontSize: 14, marginBottom: 4 }}>Step 1 of 2 — Your identity</p>
            {/* Progress */}
            <div style={{ display: 'flex', gap: 6, marginBottom: 8 }}>
              <div style={{ flex: 1, height: 3, borderRadius: 2, background: 'var(--ink)' }} />
              <div style={{ flex: 1, height: 3, borderRadius: 2, background: 'var(--line)' }} />
            </div>
            <form onSubmit={handleStep1}>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
                <Field label="First name *"><input value={firstName} onChange={e => setFirstName(e.target.value)} required style={inputStyle} /></Field>
                <Field label="Last name *"><input value={lastName} onChange={e => setLastName(e.target.value)} required style={inputStyle} /></Field>
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
                <Field label="Age *"><input type="number" min={18} max={120} value={age} onChange={e => setAge(e.target.value)} required style={inputStyle} /></Field>
                <Field label="Phone"><input type="tel" value={phone} onChange={e => setPhone(e.target.value)} placeholder="+1 555 000 0000" style={inputStyle} /></Field>
              </div>
              {error && <p style={{ color: 'var(--red)', fontFamily: 'Geist Mono', fontSize: 12, marginTop: 12 }}>{error}</p>}
              <button type="submit" style={{ width: '100%', marginTop: 28, padding: 16, background: 'var(--ink)', color: '#fff', border: 0, borderRadius: 12, fontSize: 15, fontWeight: 500, cursor: 'pointer' }}>
                Continue →
              </button>
            </form>
            <div style={{ textAlign: 'center', fontSize: 12, color: 'var(--muted)', marginTop: 20, fontFamily: 'Geist Mono' }}>
              Already have an account?{' '}
              <button onClick={() => setMode('login')} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--ink)', textDecoration: 'underline', fontSize: 12, fontFamily: 'Geist Mono' }}>Sign in</button>
            </div>
          </>
        )}

        {/* ── REGISTER STEP 2 — Address + credentials ─────────────── */}
        {mode === 'register-2' && (
          <>
            <h2 style={{ fontSize: 32, fontWeight: 500, letterSpacing: '-0.02em', margin: '14px 0 4px' }}>Almost done.</h2>
            <p style={{ color: 'var(--muted)', fontSize: 14, marginBottom: 4 }}>Step 2 of 2 — Address & credentials</p>
            {/* Progress */}
            <div style={{ display: 'flex', gap: 6, marginBottom: 8 }}>
              <div style={{ flex: 1, height: 3, borderRadius: 2, background: 'var(--ink)' }} />
              <div style={{ flex: 1, height: 3, borderRadius: 2, background: 'var(--ink)' }} />
            </div>
            <form onSubmit={handleStep2}>
              <Field label="Address"><input value={address} onChange={e => setAddress(e.target.value)} placeholder="123 Main St" style={inputStyle} /></Field>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
                <Field label="City"><input value={city} onChange={e => setCity(e.target.value)} style={inputStyle} /></Field>
                <Field label="Country"><input value={country} onChange={e => setCountry(e.target.value)} style={inputStyle} /></Field>
              </div>
              <div style={{ marginTop: 20, paddingTop: 20, borderTop: '1px solid var(--line)' }}>
                <Field label="Email *"><input type="email" value={regEmail} onChange={e => setRegEmail(e.target.value)} required style={inputStyle} /></Field>
                <Field label="Password *"><input type="password" value={regPassword} onChange={e => setRegPassword(e.target.value)} required minLength={8} style={inputStyle} /></Field>
                <Field label="Confirm password *"><input type="password" value={confirmPassword} onChange={e => setConfirmPassword(e.target.value)} required style={inputStyle} /></Field>
              </div>
              {error && <p style={{ color: 'var(--red)', fontFamily: 'Geist Mono', fontSize: 12, marginTop: 12 }}>{error}</p>}
              <div style={{ display: 'flex', gap: 10, marginTop: 28 }}>
                <button type="button" onClick={() => { setMode('register-1'); setError(''); }} style={{ flex: 1, padding: 16, background: 'rgba(14,15,18,0.06)', color: 'var(--ink)', border: 0, borderRadius: 12, fontSize: 15, cursor: 'pointer' }}>
                  ← Back
                </button>
                <button type="submit" disabled={loading} style={{ flex: 2, padding: 16, background: 'var(--ink)', color: '#fff', border: 0, borderRadius: 12, fontSize: 15, fontWeight: 500, cursor: 'pointer', opacity: loading ? 0.7 : 1 }}>
                  {loading ? 'Creating account...' : 'Create account'}
                </button>
              </div>
            </form>
          </>
        )}
      </div>
    </div>
  );
}
