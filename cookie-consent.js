(function () {
  var STORAGE_KEY = 'driveflow_cookie_consent';
  var GA_ID = 'G-EJB69589QP';
  var ADS_ID = 'AW-17936809057';

  window.dataLayer = window.dataLayer || [];
  function gtag() {
    window.dataLayer.push(arguments);
  }
  window.gtag = window.gtag || gtag;

  // Consent Mode defaults: denied until the user Accepts
  gtag('consent', 'default', {
    ad_storage: 'denied',
    ad_user_data: 'denied',
    ad_personalization: 'denied',
    analytics_storage: 'denied',
    functionality_storage: 'granted',
    security_storage: 'granted',
    wait_for_update: 500
  });

  function getChoice() {
    try {
      return localStorage.getItem(STORAGE_KEY);
    } catch (e) {
      return null;
    }
  }

  function setChoice(value) {
    try {
      localStorage.setItem(STORAGE_KEY, value);
    } catch (e) {}
  }

  function hasAccepted() {
    return getChoice() === 'accepted';
  }

  function loadScript(src, id) {
    if (id && document.getElementById(id)) return;
    var s = document.createElement('script');
    if (id) s.id = id;
    s.async = true;
    s.src = src;
    document.head.appendChild(s);
  }

  function enableAnalytics() {
    gtag('consent', 'update', {
      ad_storage: 'granted',
      ad_user_data: 'granted',
      ad_personalization: 'granted',
      analytics_storage: 'granted'
    });

    if (!window.__driveflowAnalyticsLoaded) {
      window.__driveflowAnalyticsLoaded = true;
      loadScript(
        'https://www.googletagmanager.com/gtag/js?id=' + GA_ID,
        'driveflow-ga-gtag'
      );
      gtag('js', new Date());
      gtag('config', GA_ID);
      gtag('config', ADS_ID);
      loadScript(
        'https://www.googletagmanager.com/gtag/js?id=' + ADS_ID,
        'google-ads-gtag'
      );
    }

    window.dispatchEvent(new CustomEvent('driveflow:cookie-consent', {
      detail: { accepted: true }
    }));
  }

  function denyAnalytics() {
    gtag('consent', 'update', {
      ad_storage: 'denied',
      ad_user_data: 'denied',
      ad_personalization: 'denied',
      analytics_storage: 'denied'
    });
    window.dispatchEvent(new CustomEvent('driveflow:cookie-consent', {
      detail: { accepted: false }
    }));
  }

  function hideBanner() {
    var el = document.getElementById('driveflow-cookie-banner');
    if (el) el.remove();
  }

  function showBanner() {
    if (document.getElementById('driveflow-cookie-banner')) return;

    var style = document.createElement('style');
    style.textContent =
      '#driveflow-cookie-banner{position:fixed;left:16px;right:16px;bottom:16px;z-index:99999;max-width:640px;margin:0 auto;background:#1a1a1a;color:#fff;border-radius:16px;padding:18px 20px;box-shadow:0 8px 32px rgba(0,0,0,.25);font-family:Inter,-apple-system,BlinkMacSystemFont,Segoe UI,sans-serif;font-size:14px;line-height:1.5}' +
      '#driveflow-cookie-banner p{margin:0 0 14px}' +
      '#driveflow-cookie-banner a{color:#fff;text-decoration:underline}' +
      '#driveflow-cookie-banner .df-cookie-actions{display:flex;gap:10px;flex-wrap:wrap;justify-content:flex-end}' +
      '#driveflow-cookie-banner button{border:none;border-radius:999px;padding:10px 16px;font-weight:600;font-size:13px;cursor:pointer}' +
      '#driveflow-cookie-banner .df-accept{background:#fff;color:#1a1a1a}' +
      '#driveflow-cookie-banner .df-reject{background:transparent;color:#fff;border:1px solid rgba(255,255,255,.35)}';
    document.head.appendChild(style);

    var banner = document.createElement('div');
    banner.id = 'driveflow-cookie-banner';
    banner.setAttribute('role', 'dialog');
    banner.setAttribute('aria-live', 'polite');
    banner.setAttribute('aria-label', 'Cookie consent');
    banner.innerHTML =
      '<p>We use essential cookies to run the site. Analytics and advertising cookies (Google Analytics / Google Ads) are used only if you Accept. See our <a href="/cookie-policy.html">Cookie Policy</a> and <a href="/privacy.html">Privacy Policy</a>.</p>' +
      '<div class="df-cookie-actions">' +
      '<button type="button" class="df-reject">Reject</button>' +
      '<button type="button" class="df-accept">Accept</button>' +
      '</div>';

    function mount() {
      document.body.appendChild(banner);
      banner.querySelector('.df-accept').addEventListener('click', function () {
        setChoice('accepted');
        hideBanner();
        enableAnalytics();
      });
      banner.querySelector('.df-reject').addEventListener('click', function () {
        setChoice('rejected');
        hideBanner();
        denyAnalytics();
      });
    }

    if (document.body) mount();
    else document.addEventListener('DOMContentLoaded', mount);
  }

  window.DriveflowCookieConsent = {
    hasAccepted: hasAccepted,
    getChoice: getChoice,
    accept: function () {
      setChoice('accepted');
      hideBanner();
      enableAnalytics();
    },
    reject: function () {
      setChoice('rejected');
      hideBanner();
      denyAnalytics();
    }
  };

  var choice = getChoice();
  if (choice === 'accepted') {
    enableAnalytics();
  } else if (choice === 'rejected') {
    denyAnalytics();
  } else {
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', showBanner);
    } else {
      showBanner();
    }
  }
})();
