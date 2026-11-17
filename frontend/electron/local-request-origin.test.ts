import { describe, expect, it } from 'vitest';
import { isLocalServiceRequest } from './local-request-origin';

describe('desktop local service request origin', () => {
  it.each([
    ['http://localhost:5000/api/chat', 5000],
    ['http://127.0.0.1:5000/api/chat?x=1', 5000],
    ['http://localhost:3000/dashboard', 3000],
    ['http://127.0.0.1:3000/', 3000],
  ])('allows the exact local service origin %s', (url, port) => {
    expect(isLocalServiceRequest(url, port)).toBe(true);
  });

  it.each([
    ['http://localhost:5000@outside.example/path', 5000],
    ['http://localhost:5000.outside.example/path', 5000],
    ['http://localhost:50000/path', 5000],
    ['http://user:password@localhost:5000/path', 5000],
    ['https://localhost:5000/path', 5000],
    ['http://localhost:3000@outside.example/path', 3000],
    ['http://localhost:30000/path', 3000],
    ['not a URL', 5000],
  ])('rejects a misleading or invalid URL %s', (url, port) => {
    expect(isLocalServiceRequest(url, port)).toBe(false);
  });
});
