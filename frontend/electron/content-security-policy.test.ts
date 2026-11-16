import { describe, expect, it } from 'vitest';
import { desktopContentSecurityPolicy } from './content-security-policy';

describe('desktop content security policy', () => {
  it('permits local and embedded images without permitting remote image origins', () => {
    const imageDirective = desktopContentSecurityPolicy()
      .split(';')
      .map((directive) => directive.trim().split(/\s+/))
      .find(([name]) => name === 'img-src');

    expect(imageDirective).toEqual(['img-src', "'self'", 'data:', 'app:']);
  });
});
