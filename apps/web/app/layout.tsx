import '@ude/ui/styles.css';

import type { Metadata } from 'next';
import type { ReactNode } from 'react';

export const metadata: Metadata = {
  title: 'Universal Document Engine',
  description: 'Reviewable document workflows built on a modular platform.',
};

export default function RootLayout({ children }: { readonly children: ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
