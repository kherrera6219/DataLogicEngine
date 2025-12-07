/**
 * Performance Monitoring Service
 * Tracks Web Vitals and custom performance metrics
 *
 * Monitors:
 * - Core Web Vitals (LCP, FID, CLS, FCP, TTFB)
 * - Custom timing metrics
 * - Resource loading performance
 * - User interactions
 *
 * Integration:
 * - Google Analytics
 * - Custom analytics endpoints
 * - Console logging (development)
 */

/**
 * Web Vitals metrics thresholds
 * Based on Google's recommendations
 */
const THRESHOLDS = {
  LCP: { good: 2500, poor: 4000 },      // Largest Contentful Paint
  FID: { good: 100, poor: 300 },        // First Input Delay
  CLS: { good: 0.1, poor: 0.25 },       // Cumulative Layout Shift
  FCP: { good: 1800, poor: 3000 },      // First Contentful Paint
  TTFB: { good: 800, poor: 1800 },      // Time to First Byte
  INP: { good: 200, poor: 500 }         // Interaction to Next Paint
};

/**
 * Get metric rating based on value
 */
function getMetricRating(name, value) {
  const threshold = THRESHOLDS[name];
  if (!threshold) return 'unknown';
  if (value <= threshold.good) return 'good';
  if (value <= threshold.poor) return 'needs-improvement';
  return 'poor';
}

/**
 * Performance Monitoring Class
 */
class PerformanceMonitor {
  constructor() {
    this.metrics = [];
    this.customMarks = new Map();
    this.observers = [];
    this.isInitialized = false;
  }

  /**
   * Initialize performance monitoring
   */
  initialize() {
    if (this.isInitialized) return;

    // Only run in browser environment
    if (typeof window === 'undefined') return;

    this.isInitialized = true;

    // Monitor Core Web Vitals
    this.monitorWebVitals();

    // Monitor long tasks
    this.monitorLongTasks();

    // Monitor resource loading
    this.monitorResourceTiming();

    console.log('[Performance] Monitoring initialized');
  }

  /**
   * Monitor Core Web Vitals using web-vitals library
   * Install: npm install web-vitals
   */
  monitorWebVitals() {
    // Dynamic import for web-vitals
    if (typeof window !== 'undefined' && 'PerformanceObserver' in window) {
      // Monitor LCP - Largest Contentful Paint
      this.observePerformanceEntry('largest-contentful-paint', (entry) => {
        const metric = {
          name: 'LCP',
          value: entry.renderTime || entry.loadTime,
          rating: getMetricRating('LCP', entry.renderTime || entry.loadTime),
          timestamp: Date.now()
        };
        this.recordMetric(metric);
      });

      // Monitor FID - First Input Delay
      this.observePerformanceEntry('first-input', (entry) => {
        const metric = {
          name: 'FID',
          value: entry.processingStart - entry.startTime,
          rating: getMetricRating('FID', entry.processingStart - entry.startTime),
          timestamp: Date.now()
        };
        this.recordMetric(metric);
      });

      // Monitor CLS - Cumulative Layout Shift
      let clsValue = 0;
      this.observePerformanceEntry('layout-shift', (entry) => {
        if (!entry.hadRecentInput) {
          clsValue += entry.value;
          const metric = {
            name: 'CLS',
            value: clsValue,
            rating: getMetricRating('CLS', clsValue),
            timestamp: Date.now()
          };
          this.recordMetric(metric);
        }
      });

      // Monitor FCP - First Contentful Paint
      this.observePerformanceEntry('paint', (entry) => {
        if (entry.name === 'first-contentful-paint') {
          const metric = {
            name: 'FCP',
            value: entry.startTime,
            rating: getMetricRating('FCP', entry.startTime),
            timestamp: Date.now()
          };
          this.recordMetric(metric);
        }
      });

      // Monitor Navigation Timing for TTFB
      if (window.performance && window.performance.timing) {
        window.addEventListener('load', () => {
          const timing = window.performance.timing;
          const ttfb = timing.responseStart - timing.requestStart;
          const metric = {
            name: 'TTFB',
            value: ttfb,
            rating: getMetricRating('TTFB', ttfb),
            timestamp: Date.now()
          };
          this.recordMetric(metric);
        });
      }
    }
  }

  /**
   * Create Performance Observer for specific entry types
   */
  observePerformanceEntry(entryType, callback) {
    try {
      const observer = new PerformanceObserver((list) => {
        for (const entry of list.getEntries()) {
          callback(entry);
        }
      });

      observer.observe({ type: entryType, buffered: true });
      this.observers.push(observer);
    } catch (e) {
      console.warn(`[Performance] Failed to observe ${entryType}:`, e);
    }
  }

