import '@ude/ui/styles.css';

import type { Metadata } from 'next';
import type { ReactNode } from 'react';

export const metadata: Metadata = {
  title: 'Administration | Universal Document Engine',
  description: 'Administrative application shell for the platform.',
};

export default function RootLayout({ children }: { readonly children: ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
