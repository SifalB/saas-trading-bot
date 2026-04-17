'use client';
import { AreaChart, Area, XAxis, ResponsiveContainer, Tooltip } from 'recharts';

type Point = { label: string; value: number };

const RANGES = ['1D', '1W', '1M', '1Y', 'ALL'];

export default function PortfolioChart({ data, totalPnl, balance }: {
  data: Point[];
  totalPnl: number;
  balance: number;
}) {
  const isUp = totalPnl >= 0;
  const sign = isUp ? '+' : '';

  return (
    <div style={{ background: 'var(--card)', border: '1px solid var(--line)', borderRadius: 18, padding: 28 }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginBottom: 18 }}>
        <h3 style={{ margin: 0, fontFamily: 'Geist Mono', fontSize: 11, fontWeight: 500, letterSpacing: '0.1em', textTransform: 'uppercase', color: 'var(--muted)' }}>
          Portfolio value
        </h3>
        <div style={{ display: 'flex', gap: 4 }}>
          {RANGES.map((r, i) => (
            <div key={r} style={{
              padding: '6px 12px', fontSize: 12, borderRadius: 8, fontFamily: 'Geist Mono', letterSpacing: '0.04em',
              background: i === 2 ? 'rgba(14,15,18,0.06)' : 'transparent',
              color: i === 2 ? 'var(--ink)' : 'var(--muted)',
              cursor: 'pointer',
            }}>{r}</div>
          ))}
        </div>
      </div>

      {/* Value */}
      <div style={{ fontSize: 72, letterSpacing: '-0.035em', fontWeight: 500, lineHeight: 1 }}>
        ${Math.floor(balance).toLocaleString()}
        <span style={{ color: 'var(--muted)', fontWeight: 400 }}>
          .{String(Math.abs(balance % 1 * 100).toFixed(0)).padStart(2, '0')}
        </span>
      </div>

      <div style={{ display: 'flex', gap: 24, marginTop: 14, alignItems: 'center' }}>
        <div style={{
          display: 'inline-flex', alignItems: 'center', gap: 6, padding: '6px 10px',
          borderRadius: 999, fontFamily: 'Geist Mono', fontSize: 13,
          background: isUp ? 'rgba(20,180,130,0.1)' : 'rgba(210,80,40,0.1)',
          color: isUp ? 'var(--green)' : 'var(--red)',
        }}>
          {isUp ? '▲' : '▼'} {sign}${Math.abs(totalPnl).toFixed(2)}
        </div>
        <div style={{ color: 'var(--muted)', fontSize: 14, fontFamily: 'Geist Mono' }}>All time P&L</div>
      </div>

      {/* Chart */}
      <div style={{ marginTop: 28, height: 220 }}>
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={data} margin={{ top: 5, right: 0, left: 0, bottom: 0 }}>
            <defs>
              <linearGradient id="grad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="var(--accent)" stopOpacity={0.22} />
                <stop offset="100%" stopColor="var(--accent)" stopOpacity={0} />
              </linearGradient>
            </defs>
            <XAxis dataKey="label" tick={{ fontFamily: 'Geist Mono', fontSize: 11, fill: 'var(--muted)' }} axisLine={false} tickLine={false} />
            <Tooltip
              contentStyle={{ background: 'var(--ink)', border: 'none', borderRadius: 8, color: '#fff', fontFamily: 'Geist Mono', fontSize: 12 }}
              formatter={(v: number) => [`$${v.toFixed(2)}`, 'Balance']}
            />
            <Area type="monotone" dataKey="value" stroke="var(--accent)" strokeWidth={2.2} fill="url(#grad)" dot={false} />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
