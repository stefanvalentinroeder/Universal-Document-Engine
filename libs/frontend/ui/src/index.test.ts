import { describe, expect, it } from 'vitest';

import { getHealthTone } from './index';

describe('getHealthTone', () => {
  it.each([
    ['checking', 'neutral'],
    ['online', 'positive'],
    ['offline', 'negative'],
  ] as const)('maps %s to %s', (status, expectedTone) => {
    expect(getHealthTone(status)).toBe(expectedTone);
  });
});
