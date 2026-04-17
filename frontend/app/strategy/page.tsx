'use client';
import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import Nav from '@/components/Nav';
import BotCard from '@/components/BotCard';
import Card from '@/components/Card';
import { bots as botApi, auth, isLoggedIn, type Bot } from '@/lib/api';

const BOT_TYPES = [
  { type: 'grid', label: 'Grid Trading', desc: 'Buy low / sell high within a fixed price grid. Best for sideways markets.' },
  { type: 'scalp', label: 'Scalping', desc: 'RSI + EMA momentum strategy. Fast in-and-out trades on 1m candles.' },
  { type: 'corr', label: 'Correlation', desc: 'Trade altcoins when BTC makes a significant move. Follow the leader.' },
];

export default function StrategyPage() {
  const router = useRouter();
  const [allBots, setAllBots] = useState<Bot[]>([]);
  const [email, setEmail] = useState('');
  const [creating, setCreating] = useState(false);
  const [name, setName] = useState('');
  const [type, setType] = useState('grid');
  const [paper, setPaper] = useState(true);
  const [error, setError] = useState('');

  async function load() {
    try {
      const [b, me] = await Promise.all([botApi.list(), auth.me()]);
      setAllBots(b); setEmail(me.email);
    } catch { router.push('/login'); }
  }

  useEffect(() => {
    if (!isLoggedIn()) { router.push('/login'); return; }
    load();
  }, []);

  async function createBot(e: React.FormEvent) {
    e.preventDefault(); setError('');
    try {
      await botApi.create(name || `${type} bot`, type, {}, paper);
      setCreating(false); setName('');
      load();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed');
    }
  }

  return (
    <>
      <Nav email={email} botRunning={allBots.some(b => b.status === 'running')} />
      <div style={{ maxWidth: 1280, margin: '0 auto', padding: '40px 32px 80px' }}>

        <div style={{ marginBottom: 28 }}>
          <div style={{ fontFamily: 'Geist Mono', fontSize: 11, letterSpacing: '0.14em', textTransform: 'uppercase', color: 'var(--muted)' }}>Strategy</div>
          <h1 style={{ fontSize: 40, letterSpacing: '-0.025em', fontWeight: 500, lineHeight: 1.05, margin: '6px 0 0' }}>
            Your <span className="serif">trading bots.</span>
          </h1>
        </div>

        {/* Bot type cards */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 16, marginBottom: 40 }}>
          {BOT_TYPES.map(bt => (
            <div key={bt.type} onClick={() => { setType(bt.type); setCreating(true); }}
              style={{
                background: type === bt.type && creating ? 'var(--ink)' : 'var(--card)',
                color: type === bt.type && creating ? '#fff' : 'var(--ink)',
                border: `1px solid ${type === bt.type && creating ? 'transparent' : 'var(--line)'}`,
                borderRadius: 18, padding: 24, cursor: 'pointer',
              }}>
              <div style={{ fontFamily: 'Geist Mono', fontSize: 11, letterSpacing: '0.1em', textTransform: 'uppercase', color: type === bt.type && creating ? 'rgba(255,255,255,0.55)' : 'var(--muted)', marginBottom: 10 }}>{bt.type}</div>
              <div style={{ fontSize: 20, fontWeight: 500, marginBottom: 8 }}>{bt.label}</div>
              <div style={{ fontSize: 14, color: type === bt.type && creating ? 'rgba(255,255,255,0.7)' : 'var(--muted)', lineHeight: 1.5 }}>{bt.desc}</div>
            </div>
          ))}
        </div>

        {/* Create form */}
        {creating && (
          <Card style={{ marginBottom: 40 }}>
            <h3 style={{ margin: '0 0 20px', fontSize: 20, fontWeight: 500 }}>New {BOT_TYPES.find(b => b.type === type)?.label} bot</h3>
            <form onSubmit={createBot} style={{ display: 'flex', gap: 16, alignItems: 'flex-end', flexWrap: 'wrap' }}>
              <div>
                <label style={{ display: 'block', fontFamily: 'Geist Mono', fontSize: 11, letterSpacing: '0.1em', textTransform: 'uppercase', color: 'var(--muted)', marginBottom: 8 }}>Name</label>
                <input value={name} onChange={e => setName(e.target.value)} placeholder={`My ${type} bot`}
                  style={{ padding: '12px 16px', fontSize: 15, background: '#fff', border: '1px solid var(--line)', borderRadius: 10, fontFamily: 'inherit', outline: 'none', width: 240 }} />
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 10, paddingBottom: 2 }}>
                <input type="checkbox" id="paper" checked={paper} onChange={e => setPaper(e.target.checked)} />
                <label htmlFor="paper" style={{ fontSize: 14, color: 'var(--body)' }}>Paper trading</label>
              </div>
              {error && <span style={{ color: 'var(--red)', fontFamily: 'Geist Mono', fontSize: 13 }}>{error}</span>}
              <div style={{ display: 'flex', gap: 10 }}>
                <button type="submit" style={{ padding: '12px 20px', background: 'var(--ink)', color: '#fff', border: 0, borderRadius: 10, fontSize: 14, fontWeight: 500, cursor: 'pointer' }}>
                  Create bot
                </button>
                <button type="button" onClick={() => setCreating(false)} style={{ padding: '12px 20px', background: 'rgba(14,15,18,0.06)', color: 'var(--ink)', border: 0, borderRadius: 10, fontSize: 14, cursor: 'pointer' }}>
                  Cancel
                </button>
              </div>
            </form>
          </Card>
        )}

        {/* Existing bots */}
        {allBots.length > 0 && (
          <>
            <div style={{ fontFamily: 'Geist Mono', fontSize: 11, letterSpacing: '0.14em', textTransform: 'uppercase', color: 'var(--muted)', marginBottom: 16 }}>
              {allBots.length} bot{allBots.length > 1 ? 's' : ''}
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: 20 }}>
              {allBots.map(b => <BotCard key={b.id} bot={b} onRefresh={load} />)}
            </div>
          </>
        )}

        {!creating && allBots.length === 0 && (
          <div style={{ textAlign: 'center', padding: '60px 0', color: 'var(--muted)', fontFamily: 'Geist Mono', fontSize: 14 }}>
            Click a strategy above to create your first bot.
          </div>
        )}
      </div>
    </>
  );
}
