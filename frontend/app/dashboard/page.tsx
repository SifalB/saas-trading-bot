'use client';
import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import Nav from '@/components/Nav';
import PortfolioChart from '@/components/PortfolioChart';
import StrategyCard from '@/components/StrategyCard';
import Card, { CardHead, CardLabel } from '@/components/Card';
import { dashboard, auth, bots as botApi, isLoggedIn, type Stats, type StrategyStat, type Trade, type Portfolio, type Equity, trades as tradesApi } from '@/lib/api';

export default function DashboardPage() {
  const router = useRouter();
  const [stats, setStats] = useState<Stats | null>(null);
  const [pf, setPf] = useState<Portfolio | null>(null);
  const [eq, setEq] = useState<Equity | null>(null);
  const [strategies, setStrategies] = useState<StrategyStat[]>([]);
  const [recentTrades, setRecentTrades] = useState<Trade[]>([]);
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(true);
  const [launching, setLaunching] = useState(false);

  async function launchAll() {
    setLaunching(true);
    try {
      await botApi.launchAll();
      await load();
    } catch (e) {
      console.error(e);
    } finally {
      setLaunching(false);
    }
  }

  async function load() {
    try {
      const [s, p, e, str, t, me] = await Promise.all([
        dashboard.stats(),
        dashboard.portfolio(),
        dashboard.equity(),
        dashboard.strategies(),
        tradesApi.list({ limit: 6 }),
        auth.me(),
      ]);
      setStats(s); setPf(p); setEq(e); setStrategies(str); setRecentTrades(t); setEmail(me.email);
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
  const chartData = (eq?.points ?? []).map(p => ({
    label: new Date(p.t).toLocaleString(undefined, { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' }),
    value: p.value,
  }));
  const balance = chartData.length ? chartData[chartData.length - 1].value : (pf?.equity ?? 0);
  const activeStrategies = strategies.filter(s => s.running).length;
  const anyRunning = activeStrategies > 0;
  const sign = (n: number) => (n >= 0 ? '+' : '');

  const overviewTiles = [
    { k: 'Total P&L', v: `${sign(totalPnl)}$${totalPnl.toFixed(2)}`, color: totalPnl > 0 ? 'var(--green)' : totalPnl < 0 ? 'var(--red)' : 'var(--ink)' },
    { k: 'Available to trade', v: `$${(pf?.available_cash ?? 0).toFixed(2)}`, sub: 'free cash' },
    { k: 'In positions', v: `$${(pf?.deployed ?? 0).toFixed(2)}`, sub: `${pf?.open_positions ?? 0} open` },
    { k: 'Fees paid', v: `-$${(pf?.total_fees ?? 0).toFixed(2)}`, color: 'var(--muted)' },
    { k: 'Win rate', v: `${stats?.win_rate ?? 0}%`, sub: `${stats?.total_trades ?? 0} trades` },
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
          <p style={{ fontFamily: 'Geist Mono', fontSize: 11, color: 'var(--muted)', margin: '10px 0 0', letterSpacing: '0.03em' }}>
            Each strategy trades its own independent ${(5000).toLocaleString()} paper account — including the Buy &amp; Hold benchmark — so returns compare directly.
          </p>
        </div>

        {/* Overview tiles */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: 14, marginBottom: 28 }}>
          {overviewTiles.map(({ k, v, color, sub }) => (
            <Card key={k} style={{ padding: 20 }}>
              <div style={{ fontFamily: 'Geist Mono', fontSize: 10, letterSpacing: '0.1em', textTransform: 'uppercase', color: 'var(--muted)', marginBottom: 8 }}>{k}</div>
              <div style={{ fontSize: 24, fontWeight: 500, letterSpacing: '-0.02em', color: color ?? 'var(--ink)' }}>{v}</div>
              {sub && <div style={{ fontFamily: 'Geist Mono', fontSize: 10, color: 'var(--muted)', marginTop: 4 }}>{sub}</div>}
            </Card>
          ))}
        </div>

        {/* Portfolio chart — real recorded equity, never synthesised */}
        <div style={{ marginBottom: 40 }}>
          {eq?.has_history ? (
            <>
              <PortfolioChart data={chartData} totalPnl={totalPnl} balance={balance} />
              <div style={{ fontFamily: 'Geist Mono', fontSize: 11, color: 'var(--muted)', marginTop: 10 }}>
                Max drawdown {eq.max_drawdown_pct.toFixed(2)}% (-${eq.max_drawdown.toFixed(2)}) · recorded every 5 min
              </div>
            </>
          ) : (
            <Card>
              <CardHead><CardLabel>Equity curve</CardLabel></CardHead>
              <p style={{ color: 'var(--muted)', fontSize: 14, fontFamily: 'Geist Mono', margin: 0 }}>
                Building history — equity is recorded every 5 minutes. The curve appears once there are at least two snapshots.
              </p>
            </Card>
          )}
        </div>

        {/* ── STRATEGIES ───────────────────────────────────────── */}
        <div style={{ marginBottom: 18, display: 'flex', alignItems: 'flex-end', justifyContent: 'space-between', gap: 16 }}>
          <div>
            <div style={{ fontFamily: 'Geist Mono', fontSize: 11, letterSpacing: '0.14em', textTransform: 'uppercase', color: 'var(--muted)' }}>
              Strategies
            </div>
            <h2 style={{ fontSize: 26, letterSpacing: '-0.02em', fontWeight: 500, margin: '4px 0 0' }}>
              Each strategy at a glance
            </h2>
          </div>
          <button onClick={launchAll} disabled={launching}
            style={{ padding: '11px 18px', background: anyRunning ? 'rgba(14,15,18,0.06)' : 'var(--ink)', color: anyRunning ? 'var(--ink)' : '#fff', border: 0, borderRadius: 10, fontSize: 14, fontWeight: 500, cursor: launching ? 'default' : 'pointer', opacity: launching ? 0.7 : 1, whiteSpace: 'nowrap' }}>
            {launching ? 'Launching…' : anyRunning ? 'Restart all (paper)' : 'Launch all strategies (paper)'}
          </button>
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
                    <div style={{ fontSize: 14 }}>{t.symbol} · <span style={{ color: 'var(--muted)' }}>{t.bot_name}</span></div>
                    <div style={{ fontFamily: 'Geist Mono', fontSize: 11, letterSpacing: '0.05em', color: 'var(--muted)', marginTop: 3 }}>
                      {t.reason} · {new Date(t.exit_time).toLocaleString()}
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
