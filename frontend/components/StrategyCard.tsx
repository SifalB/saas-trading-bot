'use client';
import Link from 'next/link';
import type { StrategyStat } from '@/lib/api';

function MiniStat({ label, value, color }: { label: string; value: string; color?: string }) {
  return (
    <div>
      <div style={{ fontFamily: 'Geist Mono', fontSize: 10, letterSpacing: '0.1em', textTransform: 'uppercase', color: 'var(--muted)', marginBottom: 5 }}>{label}</div>
      <div style={{ fontSize: 16, fontWeight: 500, letterSpacing: '-0.01em', color: color ?? 'var(--ink)' }}>{value}</div>
    </div>
  );
}

export default function StrategyCard({ s }: { s: StrategyStat }) {
  const pnlColor = s.total_pnl > 0 ? 'var(--green)' : s.total_pnl < 0 ? 'var(--red)' : 'var(--ink)';
  const todayColor = s.pnl_today > 0 ? 'var(--green)' : s.pnl_today < 0 ? 'var(--red)' : 'var(--muted)';
  const sign = (n: number) => (n >= 0 ? '+' : '');

  return (
    <div style={{ background: 'var(--card)', border: '1px solid var(--line)', borderRadius: 18, padding: 24, display: 'flex', flexDirection: 'column', gap: 18 }}>
      {/* Header: name + status */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div>
          <div style={{ fontSize: 17, fontWeight: 500, letterSpacing: '-0.01em' }}>{s.label}</div>
          <div style={{ fontFamily: 'Geist Mono', fontSize: 10, letterSpacing: '0.1em', textTransform: 'uppercase', color: 'var(--muted)', marginTop: 3 }}>
            {s.bot_count === 0 ? 'No bot' : `${s.bot_count} bot${s.bot_count > 1 ? 's' : ''}`}
          </div>
        </div>
        <div style={{ display: 'inline-flex', alignItems: 'center', gap: 7, fontFamily: 'Geist Mono', fontSize: 10, letterSpacing: '0.08em', textTransform: 'uppercase', color: s.running ? 'var(--green)' : 'var(--muted)' }}>
          <span className={s.running ? 'pulse-ring' : ''} style={{ position: 'relative', width: 8, height: 8, borderRadius: '50%', background: s.running ? 'var(--green)' : 'var(--line)', display: 'inline-block' }} />
          {s.running ? 'Running' : 'Idle'}
        </div>
      </div>

      {/* P&L */}
      <div>
        <div style={{ fontSize: 34, fontWeight: 500, letterSpacing: '-0.025em', color: pnlColor }}>
          {sign(s.total_pnl)}${s.total_pnl.toFixed(2)}
        </div>
        <div style={{ fontFamily: 'Geist Mono', fontSize: 12, color: todayColor, marginTop: 4 }}>
          {sign(s.pnl_today)}${s.pnl_today.toFixed(2)} today
        </div>
      </div>

      {/* Mini stats */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 12, paddingTop: 16, borderTop: '1px solid var(--line)' }}>
        <MiniStat label="Win rate" value={`${s.win_rate}%`} />
        <MiniStat label="Trades today" value={String(s.trades_today)} />
        <MiniStat label="Total trades" value={String(s.total_trades)} />
      </div>

      {s.bot_count === 0 && (
        <Link href="/strategy" style={{ fontFamily: 'Geist Mono', fontSize: 11, letterSpacing: '0.08em', textTransform: 'uppercase', color: 'var(--accent)', textDecoration: 'none' }}>
          Create a bot →
        </Link>
      )}
    </div>
  );
}
