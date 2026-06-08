/**
 * Analytics Utility
 * Flexible analytics tracking supporting multiple providers
 */

import { getApiBaseUrl } from '../lib/api';

// Get the API base URL from the centralized config
const API_BASE_URL = getApiBaseUrl();
// Global tracking cache to prevent duplicate events
const eventCache = new Map();
const EVENT_DEBOUNCE_TIME = 2000; // 2 seconds

/**
 * Track an analytics event
 * @param {string} eventName - The name of the event to track
 * @param {object} properties - Additional properties for the event
 */
export const trackEvent = (eventName, properties = {}) => {
  // Create a unique key for this event
  const eventKey = `${eventName}_${JSON.stringify(properties)}`;
  const now = Date.now();
  
  // Check if this exact event was recently tracked
  if (eventCache.has(eventKey)) {
    const lastTracked = eventCache.get(eventKey);
    if (now - lastTracked < EVENT_DEBOUNCE_TIME) {
      // Skip duplicate event within debounce window
      return;
    }
  }
  
  // Update cache with current timestamp
  eventCache.set(eventKey, now);
  
  // Clean up old entries from cache (keep only last 5 minutes)
  const fiveMinutesAgo = now - 300000;
  for (const [key, timestamp] of eventCache.entries()) {
    if (timestamp < fiveMinutesAgo) {
      eventCache.delete(key);
    }
  }
  
  // Google Analytics 4
  // if (typeof window !== 'undefined' && window.gtag) {
  //   window.gtag('event', eventName, properties);
  // }
  
  // // Custom backend tracking
  // if (typeof window !== 'undefined' && window.fetch) {
  //   fetch(`${API_BASE_URL}/api/analytics/track`, {
  //     method: 'POST',
  //     headers: { 'Content-Type': 'application/json' },
  //     body: JSON.stringify({ event: eventName, timestamp: now, ...properties })
  //   }).catch(() => {}); // Fail silently
  // }
  
  // Console log for development
  // if (process.env.NODE_ENV === 'development') {
  //   console.log('📊 Analytics Event:', eventName, properties);
  // }
};

/**
 * Track page view
 * @param {string} pageName - Name of the page
 * @param {object} properties - Additional properties
 */
export const trackPageView = (pageName, properties = {}) => {
  trackEvent('page_view', { page: pageName, ...properties });
};

/**
 * Track section visibility using Intersection Observer
 * @param {string} sectionName - Name of the section
 * @param {HTMLElement} element - The DOM element to observe
 * @param {function} callback - Optional callback when section is viewed
 */
export const trackSectionView = (sectionName, element, callback) => {
  if (typeof window === 'undefined' || !element) return;

  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          trackEvent('section_view', { section: sectionName });
          if (callback) callback();
          observer.unobserve(entry.target);
        }
      });
    },
    { threshold: 0.3 }
  );

  observer.observe(element);
  return observer;
};

/**
 * Track scroll depth
 * Uses throttling to limit API calls - only checks every 500ms
 */
export const initScrollDepthTracking = () => {
  if (typeof window === 'undefined') return;

  const depths = [25, 50, 75, 100];
  const tracked = new Set();
  let isThrottled = false;

  const trackScrollDepth = () => {
    // Throttle: only run once every 500ms
    if (isThrottled) return;
    isThrottled = true;
    setTimeout(() => { isThrottled = false; }, 500);

    const scrollPercentage = Math.round(
      ((window.scrollY + window.innerHeight) / document.documentElement.scrollHeight) * 100
    );

    depths.forEach((depth) => {
      if (scrollPercentage >= depth && !tracked.has(depth)) {
        tracked.add(depth);
        trackEvent('scroll_depth', { depth: `${depth}%` });
      }
    });
  };

  window.addEventListener('scroll', trackScrollDepth, { passive: true });
  return () => window.removeEventListener('scroll', trackScrollDepth);
};

/**
 * Track time on page
 * Only tracks specific milestones: 30s, 60s, 120s, 300s and on page unload
 * This prevents continuous API calls
 */
export const initTimeOnPageTracking = () => {
  if (typeof window === 'undefined') return;

  const startTime = Date.now();
  const milestones = [30, 60, 120, 300]; // Track at 30s, 1min, 2min, 5min
  const tracked = new Set();

  const trackTimeOnPage = () => {
    const timeSpent = Math.round((Date.now() - startTime) / 1000);
    trackEvent('time_on_page', { seconds: timeSpent });
  };

  // Check milestones
  const checkMilestone = () => {
    const timeSpent = Math.round((Date.now() - startTime) / 1000);
    milestones.forEach((milestone) => {
      if (timeSpent >= milestone && !tracked.has(milestone)) {
        tracked.add(milestone);
        trackEvent('time_milestone', { seconds: milestone });
      }
    });
  };

  // Track on page unload
  window.addEventListener('beforeunload', trackTimeOnPage);
  
  // Check milestones every 10 seconds (not every second)
  const interval = setInterval(checkMilestone, 10000);

  return () => {
    window.removeEventListener('beforeunload', trackTimeOnPage);
    clearInterval(interval);
  };
};

/**
 * Track CTA clicks
 * @param {string} ctaName - Name/location of the CTA
 * @param {string} destination - Where the CTA leads
 */
export const trackCTAClick = (ctaName, destination = '') => {
  trackEvent('cta_click', { cta_name: ctaName, destination });
};

/**
 * Track form interactions
 * @param {string} formName - Name of the form
 * @param {string} action - Action performed (start, submit, error)
 */
export const trackFormInteraction = (formName, action, properties = {}) => {
  trackEvent('form_interaction', { form: formName, action, ...properties });
};

