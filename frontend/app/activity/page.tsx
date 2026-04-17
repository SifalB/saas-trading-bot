'use client';
import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import Nav from '@/components/Nav';
import Card from '@/components/Card';
import { trades as tradesApi, auth, isLoggedIn, type Trade } from '@/lib/api';

const REASON_COLORS: Record<string, { bg: string; color: string; label: string }> = {
  TAKE_PROFIT: { bg: 'rgba(20,180,130,0.12)', color: 'var(--green)', label: 'TP' },
  STOP_LOSS:   { bg: 'rgba(210,80,40,0.12)',  color: 'var(--red)',   label: 'SL' },
  TIMEOUT:     { bg: 'rgba(14,15,18,0.06)',   color: 'var(--muted)', label: 'TO' },
  GRID_SELL:   { bg: 'rgba(20,180,130,0.12)', color: 'var(--green)', label: 'GD' },
  GRID_RESET:  { bg: 'rgba(14,15,18,0.06)',   color: 'var(--muted)', label: 'RS' },
  SIGNAL:      { bg: 'rgba(20,180,130,0.12)', color: 'var(--green)', label: 'SG' },
};

export default function ActivityPage() {
  const router = useRouter();
  const [allTrades, setAllTrades] = useState<Trade[]>([]);
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!isLoggedIn()) { router.push('/login'); return; }
    Promise.all([tradesApi.list({ limit: 200 }), auth.me()])
      .then(([t, me]) => { setAllTrades(t); setEmail(me.email); })
      .catch(() => router.push('/login'))
      .finally(() => setLoading(false));
  }, []);

  const totalPnl = allTrades.reduce((s, t) => s + t.pnl_usdt, 0);
  const wins = allTrades.filter(t => t.pnl_usdt > 0).length;
  const winRate = allTrades.length ? (wins / allTrades.length * 100).toFixed(1) : '0';

  return (
    <>
      <Nav email={email} />
      <div style={{ maxWidth: 1280, margin: '0 auto', padding: '40px 32px 80px' }}>

        <div style={{ marginBottom: 28 }}>
          <div style={{ fontFamily: 'Geist Mono', fontSize: 11, letterSpacing: '0.14em', textTransform: 'uppercase', color: 'var(--muted)' }}>Activity</div>
          <h1 style={{ fontSize: 40, letterSpacing: '-0.025em', fontWeight: 500, lineHeight: 1.05, margin: '6px 0 0' }}>
            Trade <span className="serif">history.</span>
          </h1>
        </div>

        {/* Summary */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 16, marginBottom: 32 }}>
          {[
            { k: 'Total P&L', v: `${totalPnl >= 0 ? '+' : ''}$${totalPnl.toFixed(2)}`, color: totalPnl >= 0 ? 'var(--green)' : 'var(--red)' },
            { k: 'Total trades', v: String(allTrades.length) },
            { k: 'Win rate', v: `${winRate}%` },
          ].map(({ k, v, color }) => (
            <Card key={k}>
              <div style={{ fontFamily: 'Geist Mono', fontSize: 11, letterSpacing: '0.1em', textTransform: 'uppercase', color: 'var(--muted)', marginBottom: 8 }}>{k}</div>
              <div style={{ fontSize: 32, fontWeight: 500, letterSpacing: '-0.02em', color: color ?? 'var(--ink)' }}>{v}</div>
            </Card>
          ))}
        </div>

        {/* Table */}
        <Card>
          {loading ? (
            <p style={{ color: 'var(--muted)', fontFamily: 'Geist Mono', fontSize: 13 }}>Loading...</p>
          ) : allTrades.length === 0 ? (
            <p style={{ color: 'var(--muted)', fontFamily: 'Geist Mono', fontSize: 13 }}>No trades yet.</p>
          ) : (
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead>
                <tr>
                  {['Type', 'Symbol', 'Entry', 'Exit', 'P&L', 'Time'].map(h => (
                    <th key={h} style={{ textAlign: 'left', padding: '14px 0', borderBottom: '1px solid var(--line)', fontFamily: 'Geist Mono', fontSize: 11, letterSpacing: '0.1em', textTransform: 'uppercase', color: 'var(--muted)', fontWeight: 500 }}>
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {allTrades.map(t => {
                  const tag = REASON_COLORS[t.reason] ?? REASON_COLORS.SIGNAL;
                  const isWin = t.pnl_usdt >= 0;
                  return (
                    <tr key={t.id}>
                      <td style={{ padding: '14px 0', borderBottom: '1px solid var(--line)' }}>
                        <span style={{ display: 'inline-block', padding: '4px 10px', borderRadius: 6, background: tag.bg, color: tag.color, fontFamily: 'Geist Mono', fontSize: 11 }}>
                          {tag.label}
                        </span>
                      </td>
                      <td style={{ padding: '14px 0', borderBottom: '1px solid var(--line)', fontSize: 14, fontWeight: 500 }}>{t.symbol}</td>
                      <td style={{ padding: '14px 0', borderBottom: '1px solid var(--line)', fontFamily: 'Geist Mono', fontSize: 13 }}>${t.entry_price.toLocaleString(undefined, { maximumFractionDigits: 4 })}</td>
                      <td style={{ padding: '14px 0', borderBottom: '1px solid var(--line)', fontFamily: 'Geist Mono', fontSize: 13 }}>${t.exit_price.toLocaleString(undefined, { maximumFractionDigits: 4 })}</td>
                      <td style={{ padding: '14px 0', borderBottom: '1px solid var(--line)', fontFamily: 'Geist Mono', fontSize: 13, color: isWin ? 'var(--green)' : 'var(--red)' }}>
                        {isWin ? '+' : ''}${t.pnl_usdt.toFixed(4)}
                      </td>
                      <td style={{ padding: '14px 0', borderBottom: '1px solid var(--line)', fontFamily: 'Geist Mono', fontSize: 11, color: 'var(--muted)' }}>
                        {new Date(t.exit_time).toLocaleString()}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          )}
        </Card>
      </div>
    </>
  );
}
