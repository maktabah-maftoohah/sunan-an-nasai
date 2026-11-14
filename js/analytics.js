/**
 * Maktabah Maftoohah Sunan an-Nasa'i - Analytics Module (analytics.js)
 * Google Tag Manager (GTM) and Google Analytics 4 (GA4) integration
 * with SPA virtual pageview tracking and specialized Hadith metrics.
 */

const DEFAULT_CONTAINER_ID = 'GTM-XXXXXXXX';

class AnalyticsService {
  constructor() {
    this.initialized = false;
    this.containerId = null;
    this.lastTrackedPath = null;
  }

  getContainerId() {
    try {
      const stored = localStorage.getItem('maktabah_ga_id');
      if (stored && stored.trim()) return stored.trim();
    } catch {
      // ignore localStorage
    }
    return DEFAULT_CONTAINER_ID;
  }

  init(customId = null) {
    if (this.initialized) return;

    this.containerId = customId || this.getContainerId();

    if (!this.containerId || this.containerId === 'GTM-XXXXXXXX' || this.containerId === 'G-XXXXXXXXXX') {
      return;
    }

    if (typeof navigator !== 'undefined') {
      const dnt = navigator.doNotTrack || window.doNotTrack || navigator.msDoNotTrack;
      if (dnt === '1' || dnt === 'yes') {
        return;
      }
    }

    window.dataLayer = window.dataLayer || [];
    window.gtag = window.gtag || function() {
      window.dataLayer.push(arguments);
    };

    window.gtag('js', new Date());

    if (this.containerId.startsWith('GTM-')) {
      const script = document.createElement('script');
      script.async = true;
      script.src = `https://www.googletagmanager.com/gtm.js?id=${encodeURIComponent(this.containerId)}`;
      document.head.appendChild(script);
    } else if (this.containerId.startsWith('G-')) {
      const script = document.createElement('script');
      script.async = true;
      script.src = `https://www.googletagmanager.com/gtag/js?id=${encodeURIComponent(this.containerId)}`;
      document.head.appendChild(script);
      window.gtag('config', this.containerId, {
        send_page_view: false
      });
    }

    this.initialized = true;
  }

  trackPageView(pagePath, pageTitle) {
    if (!this.initialized && !window.dataLayer) return;
    if (this.lastTrackedPath === pagePath) return;
    this.lastTrackedPath = pagePath;

    const eventPayload = {
      event: 'virtual_pageview',
      page_path: pagePath,
      page_title: pageTitle,
      page_location: window.location.href
    };

    if (window.dataLayer) {
      window.dataLayer.push(eventPayload);
    }

    if (typeof window.gtag === 'function' && this.containerId && this.containerId.startsWith('G-')) {
      window.gtag('event', 'page_view', {
        page_title: pageTitle,
        page_location: window.location.href,
        page_path: pagePath
      });
    }
  }

  trackEvent(eventName, params = {}) {
    if (!this.initialized && !window.dataLayer) return;

    const payload = {
      event: eventName,
      ...params
    };

    if (window.dataLayer) {
      window.dataLayer.push(payload);
    }

    if (typeof window.gtag === 'function') {
      window.gtag('event', eventName, params);
    }
  }

  trackHadithView(hadithNumber, bookNumber, bookTitle) {
    this.trackEvent('view_item', {
      item_type: 'hadith',
      item_id: String(hadithNumber),
      item_name: `Sunan an-Nasa'i #${hadithNumber}`,
      item_category: 'hadith',
      item_category2: bookTitle,
      book_number: bookNumber,
      hadith_number: hadithNumber
    });
  }

  trackShare(hadithNumber, method = 'copy_link') {
    this.trackEvent('share', {
      method: method,
      content_type: 'hadith',
      item_id: String(hadithNumber)
    });
  }

  trackSearch(query, resultCount = 0) {
    if (!query || !query.trim()) return;
    this.trackEvent('search', {
      search_term: query.trim(),
      result_count: resultCount
    });
  }
}

export const analytics = new AnalyticsService();
