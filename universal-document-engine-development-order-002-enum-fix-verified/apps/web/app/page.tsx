import { AppShell, PlaceholderCard } from '@ude/ui';

import { ApiHealthStatus } from '../components/api-health-status';
import { webNavigation } from '../navigation';

const cards = [
  {
    eyebrow: 'Workspace',
    title: 'Projects',
    description:
      'Future home for isolated document projects and their controlled lifecycle.',
  },
  {
    eyebrow: 'Core asset',
    title: 'Documents',
    description:
      'A review-first document workspace will be connected in a later order.',
  },
  {
    eyebrow: 'Reusable layer',
    title: 'Templates',
    description: 'Versioned templates will remain independent from the user interface.',
  },
  {
    eyebrow: 'Deterministic layer',
    title: 'Rules',
    description:
      'Approved rules will make decisions without depending on an AI provider.',
  },
  {
    eyebrow: 'Quality gate',
    title: 'Human review',
    description:
      'Legally relevant output will always require an explicit human review step.',
  },
  {
    eyebrow: 'Deployment',
    title: 'Hybrid by design',
    description:
      'The same codebase is prepared for future cloud and on-premise operation.',
  },
] as const;

export default function DashboardPage() {
  return (
    <AppShell
      contextLabel="Main application"
      navigation={webNavigation}
      productName="Universal Document Engine"
    >
      <section className="ude-hero">
        <div>
          <span className="ude-kicker">Platform foundation</span>
          <h1>Structured inputs. Controlled rules. Reviewable documents.</h1>
          <p>
            This application shell establishes the neutral platform boundary. No
            document-generation or specialist workflow logic is active yet.
          </p>
        </div>
        <ApiHealthStatus />
      </section>
      <section className="ude-grid" aria-label="Platform areas">
        {cards.map((card) => (
          <PlaceholderCard {...card} key={card.title} />
        ))}
      </section>
    </AppShell>
  );
}
