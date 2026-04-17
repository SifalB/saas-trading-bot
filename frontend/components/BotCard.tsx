'use client';
import { Bot, bots as botApi } from '@/lib/api';
import { useState } from 'react';

export default function BotCard({ bot, onRefresh }: { bot: Bot; onRefresh: () => void }) {
  const [loading, setLoading] = useState(false);
  const isRunning = bot.status === 'running';

  async function toggle() {
    setLoading(true);
    try {
      if (isRunning) await botApi.stop(bot.id);
      else await botApi.start(bot.id);
      onRefresh();
    } finally {
      setLoading(false);
    }
  }

  const typeLabel: Record<string, string> = { grid: 'Grid Trading', scalp: 'Scalping', corr: 'Correlation' };

  return (
    <div style={{
      background: 'var(--ink)', color: '#fff', borderRadius: 18, padding: 28,
    }}>
      {/* Head */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h3 style={{ margin: 0, fontFamily: 'Geist Mono', fontSize: 11, letterSpacing: '0.1em', textTransform: 'uppercase', color: 'rgba(255,255,255,0.55)' }}>
          {bot.name}
        </h3>
        <div style={{
          display: 'inline-flex', alignItems: 'center', gap: 10,
          background: 'rgba(255,255,255,0.08)', padding: '8px 14px',
          borderRadius: 999, fontSize: 13, fontFamily: 'Geist Mono', letterSpacing: '0.04em',
        }}>
          <span style={{
            width: 8, height: 8, borderRadius: '50%',
            background: isRunning ? 'var(--green)' : 'rgba(255,255,255,0.3)',
          }} />
          {isRunning ? 'LIVE' : 'STOPPED'}
        </div>
      </div>

      {/* Strategy */}
      <div style={{ fontSize: 32, fontWeight: 500, letterSpacing: '-0.015em', marginTop: 20, lineHeight: 1.1 }}>
        {typeLabel[bot.type] || bot.type}
        {bot.paper_mode && (
          <span style={{ fontSize: 14, fontFamily: 'Geist Mono', color: 'rgba(255,255,255,0.4)', marginLeft: 12, fontWeight: 400 }}>
            PAPER
          </span>
        )}
      </div>

      {/* Meta */}
      <div style={{
        display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 18,
        marginTop: 22, paddingTop: 22, borderTop: '1px solid rgba(255,255,255,0.1)',
      }}>
        {[
          { k: 'Symbols', v: ((bot.config.symbols || bot.config.alt_symbols) as string[] | undefined)?.length ?? '—' },
          { k: 'Paper mode', v: bot.paper_mode ? 'Yes' : 'Live' },
          { k: 'Status', v: bot.status },
        ].map(({ k, v }) => (
          <div key={k}>
            <div style={{ fontFamily: 'Geist Mono', fontSize: 11, letterSpacing: '0.1em', textTransform: 'uppercase', color: 'rgba(255,255,255,0.5)' }}>{k}</div>
            <div style={{ fontSize: 20, fontWeight: 500, marginTop: 6 }}>{String(v)}</div>
          </div>
        ))}
      </div>

      {/* Actions */}
      <div style={{ display: 'flex', gap: 10, marginTop: 22 }}>
        <button
          onClick={toggle}
          disabled={loading}
          style={{
            border: 0, padding: '12px 18px', borderRadius: 10, fontSize: 14, fontWeight: 500,
            background: '#fff', color: 'var(--ink)', cursor: 'pointer', opacity: loading ? 0.6 : 1,
          }}>
          {loading ? '...' : isRunning ? 'Stop bot' : 'Start bot'}
        </button>
      </div>
    </div>
  );
}
