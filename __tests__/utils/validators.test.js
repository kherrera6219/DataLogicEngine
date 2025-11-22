import { isValidEmail, validatePassword, sanitizeInput } from '../../utils/validators'

describe('validators', () => {
  describe('isValidEmail', () => {
    it('validates correct email addresses', () => {
      expect(isValidEmail('test@example.com')).toBe(true)
      expect(isValidEmail('user.name@domain.co.uk')).toBe(true)
      expect(isValidEmail('user+tag@example.com')).toBe(true)
    })

    it('rejects invalid email addresses', () => {
      expect(isValidEmail('invalid')).toBe(false)
      expect(isValidEmail('invalid@')).toBe(false)
      expect(isValidEmail('@invalid.com')).toBe(false)
      expect(isValidEmail('invalid@com')).toBe(false)
      expect(isValidEmail('')).toBe(false)
      expect(isValidEmail(null)).toBe(false)
      expect(isValidEmail(undefined)).toBe(false)
    })
  })

  describe('validatePassword', () => {
    it('accepts strong passwords', () => {
      const result = validatePassword('StrongP@ss123')
      expect(result.valid).toBe(true)
      expect(result.errors).toHaveLength(0)
    })

    it('rejects passwords that are too short', () => {
      const result = validatePassword('Ab1!')
      expect(result.valid).toBe(false)
      expect(result.errors).toContain('Password must be at least 8 characters long')
    })

    it('requires uppercase letter', () => {
      const result = validatePassword('lowercase123!')
      expect(result.valid).toBe(false)
      expect(result.errors).toContain('Password must contain at least one uppercase letter')
    })

    it('requires lowercase letter', () => {
      const result = validatePassword('UPPERCASE123!')
      expect(result.valid).toBe(false)
      expect(result.errors).toContain('Password must contain at least one lowercase letter')
    })

    it('requires a number', () => {
      const result = validatePassword('NoNumbers!')
      expect(result.valid).toBe(false)
      expect(result.errors).toContain('Password must contain at least one number')
    })

    it('requires a special character', () => {
      const result = validatePassword('NoSpecial123')
      expect(result.valid).toBe(false)
      expect(result.errors).toContain('Password must contain at least one special character (!@#$%^&*)')
    })

    it('returns multiple errors for weak passwords', () => {
      const result = validatePassword('weak')
      expect(result.valid).toBe(false)
      expect(result.errors.length).toBeGreaterThan(1)
    })

    it('handles null and undefined', () => {
      expect(validatePassword(null).valid).toBe(false)
      expect(validatePassword(undefined).valid).toBe(false)
      expect(validatePassword('').valid).toBe(false)
    })
  })

  describe('sanitizeInput', () => {
    it('escapes HTML special characters', () => {
      expect(sanitizeInput('<script>alert("XSS")</script>'))
        .toBe('&lt;script&gt;alert(&quot;XSS&quot;)&lt;&#x2F;script&gt;')
    })

    it('escapes quotes', () => {
      expect(sanitizeInput('It\'s a "test"'))
        .toBe('It&#x27;s a &quot;test&quot;')
    })

    it('handles empty and null inputs', () => {
      expect(sanitizeInput('')).toBe('')
      expect(sanitizeInput(null)).toBe('')
      expect(sanitizeInput(undefined)).toBe('')
    })

    it('preserves safe text', () => {
      expect(sanitizeInput('Safe text 123')).toBe('Safe text 123')
    })
  })
})
