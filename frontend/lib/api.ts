const BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

function getToken(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem('token');
}

export function setToken(t: string) { localStorage.setItem('token', t); }
export function clearToken() { localStorage.removeItem('token'); }
export function isLoggedIn() { return !!getToken(); }

async function req<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = getToken();
  const res = await fetch(`${BASE}${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...options.headers,
    },
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || 'Request failed');
  }
  if (res.status === 204) return undefined as T;
  return res.json();
}

// ── Auth ──────────────────────────────────────────────────────────────────────
export const auth = {
  register: (data: {
    email: string; password: string;
    first_name: string; last_name: string; age: number;
    phone?: string; address?: string; city?: string; country?: string;
  }) =>
    req<{ access_token: string }>('/auth/register', {
      method: 'POST', body: JSON.stringify(data),
    }),
  login: (email: string, password: string) =>
    req<{ access_token: string }>('/auth/login', {
      method: 'POST', body: JSON.stringify({ email, password }),
    }),
  me: () => req<{ id: number; email: string; plan: string; has_binance_keys: boolean }>('/auth/me'),
  setBinanceKeys: (api_key: string, secret: string) =>
    req('/auth/binance-keys', { method: 'PUT', body: JSON.stringify({ api_key, secret }) }),
};

// ── Bots ──────────────────────────────────────────────────────────────────────
export type Bot = {
  id: number; name: string; type: string; config: Record<string, unknown>;
  paper_mode: boolean; status: string; created_at: string;
};

export const bots = {
  list: () => req<Bot[]>('/bots/'),
  create: (name: string, type: string, config: Record<string, unknown>, paper_mode = true) =>
    req<Bot>('/bots/', { method: 'POST', body: JSON.stringify({ name, type, config, paper_mode }) }),
  update: (id: number, data: Partial<Bot>) =>
    req<Bot>(`/bots/${id}`, { method: 'PATCH', body: JSON.stringify(data) }),
  delete: (id: number) => req(`/bots/${id}`, { method: 'DELETE' }),
  start: (id: number) => req(`/bots/${id}/start`, { method: 'POST' }),
  stop: (id: number) => req(`/bots/${id}/stop`, { method: 'POST' }),
  defaults: (type: string) => req<Record<string, unknown>>(`/bots/defaults/${type}`),
};

// ── Trades ────────────────────────────────────────────────────────────────────
export type Trade = {
  id: number; bot_id: number; symbol: string;
  entry_price: number; exit_price: number; size: number;
  pnl_usdt: number; pnl_pct: number; reason: string;
  entry_time: string; exit_time: string;
};

export const trades = {
  list: (params?: { bot_id?: number; symbol?: string; limit?: number }) => {
    const q = new URLSearchParams();
    if (params?.bot_id) q.set('bot_id', String(params.bot_id));
    if (params?.symbol) q.set('symbol', params.symbol);
    if (params?.limit) q.set('limit', String(params.limit));
    return req<Trade[]>(`/trades/?${q}`);
  },
};

// ── Dashboard ─────────────────────────────────────────────────────────────────
export type Stats = {
  total_pnl: number; total_trades: number; win_rate: number;
  best_trade: number; worst_trade: number; active_bots: number; trades_today: number;
};

export const dashboard = { stats: () => req<Stats>('/dashboard/stats') };
