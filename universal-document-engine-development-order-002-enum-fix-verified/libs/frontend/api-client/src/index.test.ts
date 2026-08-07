import { describe, expect, it } from 'vitest';

import { normalizeApiBaseUrl } from './index';

describe('normalizeApiBaseUrl', () => {
  it('removes trailing slashes without changing the origin', () => {
    expect(normalizeApiBaseUrl('http://localhost:8000///')).toBe(
      'http://localhost:8000',
    );
  });
});
