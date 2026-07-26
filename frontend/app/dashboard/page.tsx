'use client';
import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import Nav from '@/components/Nav';
import PortfolioChart from '@/components/PortfolioChart';
import StrategyCard from '@/components/StrategyCard';
import Card, { CardHead, CardLabel } from '@/components/Card';
import { dashboard, auth, isLoggedIn, type Stats, type StrategyStat, type Trade, trades as tradesApi } from '@/lib/api';

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
  const [strategies, setStrategies] = useState<StrategyStat[]>([]);
  const [recentTrades, setRecentTrades] = useState<Trade[]>([]);
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(true);

  async function load() {
    try {
      const [s, str, t, me] = await Promise.all([
        dashboard.stats(),
        dashboard.strategies(),
        tradesApi.list({ limit: 6 }),
        auth.me(),
      ]);
      setStats(s); setStrategies(str); setRecentTrades(t); setEmail(me.email);
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

  const totalPnl = stats?.total_pnl ?? 0;
  const chartData = seed5000(totalPnl);
  const balance = 5000 + totalPnl;
  const activeStrategies = strategies.filter(s => s.running).length;
  const anyRunning = activeStrategies > 0;
  const sign = (n: number) => (n >= 0 ? '+' : '');

  const overviewTiles = [
    { k: 'Total P&L', v: `${sign(totalPnl)}$${totalPnl.toFixed(2)}`, color: totalPnl > 0 ? 'var(--green)' : totalPnl < 0 ? 'var(--red)' : 'var(--ink)' },
    { k: 'Win rate', v: `${stats?.win_rate ?? 0}%` },
    { k: 'Trades today', v: String(stats?.trades_today ?? 0) },
    { k: 'Total trades', v: String(stats?.total_trades ?? 0) },
    { k: 'Active strategies', v: `${activeStrategies} / ${strategies.length}` },
  ];

  return (
    <>
      <Nav botRunning={anyRunning} email={email} />
      <div style={{ maxWidth: 1280, margin: '0 auto', padding: '40px 32px 80px' }}>

        {/* ── OVERVIEW ─────────────────────────────────────────── */}
        <div style={{ marginBottom: 24 }}>
          <div style={{ fontFamily: 'Geist Mono', fontSize: 11, letterSpacing: '0.14em', textTransform: 'uppercase', color: 'var(--muted)' }}>
            Overview
          </div>
          <h1 style={{ fontSize: 40, letterSpacing: '-0.025em', fontWeight: 500, lineHeight: 1.05, margin: '6px 0 0' }}>
            {stats?.total_trades
              ? <>Portfolio <span className="serif">{sign(totalPnl)}${totalPnl.toFixed(2)}</span> across all strategies.</>
              : <>Your <span className="serif">trading cockpit.</span></>}
          </h1>
        </div>

        {/* Overview tiles */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: 14, marginBottom: 28 }}>
          {overviewTiles.map(({ k, v, color }) => (
            <Card key={k} style={{ padding: 20 }}>
              <div style={{ fontFamily: 'Geist Mono', fontSize: 10, letterSpacing: '0.1em', textTransform: 'uppercase', color: 'var(--muted)', marginBottom: 8 }}>{k}</div>
              <div style={{ fontSize: 24, fontWeight: 500, letterSpacing: '-0.02em', color: color ?? 'var(--ink)' }}>{v}</div>
            </Card>
          ))}
        </div>

        {/* Portfolio chart */}
        <div style={{ marginBottom: 40 }}>
          <PortfolioChart data={chartData} totalPnl={totalPnl} balance={balance} />
        </div>

        {/* ── STRATEGIES ───────────────────────────────────────── */}
        <div style={{ marginBottom: 18 }}>
          <div style={{ fontFamily: 'Geist Mono', fontSize: 11, letterSpacing: '0.14em', textTransform: 'uppercase', color: 'var(--muted)' }}>
            Strategies
          </div>
          <h2 style={{ fontSize: 26, letterSpacing: '-0.02em', fontWeight: 500, margin: '4px 0 0' }}>
            Each strategy at a glance
          </h2>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: 16, marginBottom: 40 }}>
          {strategies.map(s => <StrategyCard key={s.strategy} s={s} />)}
        </div>

        {/* ── RECENT TRADES ────────────────────────────────────── */}
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
    </>
  );
}
