import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import {
  getLocalStorageItem,
  setLocalStorageItem,
  removeLocalStorageItem,
} from '@/lib/state/storage';

describe('Storage utilities', () => {
  let mockLocalStorage: Record<string, string>;

  beforeEach(() => {
    mockLocalStorage = {};
    const mockStorage = {
      getItem: vi.fn((key: string) => mockLocalStorage[key] ?? null),
      setItem: vi.fn((key: string, value: string) => {
        mockLocalStorage[key] = value;
      }),
      removeItem: vi.fn((key: string) => {
        delete mockLocalStorage[key];
      }),
      clear: vi.fn(() => {
        mockLocalStorage = {};
      }),
      key: vi.fn(() => null),
      length: 0,
    };
    Object.defineProperty(window, 'localStorage', {
      value: mockStorage,
      writable: true,
    });
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  describe('getLocalStorageItem', () => {
    it('should return null when key does not exist', () => {
      const result = getLocalStorageItem('non-existent-key');
      expect(result).toBeNull();
    });

    it('should return the value when key exists', () => {
      mockLocalStorage['test-key'] = 'test-value';
      const result = getLocalStorageItem('test-key');
      expect(result).toBe('test-value');
    });

    it('should return null when localStorage throws an error', () => {
      const mockStorage = {
        getItem: vi.fn(() => {
          throw new Error('Storage quota exceeded');
        }),
      };
      Object.defineProperty(window, 'localStorage', {
        value: mockStorage,
        writable: true,
      });
      const result = getLocalStorageItem('any-key');
      expect(result).toBeNull();
    });

    it('should return null when window is undefined', () => {
      const originalWindow = global.window;
      // @ts-expect-error test intentionally removes window
      delete global.window;
      const result = getLocalStorageItem('any-key');
      expect(result).toBeNull();
      global.window = originalWindow;
    });
  });

  describe('setLocalStorageItem', () => {
    it('should set a value in localStorage', () => {
      const result = setLocalStorageItem('test-key', 'test-value');
      expect(result).toBe(true);
      expect(mockLocalStorage['test-key']).toBe('test-value');
    });

    it('should return true on successful set', () => {
      const result = setLocalStorageItem('key', 'value');
      expect(result).toBe(true);
    });

    it('should return false when localStorage throws an error', () => {
      const mockStorage = {
        setItem: vi.fn(() => {
          throw new Error('QuotaExceededError');
        }),
      };
      Object.defineProperty(window, 'localStorage', {
        value: mockStorage,
        writable: true,
      });
      const result = setLocalStorageItem('key', 'value');
      expect(result).toBe(false);
    });

    it('should return false when window is undefined', () => {
      const originalWindow = global.window;
      // @ts-expect-error test intentionally removes window
      delete global.window;
      const result = setLocalStorageItem('key', 'value');
      expect(result).toBe(false);
      global.window = originalWindow;
    });

    it('should handle JSON serialization', () => {
      const jsonString = JSON.stringify({ name: 'test', age: 30 });
      const result = setLocalStorageItem('user-data', jsonString);
      expect(result).toBe(true);
      const retrieved = getLocalStorageItem('user-data');
      expect(JSON.parse(retrieved!)).toEqual({ name: 'test', age: 30 });
    });
  });

  describe('removeLocalStorageItem', () => {
    it('should remove an item from localStorage', () => {
      mockLocalStorage['test-key'] = 'test-value';
      const result = removeLocalStorageItem('test-key');
      expect(result).toBe(true);
      expect(mockLocalStorage['test-key']).toBeUndefined();
    });

    it('should return true even if key does not exist', () => {
      const result = removeLocalStorageItem('non-existent-key');
      expect(result).toBe(true);
    });

    it('should return false when localStorage throws an error', () => {
      const mockStorage = {
        removeItem: vi.fn(() => {
          throw new Error('Storage error');
        }),
      };
      Object.defineProperty(window, 'localStorage', {
        value: mockStorage,
        writable: true,
      });
      const result = removeLocalStorageItem('key');
      expect(result).toBe(false);
    });

    it('should return false when window is undefined', () => {
      const originalWindow = global.window;
      // @ts-expect-error test intentionally removes window
      delete global.window;
      const result = removeLocalStorageItem('key');
      expect(result).toBe(false);
      global.window = originalWindow;
    });
  });

  describe('Integration scenarios', () => {
    it('should persist and retrieve user session data', () => {
      const userData = JSON.stringify({
        user_id: '123',
        username: 'testuser',
        email: 'test@example.com',
        lastLogin: new Date().toISOString(),
      });
      setLocalStorageItem('user-session', userData);
      const retrieved = getLocalStorageItem('user-session');
      expect(JSON.parse(retrieved!)).toEqual(JSON.parse(userData));
    });

    it('should clear all storage', () => {
      setLocalStorageItem('key1', 'value1');
      setLocalStorageItem('key2', 'value2');
      setLocalStorageItem('key3', 'value3');

      expect(Object.keys(mockLocalStorage).length).toBe(3);

      removeLocalStorageItem('key1');
      removeLocalStorageItem('key2');
      removeLocalStorageItem('key3');

      expect(Object.keys(mockLocalStorage).length).toBe(0);
    });

    it('should handle multiple operations in sequence', () => {
      setLocalStorageItem('auth-token', 'abc123');
      expect(getLocalStorageItem('auth-token')).toBe('abc123');

      setLocalStorageItem('auth-token', 'xyz789');
      expect(getLocalStorageItem('auth-token')).toBe('xyz789');

      removeLocalStorageItem('auth-token');
      expect(getLocalStorageItem('auth-token')).toBeNull();
    });

    it('should handle large data storage', () => {
      const largeData = JSON.stringify({
        data: Array.from({ length: 1000 }, (_, i) => ({
          id: i,
          name: `item-${i}`,
          description: `This is item number ${i}`,
        })),
      });
      const result = setLocalStorageItem('large-data', largeData);
      expect(result).toBe(true);
      const retrieved = getLocalStorageItem('large-data');
      expect(retrieved).toBe(largeData);
    });
  });
});
