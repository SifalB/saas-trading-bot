import { CSSProperties, ReactNode } from 'react';

export default function Card({
  children, dark = false, style,
}: { children: ReactNode; dark?: boolean; style?: CSSProperties }) {
  return (
    <div style={{
      background: dark ? 'var(--ink)' : 'var(--card)',
      color: dark ? '#fff' : 'var(--ink)',
      border: dark ? 'none' : '1px solid var(--line)',
      borderRadius: 18, padding: 28,
      ...style,
    }}>
      {children}
    </div>
  );
}

export function CardHead({ children }: { children: ReactNode }) {
  return (
    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginBottom: 18 }}>
      {children}
    </div>
  );
}

export function CardLabel({ dark = false, children }: { dark?: boolean; children: ReactNode }) {
  return (
    <h3 style={{
      margin: 0, fontFamily: 'Geist Mono', fontSize: 11, fontWeight: 500,
      letterSpacing: '0.1em', textTransform: 'uppercase',
      color: dark ? 'rgba(255,255,255,0.55)' : 'var(--muted)',
    }}>
      {children}
    </h3>
  );
}
