// Reports one page view to the visitmap Worker (see visitmap/). No cookies are set.
// Visiting any page with ?notrack stops counting this browser; ?track turns it back on.
(() => {
  'use strict';

  const script = document.currentScript;
  const { endpoint, site, host } = (script && script.dataset) || {};
  if (!endpoint || !site || location.hostname !== host) return;
  try {
    const params = new URLSearchParams(location.search);
    if (params.has('notrack')) localStorage.setItem('visits:ignore', '1');
    if (params.has('track')) localStorage.removeItem('visits:ignore');
    if (localStorage.getItem('visits:ignore') === '1') return;
  } catch {
    // Storage can be unavailable (private mode); counting continues without the opt-out.
  }
  if (navigator.globalPrivacyControl || navigator.doNotTrack === '1') return;

  const body = JSON.stringify({ site, page: location.pathname, ref: document.referrer });
  if (navigator.sendBeacon && navigator.sendBeacon(endpoint, body)) return;
  fetch(endpoint, { method: 'POST', body, keepalive: true, mode: 'no-cors' }).catch(() => {});
})();
