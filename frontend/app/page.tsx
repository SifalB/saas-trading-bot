'use client';
import Link from 'next/link';
import { isLoggedIn } from '@/lib/api';

export default function LandingPage() {
  const loggedIn = typeof window !== 'undefined' && isLoggedIn();

  return (
    <div style={{ background: 'var(--bg)', minHeight: '100vh' }}>

      {/* ── Nav ───────────────────────────────────────────────────── */}
      <nav style={{
        height: 68, borderBottom: '1px solid var(--line)',
        display: 'flex', alignItems: 'center', padding: '0 48px',
        position: 'sticky', top: 0, zIndex: 10, background: 'var(--bg)',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, fontWeight: 500, fontSize: 17, letterSpacing: '0.01em' }}>
          <span style={{ width: 14, height: 14, borderRadius: '50%', background: 'var(--accent)', display: 'inline-block' }} />
          Veridian
        </div>
        <div style={{ flex: 1 }} />
        <div style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
          <Link href={loggedIn ? '/dashboard' : '/login'} style={{
            padding: '10px 20px', background: 'var(--ink)', color: '#fff',
            borderRadius: 10, fontSize: 14, fontWeight: 500, textDecoration: 'none',
          }}>
            {loggedIn ? 'Go to dashboard' : 'Sign in'}
          </Link>
        </div>
      </nav>

      {/* ── Hero ──────────────────────────────────────────────────── */}
      <section style={{ maxWidth: 1280, margin: '0 auto', padding: '120px 48px 100px' }}>
        <div style={{ fontFamily: 'Geist Mono', fontSize: 12, letterSpacing: '0.14em', textTransform: 'uppercase', color: 'var(--muted)', marginBottom: 28 }}>
          Veridian Trading · v1.0
        </div>
        <h1 style={{ fontSize: 'clamp(64px, 8vw, 120px)', fontWeight: 500, letterSpacing: '-0.03em', lineHeight: 1.02, margin: '0 0 32px', maxWidth: 900 }}>
          Trade on your<br /><span className="serif">own terms.</span>
        </h1>
        <p style={{ fontSize: 22, color: 'var(--muted)', maxWidth: 560, lineHeight: 1.5, margin: '0 0 48px' }}>
          A SaaS platform for personalized crypto trading bots — tuned to the risk you want to take.
        </p>
        <div style={{ display: 'flex', gap: 14 }}>
          <Link href={loggedIn ? '/dashboard' : '/login'} style={{
            padding: '16px 28px', background: 'var(--ink)', color: '#fff',
            borderRadius: 12, fontSize: 16, fontWeight: 500, textDecoration: 'none',
          }}>
            {loggedIn ? 'Open dashboard →' : 'Start for free →'}
          </Link>
          <a href="#how" style={{
            padding: '16px 28px', background: 'rgba(14,15,18,0.06)', color: 'var(--ink)',
            borderRadius: 12, fontSize: 16, fontWeight: 500, textDecoration: 'none',
          }}>
            How it works
          </a>
        </div>
      </section>

      {/* ── Stats ─────────────────────────────────────────────────── */}
      <section style={{ borderTop: '1px solid var(--line)', borderBottom: '1px solid var(--line)' }}>
        <div style={{ maxWidth: 1280, margin: '0 auto', padding: '60px 48px', display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 48 }}>
          {[
            { n: '420M+', l: 'People globally now hold crypto as part of a long-term portfolio' },
            { n: '14%',   l: 'Average annual return institutions target from algorithmic strategies' },
            { n: '< 3%',  l: 'Of retail holders use any form of automated strategy today' },
          ].map(({ n, l }) => (
            <div key={n}>
              <div style={{ fontSize: 64, fontWeight: 500, letterSpacing: '-0.03em', lineHeight: 1 }}>{n}</div>
              <div style={{ marginTop: 14, fontSize: 16, color: 'var(--muted)', lineHeight: 1.5, maxWidth: 280 }}>{l}</div>
            </div>
          ))}
        </div>
      </section>

      {/* ── How it works ──────────────────────────────────────────── */}
      <section id="how" style={{ maxWidth: 1280, margin: '0 auto', padding: '100px 48px' }}>
        <div style={{ fontFamily: 'Geist Mono', fontSize: 12, letterSpacing: '0.14em', textTransform: 'uppercase', color: 'var(--muted)', marginBottom: 20 }}>
          How it works
        </div>
        <h2 style={{ fontSize: 56, fontWeight: 500, letterSpacing: '-0.025em', lineHeight: 1.05, margin: '0 0 64px', maxWidth: 800 }}>
          Three steps to a bot that works the way <span className="serif">you</span> want it to.
        </h2>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 48 }}>
          {[
            { n: 'STEP 01', title: 'Connect your exchange', desc: 'Link a trade-only API key from Binance. Funds never leave your wallet.' },
            { n: 'STEP 02', title: 'Configure your risk', desc: 'Set a risk slider from Conservative to Aggressive. The engine maps it to a full strategy.' },
            { n: 'STEP 03', title: 'Let it run', desc: 'Trades execute automatically. Pause, adjust, or export your history any time.' },
          ].map(({ n, title, desc }) => (
            <div key={n} style={{ paddingTop: 28, borderTop: '1px solid var(--line)' }}>
              <div style={{ fontFamily: 'Geist Mono', fontSize: 12, letterSpacing: '0.1em', color: 'var(--muted)', marginBottom: 20 }}>{n}</div>
              <h3 style={{ fontSize: 28, fontWeight: 500, letterSpacing: '-0.015em', lineHeight: 1.1, margin: '0 0 14px' }}>{title}</h3>
              <p style={{ fontSize: 17, color: 'var(--muted)', lineHeight: 1.5, margin: 0 }}>{desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* ── Risk slider visual ─────────────────────────────────────── */}
      <section style={{ background: 'var(--ink)', color: '#fff' }}>
        <div style={{ maxWidth: 1280, margin: '0 auto', padding: '100px 48px' }}>
          <div style={{ fontFamily: 'Geist Mono', fontSize: 12, letterSpacing: '0.14em', textTransform: 'uppercase', color: 'rgba(255,255,255,0.5)', marginBottom: 20 }}>
            Risk customization
          </div>
          <h2 style={{ fontSize: 56, fontWeight: 500, letterSpacing: '-0.025em', lineHeight: 1.05, margin: '0 0 64px', maxWidth: 900 }}>
            Your tolerance, <span className="serif">mapped directly</span> to how the bot trades.
          </h2>

          {/* Slider visual */}
          <div style={{ marginBottom: 28 }}>
            <div style={{ height: 14, borderRadius: 999, background: 'linear-gradient(90deg, oklch(0.78 0.09 160) 0%, oklch(0.82 0.11 90) 50%, oklch(0.66 0.18 28) 100%)', position: 'relative' }}>
              <div style={{ position: 'absolute', left: '34%', top: '50%', transform: 'translate(-50%,-50%)', width: 34, height: 34, borderRadius: '50%', background: '#fff', border: '3px solid rgba(255,255,255,0.3)', boxShadow: '0 6px 20px rgba(0,0,0,0.3)' }} />
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', marginTop: 24, gap: 16 }}>
              {[
                { t: 'Conservative', d: 'Tight stops · blue-chips only · small sizing' },
                { t: 'Balanced', d: 'Diversified · moderate sizing · weekly rebalance', center: true },
                { t: 'Aggressive', d: 'Wider ranges · altcoins · larger positions', right: true },
              ].map(({ t, d, center, right }) => (
                <div key={t} style={{ textAlign: center ? 'center' : right ? 'right' : 'left' }}>
                  <div style={{ fontSize: 22, fontWeight: 500, letterSpacing: '-0.01em' }}>{t}</div>
                  <div style={{ marginTop: 8, fontSize: 14, color: 'rgba(255,255,255,0.55)' }}>{d}</div>
                </div>
              ))}
            </div>
          </div>

          <div style={{ fontFamily: 'Geist Mono', fontSize: 13, color: 'rgba(255,255,255,0.45)', marginTop: 40 }}>
            No jargon. No config files. Move the slider — the strategy adapts.
          </div>
        </div>
      </section>

      {/* ── Security ──────────────────────────────────────────────── */}
      <section style={{ maxWidth: 1280, margin: '0 auto', padding: '100px 48px' }}>
        <div style={{ fontFamily: 'Geist Mono', fontSize: 12, letterSpacing: '0.14em', textTransform: 'uppercase', color: 'var(--muted)', marginBottom: 20 }}>
          Security
        </div>
        <h2 style={{ fontSize: 56, fontWeight: 500, letterSpacing: '-0.025em', lineHeight: 1.05, margin: '0 0 64px', maxWidth: 800 }}>
          Transparency isn{"'"}t a feature. It{"'"}s the <span className="serif">default.</span>
        </h2>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 48 }}>
          <div>
            {[
              { n: '01', title: 'Funds never leave your exchange', desc: 'We hold trade-execution keys only. Withdrawal permissions are never requested.' },
              { n: '02', title: 'Every trade is logged', desc: 'Full audit trail. Strategy changes are versioned and reversible.' },
              { n: '03', title: 'Your data stays yours', desc: 'Export full trade history at any time in CSV or JSON.' },
            ].map(({ n, title, desc }) => (
              <div key={n} style={{ display: 'grid', gridTemplateColumns: '48px 1fr', gap: 20, padding: '28px 0', borderTop: '1px solid var(--line)' }}>
                <div style={{ fontFamily: 'Geist Mono', fontSize: 14, color: 'var(--muted)' }}>{n}</div>
                <div>
                  <div style={{ fontSize: 20, fontWeight: 500, letterSpacing: '-0.01em', marginBottom: 8 }}>{title}</div>
                  <div style={{ fontSize: 15, color: 'var(--muted)', lineHeight: 1.5 }}>{desc}</div>
                </div>
              </div>
            ))}
          </div>
          <div style={{ background: '#f2efe8', borderRadius: 18, padding: 40, display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
            <div style={{ fontFamily: 'Geist Mono', fontSize: 11, letterSpacing: '0.1em', textTransform: 'uppercase', color: 'var(--muted)', marginBottom: 20 }}>API key permissions</div>
            {[
              { label: 'READ portfolio',     ok: true },
              { label: 'EXECUTE trades',     ok: true },
              { label: 'WITHDRAW funds',     ok: false },
              { label: 'TRANSFER to wallet', ok: false },
            ].map(({ label, ok }) => (
              <div key={label} style={{ display: 'flex', justifyContent: 'space-between', padding: '16px 0', borderBottom: '1px solid var(--line)', fontFamily: 'Geist Mono', fontSize: 14 }}>
                <span>{label}</span>
                <span style={{ color: ok ? 'var(--green)' : 'var(--muted)' }}>{ok ? 'enabled' : 'disabled'}</span>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Pricing ───────────────────────────────────────────────── */}
      <section style={{ background: '#f2efe8', borderTop: '1px solid var(--line)' }}>
        <div style={{ maxWidth: 1280, margin: '0 auto', padding: '100px 48px' }}>
          <div style={{ fontFamily: 'Geist Mono', fontSize: 12, letterSpacing: '0.14em', textTransform: 'uppercase', color: 'var(--muted)', marginBottom: 20 }}>
            Pricing
          </div>
          <h2 style={{ fontSize: 56, fontWeight: 500, letterSpacing: '-0.025em', lineHeight: 1.05, margin: '0 0 64px', maxWidth: 800 }}>
            Start free. <span className="serif">Scale when it pays for itself.</span>
          </h2>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 24 }}>
            {[
              {
                name: 'Starter', price: '$0', unit: '/ month', dark: false,
                desc: 'Try the bot risk-free with a small position cap.',
                features: ['Up to $500 deployed capital', 'Conservative strategies only', 'Daily digest · 30-day history'],
              },
              {
                name: 'Standard', price: '$29', unit: '/ month', dark: true,
                desc: 'The full risk range, the full feature set.',
                features: ['Unlimited deployed capital', 'Full Conservative → Aggressive slider', 'Real-time alerts · full export'],
              },
              {
                name: 'Performance', price: '1%', unit: 'of profit', dark: false,
                desc: 'For serious portfolios that need more.',
                features: ['Priority execution routing', 'Custom strategy branches', 'Dedicated support'],
              },
            ].map(({ name, price, unit, dark, desc, features }) => (
              <div key={name} style={{
                background: dark ? 'var(--ink)' : '#fff', color: dark ? '#fff' : 'var(--ink)',
                borderRadius: 18, padding: 40, display: 'flex', flexDirection: 'column', gap: 20,
                border: dark ? 'none' : '1px solid var(--line)',
              }}>
                <div>
                  <div style={{ fontSize: 22, fontWeight: 500 }}>{name}</div>
                  <div style={{ fontSize: 13, color: dark ? 'rgba(255,255,255,0.55)' : 'var(--muted)', marginTop: 6, lineHeight: 1.4 }}>{desc}</div>
                </div>
                <div style={{ fontSize: 64, fontWeight: 500, letterSpacing: '-0.025em', lineHeight: 1 }}>
                  {price}<span style={{ fontSize: 18, fontWeight: 400, color: dark ? 'rgba(255,255,255,0.55)' : 'var(--muted)', marginLeft: 8 }}>{unit}</span>
                </div>
                <ul style={{ listStyle: 'none', padding: 0, margin: 0, display: 'flex', flexDirection: 'column', gap: 10 }}>
                  {features.map(f => (
                    <li key={f} style={{ fontSize: 15, paddingLeft: 20, position: 'relative', color: dark ? 'rgba(255,255,255,0.85)' : 'var(--body)' }}>
                      <span style={{ position: 'absolute', left: 0, top: '50%', transform: 'translateY(-50%)', width: 10, height: 1, background: 'currentColor', opacity: 0.4, display: 'inline-block' }} />
                      {f}
                    </li>
                  ))}
                </ul>
                <Link href={loggedIn ? '/dashboard' : '/login'} style={{
                  display: 'block', textAlign: 'center', marginTop: 'auto',
                  padding: '14px', borderRadius: 10, fontSize: 15, fontWeight: 500, textDecoration: 'none',
                  background: dark ? '#fff' : 'var(--ink)', color: dark ? 'var(--ink)' : '#fff',
                }}>
                  Get started
                </Link>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── CTA ───────────────────────────────────────────────────── */}
      <section style={{ background: 'var(--accent)', color: '#fff' }}>
        <div style={{ maxWidth: 1280, margin: '0 auto', padding: '100px 48px', display: 'flex', flexDirection: 'column', gap: 48 }}>
          <h2 style={{ fontSize: 'clamp(56px, 8vw, 100px)', fontWeight: 500, letterSpacing: '-0.03em', lineHeight: 0.98, margin: 0, maxWidth: 900 }}>
            Put your money to work <span className="serif">without</span> putting in the hours.
          </h2>
          <div>
            <Link href={loggedIn ? '/dashboard' : '/login'} style={{
              display: 'inline-flex', alignItems: 'center', gap: 12,
              padding: '18px 28px', background: '#fff', color: 'var(--accent)',
              borderRadius: 12, fontSize: 18, fontWeight: 500, textDecoration: 'none',
            }}>
              {loggedIn ? 'Open dashboard' : 'Start trading free'}
              <span style={{ fontFamily: 'Geist Mono', fontSize: 16 }}>→</span>
            </Link>
          </div>
        </div>
      </section>

      {/* ── Footer ────────────────────────────────────────────────── */}
      <footer style={{ borderTop: '1px solid var(--line)', padding: '32px 48px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, fontWeight: 500, fontSize: 15 }}>
          <span style={{ width: 10, height: 10, borderRadius: '50%', background: 'var(--accent)', display: 'inline-block' }} />
          Veridian Trading
        </div>
        <div style={{ fontFamily: 'Geist Mono', fontSize: 12, color: 'var(--muted)', letterSpacing: '0.04em' }}>
          © 2026 · Paper trading · Not financial advice
        </div>
      </footer>

    </div>
  );
}
