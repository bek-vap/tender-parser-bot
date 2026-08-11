import React, { useEffect, useMemo, useState } from 'react';

type TgUser = {
  id?: number;
  username?: string;
  first_name?: string;
  last_name?: string;
};

type TgInitDataUnsafe = {
  user?: TgUser;
};

declare global {
  interface Window {
    Telegram?: {
      WebApp?: {
        ready: () => void;
        expand: () => void;
        initData: string;
        initDataUnsafe: TgInitDataUnsafe;
        close: () => void;
      };
    };
  }
}

export function App(): React.JSX.Element {
  const tg = window.Telegram?.WebApp;

  const [health, setHealth] = useState<string>('loading...');

  const apiBase = useMemo(() => {
    return import.meta.env.VITE_API_BASE ?? 'http://localhost:3001';
  }, []);

  useEffect(() => {
    tg?.ready();
    tg?.expand();
  }, [tg]);

  useEffect(() => {
    fetch(`${apiBase}/health`)
      .then((r) => r.json())
      .then((d) => setHealth(JSON.stringify(d)))
      .catch((e) => setHealth(String(e)));
  }, [apiBase]);

  return (
    <div style={{ padding: 16, fontFamily: 'system-ui, -apple-system, Segoe UI, Roboto, Arial' }}>
      <h2 style={{ marginTop: 0 }}>Tender Intelligence Mini App</h2>

      <div style={{ marginBottom: 12 }}>
        <div><b>Telegram user:</b></div>
        <pre style={{ background: '#f5f5f5', padding: 12, overflow: 'auto' }}>
          {JSON.stringify(tg?.initDataUnsafe?.user ?? null, null, 2)}
        </pre>
      </div>

      <div style={{ marginBottom: 12 }}>
        <div><b>Backend /health:</b></div>
        <pre style={{ background: '#f5f5f5', padding: 12, overflow: 'auto' }}>{health}</pre>
      </div>

      <button
        onClick={() => tg?.close()}
        style={{ padding: '10px 12px', borderRadius: 10, border: '1px solid #ddd', cursor: 'pointer' }}
      >
        Close
      </button>
    </div>
  );
}
