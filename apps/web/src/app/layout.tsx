import type { Metadata } from 'next';
import './globals.css';
import 'katex/dist/katex.min.css';

export const metadata: Metadata = {
  title: 'Scribe - AI Research Assistant',
  description: 'Paper discovery, learning, and blog drafting powered by AI',
};

function Navbar() {
  return (
    <nav style={{
      position: 'fixed',
      top: 0,
      left: 0,
      right: 0,
      height: 'var(--nav-height)',
      background: 'rgba(10, 10, 10, 0.8)',
      backdropFilter: 'blur(12px)',
      borderBottom: '1px solid var(--card-border)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      padding: '0 2rem',
      zIndex: 100
    }}>
      <a href="/" style={{ fontSize: '1.25rem', fontWeight: 700, color: 'var(--primary)' }}>
        Scribe
      </a>
      <div style={{ display: 'flex', gap: '1.5rem', alignItems: 'center' }}>
        <a href="/research" style={{ color: 'var(--secondary)', fontSize: '0.9rem' }}>Research</a>
        <a href="/dashboard" style={{ color: 'var(--secondary)', fontSize: '0.9rem' }}>Dashboard</a>
      </div>
    </nav>
  );
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>
        <Navbar />
        {children}
      </body>
    </html>
  );
}
