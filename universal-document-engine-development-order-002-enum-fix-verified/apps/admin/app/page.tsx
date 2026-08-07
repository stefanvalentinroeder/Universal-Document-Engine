import { AppShell, PlaceholderCard, StatusBadge } from '@ude/ui';

import { adminNavigation } from '../navigation';

const cards = [
  {
    eyebrow: 'Isolation boundary',
    title: 'Tenants',
    description:
      'Tenant administration is intentionally deferred; isolation remains mandatory.',
  },
  {
    eyebrow: 'Identity',
    title: 'Users',
    description:
      'Authentication and authorization will be introduced through a dedicated order.',
  },
  {
    eyebrow: 'Operations',
    title: 'System Status',
    description:
      'Operational health surfaces will consume API readiness signals in a later order.',
  },
  {
    eyebrow: 'Traceability',
    title: 'Audit',
    description:
      'Structured logs are prepared for later audit integration without storing payloads.',
  },
  {
    eyebrow: 'Platform',
    title: 'Configuration',
    description:
      'Provider-specific configuration will stay behind explicit platform interfaces.',
  },
] as const;

export default function AdminPage() {
  return (
    <AppShell
      contextLabel="Administration"
      navigation={adminNavigation}
      productName="Universal Document Engine"
    >
      <section className="ude-hero">
        <div>
          <span className="ude-kicker">Administrative boundary</span>
          <h1>Platform oversight without premature control logic.</h1>
          <p>
            This separate shell reserves the operational surface while tenant, user,
            audit, and configuration behavior remains deliberately unimplemented.
          </p>
        </div>
        <StatusBadge label="Admin shell ready" tone="positive" />
      </section>
      <section className="ude-grid" aria-label="Administration areas">
        {cards.map((card) => (
          <PlaceholderCard {...card} key={card.title} />
        ))}
      </section>
    </AppShell>
  );
}
