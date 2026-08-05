import type { ReactNode } from 'react';

export type StatusTone = 'neutral' | 'positive' | 'negative';

export interface NavigationItem {
  readonly label: string;
  readonly href: string;
}

export interface AppShellProps {
  readonly children: ReactNode;
  readonly contextLabel: string;
  readonly navigation: readonly NavigationItem[];
  readonly productName: string;
}

export interface StatusBadgeProps {
  readonly label: string;
  readonly tone?: StatusTone;
}

export interface PlaceholderCardProps {
  readonly description: string;
  readonly eyebrow: string;
  readonly title: string;
}

export function AppShell({
  children,
  contextLabel,
  navigation,
  productName,
}: AppShellProps) {
  return (
    <div className="ude-shell">
      <aside className="ude-sidebar">
        <div className="ude-brand">
          <span className="ude-brand-mark" aria-hidden="true">
            U
          </span>
          <span>
            <strong>{productName}</strong>
            <small>{contextLabel}</small>
          </span>
        </div>
        <nav className="ude-navigation" aria-label="Primary navigation">
          {navigation.map((item, index) => (
            <a
              className={index === 0 ? 'ude-nav-link is-active' : 'ude-nav-link'}
              href={item.href}
              key={item.label}
            >
              <span className="ude-nav-dot" aria-hidden="true" />
              {item.label}
            </a>
          ))}
        </nav>
        <div className="ude-sidebar-note">
          <span>Foundation workspace</span>
          <small>No production data connected</small>
        </div>
      </aside>
      <div className="ude-main">
        <header className="ude-topbar">
          <span className="ude-environment">Development environment</span>
          <button className="ude-login-placeholder" type="button" disabled>
            Sign in (planned)
          </button>
        </header>
        <main className="ude-content">{children}</main>
      </div>
    </div>
  );
}

export function StatusBadge({ label, tone = 'neutral' }: StatusBadgeProps) {
  return (
    <span className={`ude-status ude-status--${tone}`} role="status">
      <span className="ude-status-dot" aria-hidden="true" />
      {label}
    </span>
  );
}

export function PlaceholderCard({ description, eyebrow, title }: PlaceholderCardProps) {
  return (
    <article className="ude-card">
      <span className="ude-card-eyebrow">{eyebrow}</span>
      <h2>{title}</h2>
      <p>{description}</p>
      <span className="ude-card-action">Boundary established</span>
    </article>
  );
}

export function getHealthTone(status: 'checking' | 'online' | 'offline'): StatusTone {
  if (status === 'online') return 'positive';
  if (status === 'offline') return 'negative';
  return 'neutral';
}
