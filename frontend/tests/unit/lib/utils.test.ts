import { describe, it, expect } from 'vitest';
import { cn, delay } from '@/lib/utils';

describe('utils', () => {
  describe('cn', () => {
    it('should merge class names correctly', () => {
      expect(cn('c1', 'c2')).toBe('c1 c2');
    });

    it('should handle conditional class names', () => {
      expect(cn('c1', true && 'c2', false && 'c3')).toBe('c1 c2');
    });

    it('should merge tailwind classes correctly', () => {
      expect(cn('px-2 py-1', 'p-4')).toBe('p-4');
    });
  });

  describe('delay', () => {
    it('should resolve after specified time', async () => {
      const start = Date.now();
      await delay(100);
      const end = Date.now();
      expect(end - start).toBeGreaterThanOrEqual(90); // Allow some buffer
    });
  });
});
