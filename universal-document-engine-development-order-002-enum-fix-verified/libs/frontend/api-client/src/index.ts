/**
 * Stable placeholder boundary for the future OpenAPI-generated client.
 * Handwritten endpoint contracts must not be added here.
 */
export const API_CLIENT_GENERATION_STATUS = 'not-generated' as const;

export function normalizeApiBaseUrl(value: string): string {
  return value.replace(/\/+$/, '');
}
