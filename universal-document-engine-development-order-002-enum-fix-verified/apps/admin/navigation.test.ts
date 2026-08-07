import { describe, expect, it } from 'vitest';

import { adminNavigation } from './navigation';

describe('admin navigation', () => {
  it('contains the approved administration placeholders', () => {
    expect(adminNavigation.map(({ label }) => label)).toEqual([
      'Tenants',
      'Users',
      'System Status',
      'Audit',
      'Configuration',
    ]);
  });
});
