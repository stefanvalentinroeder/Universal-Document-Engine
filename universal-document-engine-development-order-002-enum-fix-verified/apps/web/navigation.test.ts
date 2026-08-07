import { describe, expect, it } from 'vitest';

import { webNavigation } from './navigation';

describe('web navigation', () => {
  it('contains the approved placeholder destinations', () => {
    expect(webNavigation.map(({ label }) => label)).toEqual([
      'Projects',
      'Documents',
      'Templates',
      'Rules',
      'Settings',
    ]);
  });
});
