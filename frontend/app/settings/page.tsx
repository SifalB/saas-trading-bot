'use client';
import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import Nav from '@/components/Nav';
import Card, { CardHead, CardLabel } from '@/components/Card';
import { auth, clearToken, isLoggedIn } from '@/lib/api';

export default function SettingsPage() {
  const router = useRouter();
  const [email, setEmail] = useState('');
  const [plan, setPlan] = useState('free');
  const [hasKeys, setHasKeys] = useState(false);
  const [apiKey, setApiKey] = useState('');
  const [secret, setSecret] = useState('');
  const [keyMsg, setKeyMsg] = useState('');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!isLoggedIn()) { router.push('/login'); return; }
    auth.me().then(me => { setEmail(me.email); setPlan(me.plan); setHasKeys(me.has_binance_keys); })
      .catch(() => router.push('/login'));
  }, []);

  async function saveKeys(e: React.FormEvent) {
    e.preventDefault(); setKeyMsg(''); setLoading(true);
    try {
      await auth.setBinanceKeys(apiKey, secret);
      setKeyMsg('Keys saved successfully.'); setHasKeys(true); setApiKey(''); setSecret('');
    } catch (err: unknown) {
      setKeyMsg(err instanceof Error ? err.message : 'Failed');
    } finally { setLoading(false); }
  }

  function logout() { clearToken(); router.push('/login'); }

  return (
    <>
      <Nav email={email} />
      <div style={{ maxWidth: 720, margin: '0 auto', padding: '40px 32px 80px' }}>

        <div style={{ marginBottom: 28 }}>
          <div style={{ fontFamily: 'Geist Mono', fontSize: 11, letterSpacing: '0.14em', textTransform: 'uppercase', color: 'var(--muted)' }}>Settings</div>
          <h1 style={{ fontSize: 40, letterSpacing: '-0.025em', fontWeight: 500, lineHeight: 1.05, margin: '6px 0 0' }}>
            Your <span className="serif">account.</span>
          </h1>
        </div>

        {/* Account info */}
        <Card style={{ marginBottom: 20 }}>
          <CardHead><CardLabel>Account</CardLabel></CardHead>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20 }}>
            {[
              { k: 'Email', v: email },
              { k: 'Plan', v: plan.charAt(0).toUpperCase() + plan.slice(1) },
            ].map(({ k, v }) => (
              <div key={k}>
                <div style={{ fontFamily: 'Geist Mono', fontSize: 11, letterSpacing: '0.1em', textTransform: 'uppercase', color: 'var(--muted)', marginBottom: 6 }}>{k}</div>
                <div style={{ fontSize: 17, fontWeight: 500 }}>{v}</div>
              </div>
            ))}
          </div>
        </Card>

        {/* Binance keys */}
        <Card style={{ marginBottom: 20 }}>
          <CardHead>
            <CardLabel>Binance API keys</CardLabel>
            {hasKeys && (
              <span style={{ fontFamily: 'Geist Mono', fontSize: 11, color: 'var(--green)', letterSpacing: '0.05em' }}>✓ Connected</span>
            )}
          </CardHead>
          <p style={{ color: 'var(--muted)', fontSize: 14, marginTop: 0, marginBottom: 20 }}>
            Trade-execution keys only. Withdrawal permissions are never required.
          </p>
          <form onSubmit={saveKeys}>
            <label style={{ display: 'block', fontFamily: 'Geist Mono', fontSize: 11, letterSpacing: '0.1em', textTransform: 'uppercase', color: 'var(--muted)', marginBottom: 8 }}>API Key</label>
            <input value={apiKey} onChange={e => setApiKey(e.target.value)} placeholder="Paste your Binance API key"
              style={{ width: '100%', padding: '12px 16px', fontSize: 14, background: '#fff', border: '1px solid var(--line)', borderRadius: 10, fontFamily: 'Geist Mono', outline: 'none', marginBottom: 14 }} />
            <label style={{ display: 'block', fontFamily: 'Geist Mono', fontSize: 11, letterSpacing: '0.1em', textTransform: 'uppercase', color: 'var(--muted)', marginBottom: 8 }}>Secret Key</label>
            <input type="password" value={secret} onChange={e => setSecret(e.target.value)} placeholder="Paste your Binance secret"
              style={{ width: '100%', padding: '12px 16px', fontSize: 14, background: '#fff', border: '1px solid var(--line)', borderRadius: 10, fontFamily: 'Geist Mono', outline: 'none', marginBottom: 20 }} />
            {keyMsg && <p style={{ fontFamily: 'Geist Mono', fontSize: 13, color: keyMsg.includes('success') ? 'var(--green)' : 'var(--red)', marginBottom: 16 }}>{keyMsg}</p>}
            <button type="submit" disabled={loading || !apiKey || !secret}
              style={{ padding: '12px 20px', background: 'var(--ink)', color: '#fff', border: 0, borderRadius: 10, fontSize: 14, fontWeight: 500, cursor: 'pointer', opacity: loading ? 0.7 : 1 }}>
              {loading ? 'Saving...' : 'Save keys'}
            </button>
          </form>
        </Card>

        {/* Logout */}
        <button onClick={logout}
          style={{ padding: '12px 20px', background: 'rgba(14,15,18,0.06)', color: 'var(--ink)', border: 0, borderRadius: 10, fontSize: 14, cursor: 'pointer', fontFamily: 'inherit' }}>
          Sign out
        </button>
      </div>
    </>
  );
}
