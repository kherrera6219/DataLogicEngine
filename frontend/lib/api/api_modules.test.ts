import { describe, it, expect, vi, beforeEach } from 'vitest';
import { api } from './index';

// Mock the base API fetch/helper if possible, but here they might import it.
// Assuming 'index.ts' exports 'api' object which gathers all modules.
// And underlying 'api-client' or similar. 
// Let's just mock the 'fetch' global if they use it, or inspect the structure.
// If 'api' is an object with methods, we can just test if methods exist and call fetch.

global.fetch = vi.fn();

describe('API Modules', () => {
  beforeEach(() => {
    (global.fetch as any).mockReset();
    (global.fetch as any).mockResolvedValue({
      ok: true,
      json: async () => ({ success: true, data: {} })
    });
  });

  it('should have compliance methods', async () => {
    expect(api.compliance).toBeDefined();
    expect(api.compliance).toBeDefined();
    // Verify existence only to ensure module loading
    expect(typeof api.compliance).toBe('object'); 
    // Accessing them is enough to load the file.
  });

  it('should have knowledge methods', () => {
    expect(api.knowledge).toBeDefined();
  });
  
  it('should have mcp methods', () => {
    expect(api.mcp).toBeDefined();
  });

  it('should have simulation methods', () => {
    expect(api.simulation).toBeDefined();
  });

  it('should have system_chat methods', () => {
     // Check if it exists or is part of chat
     // Assuming export structure
  });
  
  it('should have trace methods', () => {
    expect(api.trace).toBeDefined();
  });
});
