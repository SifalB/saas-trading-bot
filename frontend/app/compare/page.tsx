'use client';
import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import Nav from '@/components/Nav';
import { dashboard, bots as botApi, isLoggedIn, type BotStats, type Bot } from '@/lib/api';

const TYPE_LABEL: Record<string, string> = {
  grid: 'Grid', scalp: 'Scalp', corr: 'Corr', mtf: 'MTF',
  breakout: 'Breakout', dip: 'Dip', volbreak: 'VolBrk', rotation: 'Rotation', hold: 'Hold',
};

export default function ComparePage() {
  const router = useRouter();
  const [stats, setStats] = useState<BotStats[]>([]);
  const [allBots, setAllBots] = useState<Bot[]>([]);
  const [loading, setLoading] = useState(true);

  async function load() {
    try {
      const [s, b] = await Promise.all([dashboard.compare(), botApi.list()]);
      setStats(s);
      setAllBots(b);
    } catch {
      router.push('/login');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (!isLoggedIn()) { router.push('/login'); return; }
    load();
    const interval = setInterval(load, 30_000);
    return () => clearInterval(interval);
  }, []);

  const runningBots = allBots.filter(b => b.status === 'running');

  if (loading) return (
    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100vh', fontFamily: 'Geist Mono', color: 'var(--muted)', fontSize: 13 }}>
      Loading...
    </div>
  );

  const totalPnl = stats.reduce((s, b) => s + b.total_pnl, 0);
  const totalTrades = stats.reduce((s, b) => s + b.total_trades, 0);

  return (
    <>
      <Nav botRunning={runningBots.length > 0} email="" />
      <div style={{ maxWidth: 1280, margin: '0 auto', padding: '40px 32px 80px' }}>

        {/* Header */}
        <div style={{ marginBottom: 32 }}>
          <div style={{ fontFamily: 'Geist Mono', fontSize: 11, letterSpacing: '0.14em', textTransform: 'uppercase', color: 'var(--muted)' }}>
            Bot comparison
          </div>
          <h1 style={{ fontSize: 40, letterSpacing: '-0.025em', fontWeight: 500, lineHeight: 1.05, margin: '6px 0 0' }}>
            {stats.length} bots, <span className="serif">{totalTrades} trades</span>
          </h1>
        </div>

        {/* Summary row */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 16, marginBottom: 32 }}>
          {[
            { k: 'Combined P&L', v: `${totalPnl >= 0 ? '+' : ''}$${totalPnl.toFixed(2)}`, color: totalPnl >= 0 ? 'var(--green)' : 'var(--red)' },
            { k: 'Total trades', v: String(totalTrades) },
            { k: 'Active bots', v: String(runningBots.length) },
          ].map(({ k, v, color }) => (
            <div key={k} style={{ background: 'var(--surface)', borderRadius: 16, padding: '24px 28px', border: '1px solid var(--line)' }}>
              <div style={{ fontFamily: 'Geist Mono', fontSize: 11, letterSpacing: '0.1em', textTransform: 'uppercase', color: 'var(--muted)', marginBottom: 8 }}>{k}</div>
              <div style={{ fontSize: 32, fontWeight: 500, letterSpacing: '-0.02em', color: color ?? 'var(--ink)' }}>{v}</div>
            </div>
          ))}
        </div>

        {/* Leaderboard table */}
        {stats.length === 0 ? (
          <div style={{ background: 'var(--surface)', borderRadius: 16, padding: 40, border: '1px solid var(--line)', textAlign: 'center', color: 'var(--muted)', fontFamily: 'Geist Mono', fontSize: 14 }}>
            No bots yet. Create one in Strategy.
          </div>
        ) : (
          <div style={{ background: 'var(--surface)', borderRadius: 16, border: '1px solid var(--line)', overflow: 'hidden' }}>
            {/* Table header */}
            <div style={{
              display: 'grid', gridTemplateColumns: '2fr 80px 100px 90px 90px 90px 90px 100px',
              padding: '14px 24px', borderBottom: '1px solid var(--line)',
              fontFamily: 'Geist Mono', fontSize: 11, letterSpacing: '0.1em', textTransform: 'uppercase', color: 'var(--muted)',
            }}>
              <span>Bot</span>
              <span>Type</span>
              <span>Status</span>
              <span style={{ textAlign: 'right' }}>P&L</span>
              <span style={{ textAlign: 'right' }}>Balance</span>
              <span style={{ textAlign: 'right' }}>Win rate</span>
              <span style={{ textAlign: 'right' }}>Trades</span>
              <span style={{ textAlign: 'right' }}>Best / Worst</span>
            </div>

            {/* Rows */}
            {stats.map((s, i) => {
              const isRunning = s.status === 'running';
              const pnlColor = s.total_pnl >= 0 ? 'var(--green)' : 'var(--red)';
              return (
                <div key={s.bot_id} style={{
                  display: 'grid', gridTemplateColumns: '2fr 80px 100px 90px 90px 90px 90px 100px',
                  padding: '18px 24px', alignItems: 'center',
                  borderBottom: i < stats.length - 1 ? '1px solid var(--line)' : 'none',
                  background: i === 0 && s.total_pnl > 0 ? 'rgba(20,180,130,0.03)' : undefined,
                }}>
                  {/* Name + rank */}
                  <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
                    <div style={{
                      width: 28, height: 28, borderRadius: 8, display: 'flex', alignItems: 'center', justifyContent: 'center',
                      fontFamily: 'Geist Mono', fontSize: 11, fontWeight: 600,
                      background: i === 0 ? 'rgba(20,180,130,0.15)' : 'var(--line)', color: i === 0 ? 'var(--green)' : 'var(--muted)',
                    }}>
                      #{i + 1}
                    </div>
                    <div>
                      <div style={{ fontSize: 15, fontWeight: 500 }}>{s.name}</div>
                      <div style={{ fontFamily: 'Geist Mono', fontSize: 11, color: 'var(--muted)', marginTop: 2 }}>
                        {s.paper_mode ? 'Paper' : 'Live'}
                      </div>
                    </div>
                  </div>

                  {/* Type */}
                  <div style={{ fontFamily: 'Geist Mono', fontSize: 12, color: 'var(--muted)' }}>
                    {TYPE_LABEL[s.type] ?? s.type}
                  </div>

                  {/* Status */}
                  <div style={{ display: 'flex', alignItems: 'center', gap: 7 }}>
                    <span style={{ width: 7, height: 7, borderRadius: '50%', background: isRunning ? 'var(--green)' : 'var(--muted)', display: 'inline-block' }} />
                    <span style={{ fontFamily: 'Geist Mono', fontSize: 12, color: isRunning ? 'var(--green)' : 'var(--muted)' }}>
                      {isRunning ? 'Running' : 'Stopped'}
                    </span>
                  </div>

                  {/* P&L */}
                  <div style={{ fontFamily: 'Geist Mono', fontSize: 14, fontWeight: 600, color: pnlColor, textAlign: 'right' }}>
                    {s.total_pnl >= 0 ? '+' : ''}${s.total_pnl.toFixed(2)}
                  </div>

                  {/* Balance */}
                  <div style={{ fontFamily: 'Geist Mono', fontSize: 13, textAlign: 'right' }}>
                    ${s.current_balance.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                  </div>

                  {/* Win rate */}
                  <div style={{ fontFamily: 'Geist Mono', fontSize: 13, textAlign: 'right' }}>
                    {s.total_trades > 0 ? `${s.win_rate}%` : '—'}
                  </div>

                  {/* Trades */}
                  <div style={{ fontFamily: 'Geist Mono', fontSize: 13, textAlign: 'right' }}>
                    {s.total_trades}
                  </div>

                  {/* Best / Worst */}
                  <div style={{ fontFamily: 'Geist Mono', fontSize: 11, textAlign: 'right' }}>
                    <span style={{ color: 'var(--green)' }}>+${s.best_trade.toFixed(2)}</span>
                    {' / '}
                    <span style={{ color: 'var(--red)' }}>${s.worst_trade.toFixed(2)}</span>
                  </div>
                </div>
              );
            })}
          </div>
        )}

        <div style={{ marginTop: 16, fontFamily: 'Geist Mono', fontSize: 11, color: 'var(--muted)' }}>
          Refreshes every 30s. Sorted by P&L.
        </div>
      </div>
    </>
  );
}
