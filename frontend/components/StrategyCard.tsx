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
  const isBenchmark = s.strategy === 'hold';
  const beating = s.vs_benchmark > 0;

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
        <div style={{ display: 'flex', alignItems: 'baseline', gap: 10, flexWrap: 'wrap' }}>
          <div style={{ fontSize: 34, fontWeight: 500, letterSpacing: '-0.025em', color: pnlColor }}>
            {sign(s.total_pnl)}${s.total_pnl.toFixed(2)}
          </div>
          <div style={{ fontFamily: 'Geist Mono', fontSize: 14, color: pnlColor }}>
            {sign(s.return_pct)}{s.return_pct.toFixed(2)}%
          </div>
        </div>
        <div style={{ fontFamily: 'Geist Mono', fontSize: 12, color: todayColor, marginTop: 4 }}>
          {sign(s.pnl_today)}${s.pnl_today.toFixed(2)} today
        </div>
      </div>

      {/* Verdict against the do-nothing benchmark */}
      {!isBenchmark && (
        <div style={{
          fontFamily: 'Geist Mono', fontSize: 11, letterSpacing: '0.04em',
          padding: '8px 10px', borderRadius: 8,
          background: beating ? 'rgba(20,180,130,0.10)' : 'rgba(14,15,18,0.05)',
          color: beating ? 'var(--green)' : 'var(--muted)',
        }}>
          {beating ? '▲' : '▼'} {sign(s.vs_benchmark)}{s.vs_benchmark.toFixed(2)}% vs Buy &amp; Hold
        </div>
      )}

      {/* Mini stats */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 12, paddingTop: 16, borderTop: '1px solid var(--line)' }}>
        <MiniStat label="Win rate" value={`${s.win_rate}%`} />
        <MiniStat label="Trades today" value={String(s.trades_today)} />
        <MiniStat label="Total trades" value={String(s.total_trades)} />
      </div>

      {/* Risk profile — what win rate alone cannot tell you */}
      {s.total_trades > 0 && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 12, paddingTop: 14, borderTop: '1px solid var(--line)' }}>
          <MiniStat
            label="Profit factor"
            value={s.profit_factor ? s.profit_factor.toFixed(2) : '—'}
            color={s.profit_factor >= 1.3 ? 'var(--green)' : s.profit_factor && s.profit_factor < 1 ? 'var(--red)' : undefined}
          />
          <MiniStat label="Avg win / loss" value={`$${s.avg_win.toFixed(2)} / $${Math.abs(s.avg_loss).toFixed(2)}`} />
          <MiniStat
            label="Max drawdown"
            value={`${s.max_drawdown_pct.toFixed(1)}%`}
            color={s.max_drawdown_pct > 20 ? 'var(--red)' : undefined}
          />
        </div>
      )}

      {s.bot_count === 0 && (
        <Link href="/strategy" style={{ fontFamily: 'Geist Mono', fontSize: 11, letterSpacing: '0.08em', textTransform: 'uppercase', color: 'var(--accent)', textDecoration: 'none' }}>
          Create a bot →
        </Link>
      )}
    </div>
  );
}
