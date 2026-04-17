'use client';
import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import Nav from '@/components/Nav';
import PortfolioChart from '@/components/PortfolioChart';
import BotCard from '@/components/BotCard';
import Card, { CardHead, CardLabel } from '@/components/Card';
import { dashboard, bots as botApi, trades as tradesApi, auth, isLoggedIn, type Bot, type Stats, type Trade } from '@/lib/api';

function seed5000(pnl: number) {
  const base = 5000;
  const pts = Array.from({ length: 28 }, (_, i) => ({
    label: `Day ${i + 1}`,
    value: +(base + (pnl / 28) * i + Math.sin(i) * 20).toFixed(2),
  }));
  pts.push({ label: 'Today', value: +(base + pnl).toFixed(2) });
  return pts;
}

export default function DashboardPage() {
  const router = useRouter();
  const [stats, setStats] = useState<Stats | null>(null);
  const [allBots, setAllBots] = useState<Bot[]>([]);
  const [recentTrades, setRecentTrades] = useState<Trade[]>([]);
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(true);

  async function load() {
    try {
      const [s, b, t, me] = await Promise.all([
        dashboard.stats(),
        botApi.list(),
        tradesApi.list({ limit: 6 }),
        auth.me(),
      ]);
      setStats(s); setAllBots(b); setRecentTrades(t); setEmail(me.email);
    } catch {
      router.push('/login');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (!isLoggedIn()) { router.push('/login'); return; }
    load();
  }, []);

  if (loading) return (
    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100vh', fontFamily: 'Geist Mono', color: 'var(--muted)', fontSize: 13 }}>
      Loading...
    </div>
  );

  const runningBots = allBots.filter(b => b.status === 'running');
  const chartData = seed5000(stats?.total_pnl ?? 0);
  const balance = 5000 + (stats?.total_pnl ?? 0);

  return (
    <>
      <Nav botRunning={runningBots.length > 0} email={email} />
      <div style={{ maxWidth: 1280, margin: '0 auto', padding: '40px 32px 80px' }}>

        {/* Header */}
        <div style={{ marginBottom: 28 }}>
          <div style={{ fontFamily: 'Geist Mono', fontSize: 11, letterSpacing: '0.14em', textTransform: 'uppercase', color: 'var(--muted)' }}>
            Good morning
          </div>
          <h1 style={{ fontSize: 40, letterSpacing: '-0.025em', fontWeight: 500, lineHeight: 1.05, margin: '6px 0 0' }}>
            {stats?.total_trades
              ? <>Your bot made <span className="serif">{stats.total_trades} trades</span> overall.</>
              : <>Welcome to <span className="serif">Veridian Trading.</span></>}
          </h1>
        </div>

        {/* Main grid */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 360px', gap: 28 }}>

          {/* Left */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 28 }}>
            <PortfolioChart data={chartData} totalPnl={stats?.total_pnl ?? 0} balance={balance} />

            {/* Stats row */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 16 }}>
              {[
                { k: 'Total P&L', v: `${stats?.total_pnl && stats.total_pnl >= 0 ? '+' : ''}$${stats?.total_pnl?.toFixed(2) ?? '0.00'}`, color: (stats?.total_pnl ?? 0) >= 0 ? 'var(--green)' : 'var(--red)' },
                { k: 'Win rate', v: `${stats?.win_rate ?? 0}%` },
                { k: 'Trades today', v: String(stats?.trades_today ?? 0) },
                { k: 'Active bots', v: String(stats?.active_bots ?? 0) },
              ].map(({ k, v, color }) => (
                <Card key={k}>
                  <div style={{ fontFamily: 'Geist Mono', fontSize: 11, letterSpacing: '0.1em', textTransform: 'uppercase', color: 'var(--muted)', marginBottom: 8 }}>{k}</div>
                  <div style={{ fontSize: 28, fontWeight: 500, letterSpacing: '-0.02em', color: color ?? 'var(--ink)' }}>{v}</div>
                </Card>
              ))}
            </div>

            {/* Recent trades */}
            <Card>
              <CardHead>
                <CardLabel>Recent trades</CardLabel>
                <a href="/activity" style={{ fontFamily: 'Geist Mono', fontSize: 11, color: 'var(--muted)', letterSpacing: '0.1em', textTransform: 'uppercase', textDecoration: 'none' }}>All →</a>
              </CardHead>
              {recentTrades.length === 0
                ? <p style={{ color: 'var(--muted)', fontSize: 14, fontFamily: 'Geist Mono' }}>No trades yet. Start a bot to begin.</p>
                : recentTrades.map(t => {
                  const isWin = t.pnl_usdt >= 0;
                  return (
                    <div key={t.id} style={{ display: 'grid', gridTemplateColumns: '40px 1fr auto', gap: 14, padding: '14px 0', borderBottom: '1px solid var(--line)', alignItems: 'center' }}>
                      <div style={{
                        width: 30, height: 30, borderRadius: 8, display: 'flex', alignItems: 'center', justifyContent: 'center',
                        fontFamily: 'Geist Mono', fontSize: 11, fontWeight: 500,
                        background: isWin ? 'rgba(20,180,130,0.12)' : 'rgba(210,80,40,0.12)',
                        color: isWin ? 'var(--green)' : 'var(--red)',
                      }}>
                        {t.reason === 'TAKE_PROFIT' ? 'TP' : t.reason === 'STOP_LOSS' ? 'SL' : 'EXIT'}
                      </div>
                      <div>
                        <div style={{ fontSize: 14 }}>{t.symbol} — {t.reason}</div>
                        <div style={{ fontFamily: 'Geist Mono', fontSize: 11, letterSpacing: '0.05em', color: 'var(--muted)', marginTop: 3 }}>
                          {new Date(t.exit_time).toLocaleString()}
                        </div>
                      </div>
                      <div style={{ fontFamily: 'Geist Mono', fontSize: 13, color: isWin ? 'var(--green)' : 'var(--red)' }}>
                        {isWin ? '+' : ''}${t.pnl_usdt.toFixed(2)}
                      </div>
                    </div>
                  );
                })}
            </Card>
          </div>

          {/* Right */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 28 }}>
            {allBots.length === 0 ? (
              <Card dark>
                <div style={{ fontFamily: 'Geist Mono', fontSize: 11, letterSpacing: '0.1em', textTransform: 'uppercase', color: 'rgba(255,255,255,0.55)', marginBottom: 16 }}>No bots yet</div>
                <div style={{ fontSize: 20, marginBottom: 20 }}>Create your first bot in Strategy to start trading.</div>
                <a href="/strategy" style={{ display: 'inline-block', background: '#fff', color: 'var(--ink)', borderRadius: 10, padding: '12px 18px', fontSize: 14, fontWeight: 500, textDecoration: 'none' }}>
                  Go to Strategy →
                </a>
              </Card>
            ) : (
              allBots.map(b => <BotCard key={b.id} bot={b} onRefresh={load} />)
            )}
          </div>
        </div>
      </div>
    </>
  );
}
