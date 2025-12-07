/**
 * Error Tracking Service
 * Centralized error handling and reporting for production applications
 *
 * Features:
 * - Global error handler for uncaught errors
 * - Unhandled promise rejection handler
 * - Structured error logging
 * - Error deduplication
 * - Rate limiting for error reports
 * - Integration-ready for Sentry, DataDog, etc.
 *
 * Usage:
 * import { initializeErrorTracking, logError } from '@/utils/errorTracking';
 * initializeErrorTracking();
 * logError(error, { context: 'user-action' });
 */

const ERROR_LOG_ENDPOINT = '/api/log-error';
const MAX_ERRORS_PER_MINUTE = 10;
const ERROR_BUFFER_SIZE = 100;

class ErrorTrackingService {
  constructor() {
    this.errorBuffer = [];
    this.errorCounts = new Map();
    this.lastErrorTime = Date.now();
    this.errorRateLimiter = {
      count: 0,
      resetTime: Date.now() + 60000
    };
  }

  /**
   * Initialize global error handlers
   */
  initialize() {
    // Global error handler for uncaught errors
    window.addEventListener('error', this.handleGlobalError);

    // Unhandled promise rejection handler
    window.addEventListener('unhandledrejection', this.handleUnhandledRejection);

    // Console error override for development
    if (process.env.NODE_ENV === 'development') {
      this.overrideConsoleError();
    }

    console.log('[ErrorTracking] Initialized global error handlers');
  }

  /**
   * Clean up error handlers
   */
  cleanup() {
    window.removeEventListener('error', this.handleGlobalError);
    window.removeEventListener('unhandledrejection', this.handleUnhandledRejection);
  }

  /**
   * Handle global JavaScript errors
   */
  handleGlobalError = (event) => {
    const error = {
      type: 'error',
      message: event.message,
      filename: event.filename,
      lineno: event.lineno,
      colno: event.colno,
      error: event.error?.stack || event.error?.toString(),
      timestamp: new Date().toISOString()
    };

    this.logError(error, { severity: 'error', source: 'window.onerror' });

    // Prevent default browser error handling in production
    if (process.env.NODE_ENV === 'production') {
      event.preventDefault();
    }
  };

  /**
   * Handle unhandled promise rejections
   */
  handleUnhandledRejection = (event) => {
    const error = {
      type: 'unhandledRejection',
      reason: event.reason?.toString() || 'Unknown reason',
      promise: event.promise,
      stack: event.reason?.stack,
      timestamp: new Date().toISOString()
    };

    this.logError(error, { severity: 'error', source: 'unhandledrejection' });

    // Prevent default browser handling in production
    if (process.env.NODE_ENV === 'production') {
      event.preventDefault();
    }
  };

  /**
   * Override console.error to track errors
   */
  overrideConsoleError() {
    const originalError = console.error;
    console.error = (...args) => {
      this.logError(
        { message: args.join(' '), type: 'console.error' },
        { severity: 'warning', source: 'console' }
      );
      originalError.apply(console, args);
    };
  }

  /**
   * Log error with context
   * @param {Error|Object|string} error - Error object or message
   * @param {Object} context - Additional context
   */
  logError = (error, context = {}) => {
    // Check rate limit
    if (!this.checkRateLimit()) {
      console.warn('[ErrorTracking] Rate limit exceeded, error not logged');
      return;
    }

    const errorData = this.normalizeError(error, context);
    const errorKey = this.getErrorKey(errorData);

    // Deduplicate errors
    if (this.isDuplicate(errorKey)) {
      this.incrementErrorCount(errorKey);
      return;
    }

    // Add to buffer
    this.errorBuffer.push(errorData);
    if (this.errorBuffer.length > ERROR_BUFFER_SIZE) {
      this.errorBuffer.shift();
    }

    // Track error count
    this.errorCounts.set(errorKey, {
      count: 1,
      firstSeen: Date.now(),
      lastSeen: Date.now()
    });

    // Send to backend
    this.sendErrorToBackend(errorData);

    // Log to console in development
    if (process.env.NODE_ENV === 'development') {
      console.error('[ErrorTracking]', errorData);
    }
  };

  /**
   * Normalize error into consistent format
   */
  normalizeError(error, context) {
    const baseData = {
      timestamp: new Date().toISOString(),
      url: window.location.href,
      userAgent: navigator.userAgent,
      viewport: {
        width: window.innerWidth,
        height: window.innerHeight
      },
      ...context
    };

    if (error instanceof Error) {
      return {
        ...baseData,
        message: error.message,
        name: error.name,
        stack: error.stack,
        type: 'Error'
      };
    }

    if (typeof error === 'string') {
      return {
        ...baseData,
        message: error,
        type: 'string'
      };
    }

    return {
      ...baseData,
      ...error
    };
  }

  /**
   * Generate unique key for error deduplication
   */
  getErrorKey(errorData) {
    const { message, stack, filename, lineno } = errorData;
    return `${message}-${filename}-${lineno}-${stack?.split('\n')[0]}`;
  }

  /**
   * Check if error is duplicate within time window
   */
  isDuplicate(errorKey) {
    const existing = this.errorCounts.get(errorKey);
    if (!existing) return false;

    const timeSinceFirst = Date.now() - existing.firstSeen;
    // Deduplicate if seen within last 60 seconds
    return timeSinceFirst < 60000;
  }

  /**
   * Increment error count for deduplication tracking
   */
  incrementErrorCount(errorKey) {
    const existing = this.errorCounts.get(errorKey);
    if (existing) {
      existing.count += 1;
      existing.lastSeen = Date.now();
    }
  }

  /**
   * Check rate limit for error logging
   */
  checkRateLimit() {
    const now = Date.now();

    // Reset rate limiter if time window passed
    if (now >= this.errorRateLimiter.resetTime) {
      this.errorRateLimiter.count = 0;
      this.errorRateLimiter.resetTime = now + 60000;
    }

    // Check if under limit
    if (this.errorRateLimiter.count < MAX_ERRORS_PER_MINUTE) {
      this.errorRateLimiter.count += 1;
      return true;
    }

    return false;
  }

  /**
   * Send error to backend
   */
  async sendErrorToBackend(errorData) {
    try {
      await fetch(ERROR_LOG_ENDPOINT, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(errorData),
        // Don't wait for response
        keepalive: true
      });
    } catch (e) {
      // Silent fail - don't create error loops
      console.warn('[ErrorTracking] Failed to send error to backend:', e);
    }
  }

  /**
   * Get error statistics
   */
  getStats() {
    return {
      totalErrors: this.errorBuffer.length,
      uniqueErrors: this.errorCounts.size,
      recentErrors: this.errorBuffer.slice(-10),
      errorCounts: Array.from(this.errorCounts.entries()).map(([key, data]) => ({
        key,
        ...data
      }))
    };
  }

  /**
   * Clear error buffer
   */
  clearBuffer() {
    this.errorBuffer = [];
    this.errorCounts.clear();
  }
}

// Singleton instance
const errorTrackingService = new ErrorTrackingService();

/**
 * Initialize error tracking
 */
export function initializeErrorTracking() {
  errorTrackingService.initialize();
}

/**
 * Log error manually
 */
export function logError(error, context) {
  errorTrackingService.logError(error, context);
}

/**
 * Get error statistics
 */
export function getErrorStats() {
  return errorTrackingService.getStats();
}

/**
 * Clear error buffer
 */
export function clearErrorBuffer() {
  errorTrackingService.clearBuffer();
}

/**
 * Cleanup error tracking
 */
export function cleanupErrorTracking() {
  errorTrackingService.cleanup();
}

export default errorTrackingService;
