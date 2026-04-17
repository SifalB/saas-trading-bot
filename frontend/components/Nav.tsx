'use client';
import Link from 'next/link';
import { usePathname } from 'next/navigation';

const TABS = [
  { label: 'Dashboard', href: '/dashboard' },
  { label: 'Strategy',  href: '/strategy' },
  { label: 'Activity',  href: '/activity' },
  { label: 'Settings',  href: '/settings' },
];

export default function Nav({ botRunning = false, email = '' }: { botRunning?: boolean; email?: string }) {
  const path = usePathname();
  const initials = email.slice(0, 2).toUpperCase() || 'ME';

  return (
    <nav style={{
      height: 68, borderBottom: '1px solid var(--line)', display: 'flex',
      alignItems: 'center', padding: '0 32px', gap: 32,
      background: 'var(--bg)', position: 'sticky', top: 0, zIndex: 10,
    }}>
      {/* Brand */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, fontWeight: 500, fontSize: 17, letterSpacing: '0.01em' }}>
        <span style={{ width: 14, height: 14, borderRadius: '50%', background: 'var(--accent)', display: 'inline-block' }} />
        Veridian
      </div>

      {/* Tabs */}
      <div style={{ display: 'flex', gap: 4, marginLeft: 24 }}>
        {TABS.map(t => (
          <Link key={t.href} href={t.href} style={{
            padding: '8px 14px', borderRadius: 8, fontSize: 14, textDecoration: 'none',
            color: path.startsWith(t.href) ? 'var(--ink)' : 'var(--muted)',
            background: path.startsWith(t.href) ? 'rgba(14,15,18,0.06)' : 'transparent',
          }}>
            {t.label}
          </Link>
        ))}
      </div>

      <div style={{ flex: 1 }} />

      {/* Bot status */}
      {botRunning && (
        <div style={{ display: 'inline-flex', alignItems: 'center', gap: 8, fontFamily: 'Geist Mono', fontSize: 12, letterSpacing: '0.08em', textTransform: 'uppercase', color: 'var(--muted)' }}>
          <span style={{ position: 'relative', width: 8, height: 8, borderRadius: '50%', background: 'var(--green)', display: 'inline-block' }} className="pulse-ring" />
          Bot Running
        </div>
      )}

      {/* Avatar */}
      <div style={{
        width: 34, height: 34, borderRadius: '50%',
        background: 'linear-gradient(135deg, #0e0f12, var(--accent))',
        color: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center',
        fontSize: 13, fontWeight: 500,
      }}>
        {initials}
      </div>
    </nav>
  );
}