  /**
   * Monitor long tasks (> 50ms)
   */
  monitorLongTasks() {
    if ('PerformanceObserver' in window) {
      try {
        const observer = new PerformanceObserver((list) => {
          for (const entry of list.getEntries()) {
            const metric = {
              name: 'Long Task',
              value: entry.duration,
              startTime: entry.startTime,
              timestamp: Date.now()
            };
            this.recordMetric(metric);

            // Log warning for very long tasks
            if (entry.duration > 200) {
              console.warn('[Performance] Long task detected:', entry.duration, 'ms');
            }
          }
        });

        observer.observe({ type: 'longtask', buffered: true });
        this.observers.push(observer);
      } catch (e) {
        console.warn('[Performance] Long task monitoring not supported');
      }
    }
  }

  /**
   * Monitor resource loading performance
   */
  monitorResourceTiming() {
    if (window.performance && window.performance.getEntriesByType) {
      window.addEventListener('load', () => {
        const resources = window.performance.getEntriesByType('resource');

        // Analyze slow resources
        const slowResources = resources.filter(r => r.duration > 1000);
        if (slowResources.length > 0) {
          console.warn('[Performance] Slow resources detected:', slowResources);
        }

        // Calculate total resource load time
        const totalResourceTime = resources.reduce((sum, r) => sum + r.duration, 0);
        const metric = {
          name: 'Total Resource Load Time',
          value: totalResourceTime,
          resourceCount: resources.length,
          timestamp: Date.now()
        };
        this.recordMetric(metric);
      });
    }
  }

  /**
   * Record a performance metric
   */
  recordMetric(metric) {
    this.metrics.push(metric);

    // Log in development
    if (process.env.NODE_ENV === 'development') {
      console.log(`[Performance] ${metric.name}:`, metric.value, metric.rating ? `(${metric.rating})` : '');
    }

    // Send to analytics endpoint
    this.sendToAnalytics(metric);
  }

  /**
   * Send metric to analytics service
   */
  async sendToAnalytics(metric) {
    try {
      // Send to backend analytics endpoint
      await fetch('/api/analytics/performance', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          ...metric,
          url: window.location.href,
          userAgent: navigator.userAgent
        }),
        keepalive: true
      });
    } catch (e) {
      // Silent fail - don't impact user experience
    }
  }

  /**
   * Custom performance marks
   */
  mark(name) {
    if (window.performance && window.performance.mark) {
      window.performance.mark(name);
      this.customMarks.set(name, Date.now());
    }
  }

  /**
   * Measure time between two marks
   */
  measure(name, startMark, endMark) {
    if (window.performance && window.performance.measure) {
      try {
        window.performance.measure(name, startMark, endMark);
        const measure = window.performance.getEntriesByName(name)[0];

        const metric = {
          name,
          value: measure.duration,
          timestamp: Date.now()
        };
        this.recordMetric(metric);

        return measure.duration;
      } catch (e) {
        console.warn('[Performance] Failed to measure:', e);
      }
    }
  }

  /**
   * Get all recorded metrics
   */
  getMetrics() {
    return [...this.metrics];
  }

  /**
   * Get metrics summary
   */
  getSummary() {
    const vitals = {};

    ['LCP', 'FID', 'CLS', 'FCP', 'TTFB'].forEach(name => {
      const metric = this.metrics.filter(m => m.name === name).pop();
      if (metric) {
        vitals[name] = {
          value: metric.value,
          rating: metric.rating
        };
      }
    });

    return {
      vitals,
      longTaskCount: this.metrics.filter(m => m.name === 'Long Task').length,
      totalMetrics: this.metrics.length
    };
  }

  /**
   * Clean up observers
   */
  cleanup() {
    this.observers.forEach(observer => observer.disconnect());
    this.observers = [];
    this.isInitialized = false;
  }
}

// Singleton instance
const performanceMonitor = new PerformanceMonitor();

/**
 * Initialize performance monitoring
 */
export function initializePerformanceMonitoring() {
  performanceMonitor.initialize();
}

/**
 * Create a performance mark
 */
export function mark(name) {
  performanceMonitor.mark(name);
}

/**
 * Measure time between marks
 */
export function measure(name, startMark, endMark) {
  return performanceMonitor.measure(name, startMark, endMark);
}

/**
 * Get performance metrics
 */
export function getPerformanceMetrics() {
  return performanceMonitor.getMetrics();
}

/**
 * Get performance summary
 */
export function getPerformanceSummary() {
  return performanceMonitor.getSummary();
}

/**
 * Cleanup performance monitoring
 */
export function cleanupPerformanceMonitoring() {
  performanceMonitor.cleanup();
}

export default performanceMonitor;
