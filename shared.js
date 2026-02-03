(function () {
    const routesEl = document.getElementById('routes');
    if (!routesEl) return;

    const routeKey = routesEl.dataset.route;
    if (!routeKey) return;

    const API_URL = location.hostname === "localhost" || location.hostname === "127.0.0.1"
        ? "http://localhost:8080"
        : "https://driving-test-backend-production.up.railway.app";

    let accessToken = null;
    let routesData = null;
    let tokenExpiresAt = null;
    let hasLicense = false;
    let licenseExpiresAt = null;
    let currentApiSlug = null;

    function deriveCentreName() {
        const h1 = document.querySelector('h1');
        if (!h1 || !h1.textContent) return '';
        return h1.textContent.replace(/\s*Driving Test Routes.*$/i, '').trim();
    }

    function formatCentreName(fallback) {
        const name = deriveCentreName() || fallback || routeKey.replace(/-/g, ' ');
        return name;
    }

    async function loadConfig() {
        try {
            const res = await fetch('/routes-config.json');
            if (!res.ok) return {};
            return await res.json();
        } catch (err) {
            return {};
        }
    }

    function renderSharedSections(centreName) {
        routesEl.innerHTML = `
            <div id="errorContainer"></div>
            <div id="paywallContainer" style="display: none; border-radius: var(--radius-xl); background: var(--bg-card); border: 1px solid var(--border-subtle); box-shadow: var(--shadow-card); padding: 40px; margin-bottom: 40px; text-align: center;">
                <h2 style="margin: 0 0 16px; color: var(--accent); font-size: 28px; font-weight: 800;">Access Required</h2>
                <p style="margin: 0 0 24px; color: var(--text-main); font-size: 16px; line-height: 1.7;">Please log in or purchase access to view the ${centreName} driving test routes.</p>
                <div style="display: flex; gap: 16px; justify-content: center; flex-wrap: wrap;">
                    <a href="/login.html" class="route-btn" style="display: inline-block; text-decoration: none; width: auto; padding: 12px 24px;">Log In</a>
                    <a href="/payment.html" class="route-btn" style="display: inline-block; text-decoration: none; width: auto; padding: 12px 24px; background: var(--accent);">Purchase Access</a>
                </div>
            </div>
            <div id="routesContainer" class="routes-container"></div>
            <div id="loadingContainer" class="loading">Loading routes...</div>
        `;

        const purchaseEl = document.getElementById('sharedPurchase');
        if (purchaseEl) {
            purchaseEl.innerHTML = `
                <div id="purchaseSection" style="display: none; margin-top: 40px; text-align: center; padding: 40px; background: var(--bg-card); border: 1px solid var(--border-subtle); border-radius: var(--radius-xl); box-shadow: var(--shadow-card);">
                    <h3 style="margin: 0 0 16px; color: var(--text-main); font-size: 24px; font-weight: 700;">Ready to Practice These Routes?</h3>
                    <p style="margin: 0 0 24px; color: var(--text-muted); font-size: 16px; line-height: 1.6;">Get instant access to all ${centreName} driving test routes for just €11.99</p>
                    <a href="/payment.html" class="route-btn" style="display: inline-block; text-decoration: none; width: auto; padding: 14px 32px; font-size: 16px; font-weight: 600;">Buy Now - €11.99</a>
                </div>
            `;
        }

        const footerEl = document.getElementById('sharedFooter');
        if (footerEl) {
            fetch('/route-footer.html')
                .then((response) => response.text())
                .then((html) => {
                    footerEl.innerHTML = html;
                })
                .catch((err) => {
                    console.error('Failed to load route footer:', err);
                });
        }
    }

    async function checkLicenseStatus() {
        const token = localStorage.getItem('auth_token');
        if (!token) {
            hasLicense = false;
            return;
        }

        try {
            const response = await fetch(`${API_URL}/routes/license-status`, {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });

            if (response.ok) {
                const data = await response.json();
                hasLicense = data.hasLicense || false;
                licenseExpiresAt = data.expiresAt;

                if (hasLicense && licenseExpiresAt) {
                    const expiryDate = new Date(licenseExpiresAt);
                    const now = new Date();
                    if (expiryDate < now) {
                        hasLicense = false;
                    }
                }
            } else {
                hasLicense = false;
            }
        } catch (err) {
            console.error('Error checking license:', err);
            hasLicense = false;
        }
    }

    function showPaywall() {
        window.location.href = '/payment.html';
    }

    async function loadRoutes(apiSlug, centreName) {
        const loadingContainer = document.getElementById('loadingContainer');
        const routesContainer = document.getElementById('routesContainer');
        const errorContainer = document.getElementById('errorContainer');
        const token = localStorage.getItem('auth_token');

        try {
            const tokenResponse = await fetch(`${API_URL}/routes/generate-${apiSlug}-token`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });

            if (!tokenResponse.ok) {
                const error = await tokenResponse.json();
                if (error.error && error.error.includes('license')) {
                    const paywallContainer = document.getElementById('paywallContainer');
                    if (paywallContainer) {
                        paywallContainer.style.display = 'block';
                    }
                    loadingContainer.style.display = 'none';
                    routesContainer.style.display = 'none';
                    return;
                } else {
                    errorContainer.innerHTML = `
                        <div class="error">
                            <strong>Error</strong><br>
                            ${error.error || 'Failed to generate access token'}
                        </div>
                    `;
                }
                loadingContainer.style.display = 'none';
                return;
            }

            const tokenData = await tokenResponse.json();
            accessToken = tokenData.accessToken;
            tokenExpiresAt = new Date(tokenData.expiresAt);

            const dataResponse = await fetch(`${API_URL}/routes/${apiSlug}-data/${accessToken}`, {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });

            if (!dataResponse.ok) {
                const error = await dataResponse.json();
                throw new Error(error.error || 'Failed to load routes');
            }

            routesData = await dataResponse.json();
            displayRoutes(apiSlug, routesData);

            loadingContainer.style.display = 'none';
        } catch (err) {
            console.error('Error loading routes:', err);
            errorContainer.innerHTML = `
                <div class="error">
                    <strong>Error</strong><br>
                    ${err.message || 'Failed to load routes. Please try again.'}
                </div>
            `;
            loadingContainer.style.display = 'none';
        }
    }

    function displayRoutes(apiSlug, data) {
        const routesContainer = document.getElementById('routesContainer');

        if (data.message && (!data.routes || data.routes.length === 0)) {
            const countdownKey = `routeReleaseCountdown_${apiSlug}`;
            let startTime = localStorage.getItem(countdownKey);

            if (!startTime) {
                startTime = Date.now() + (12 * 60 * 60 * 1000);
                localStorage.setItem(countdownKey, startTime.toString());
            } else {
                startTime = parseInt(startTime, 10);
            }

            function updateCountdown() {
                const now = Date.now();
                const timeLeft = startTime - now;

                if (timeLeft <= 0) {
                    routesContainer.innerHTML = `
                        <div style="text-align: center; padding: 40px; background: var(--bg-card); border-radius: var(--radius-xl); border: 1px solid var(--border-subtle);">
                            <h3 style="color: var(--accent); margin-bottom: 16px;">Routes Coming Soon</h3>
                            <p style="color: var(--text-main); font-size: 16px; line-height: 1.6;">Routes are being finalized and will be available very soon!</p>
                        </div>
                    `;
                    return;
                }

                const hours = Math.floor(timeLeft / (1000 * 60 * 60));
                const minutes = Math.floor((timeLeft % (1000 * 60 * 60)) / (1000 * 60));
                const seconds = Math.floor((timeLeft % (1000 * 60)) / 1000);

                routesContainer.innerHTML = `
                    <div style="text-align: center; padding: 40px; background: var(--bg-card); border-radius: var(--radius-xl); border: 1px solid var(--border-subtle);">
                        <h3 style="color: var(--accent); margin-bottom: 16px;">Routes Coming Soon</h3>
                        <p style="color: var(--text-main); font-size: 16px; line-height: 1.6; margin-bottom: 24px;">${data.message}</p>
                        <div style="background: var(--primary-soft); border: 2px solid var(--primary); border-radius: 16px; padding: 24px; margin: 24px 0;">
                            <div style="color: var(--text-muted); font-size: 14px; margin-bottom: 8px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;">Routes Will Be Released In</div>
                            <div style="display: flex; justify-content: center; gap: 16px; margin-top: 16px; flex-wrap: wrap;">
                                <div style="text-align: center;">
                                    <div style="font-size: 36px; font-weight: 800; color: var(--accent); line-height: 1;">${hours}</div>
                                    <div style="font-size: 12px; color: var(--text-muted); margin-top: 4px; text-transform: uppercase;">Hours</div>
                                </div>
                                <div style="font-size: 36px; font-weight: 800; color: var(--accent); line-height: 1;">:</div>
                                <div style="text-align: center;">
                                    <div style="font-size: 36px; font-weight: 800; color: var(--accent); line-height: 1;">${minutes.toString().padStart(2, '0')}</div>
                                    <div style="font-size: 12px; color: var(--text-muted); margin-top: 4px; text-transform: uppercase;">Minutes</div>
                                </div>
                                <div style="font-size: 36px; font-weight: 800; color: var(--accent); line-height: 1;">:</div>
                                <div style="text-align: center;">
                                    <div style="font-size: 36px; font-weight: 800; color: var(--accent); line-height: 1;">${seconds.toString().padStart(2, '0')}</div>
                                    <div style="font-size: 12px; color: var(--text-muted); margin-top: 4px; text-transform: uppercase;">Seconds</div>
                                </div>
                            </div>
                        </div>
                    </div>
                `;
            }

            updateCountdown();
            const countdownInterval = setInterval(() => {
                updateCountdown();
            }, 1000);

            window['countdownInterval_' + apiSlug] = countdownInterval;
            return;
        }

        if (!data.routes || data.routes.length === 0) {
            routesContainer.innerHTML = '<div class="loading">No routes available</div>';
            return;
        }

        routesContainer.innerHTML = data.routes.map((route, index) => {
            const hasManoeuvre = Boolean(route.manoeuvre);
            if (hasManoeuvre) {
                return `
                    <div class="route-card">
                        <h3>Route ${index + 1}</h3>
                        <div class="route-btn-group">
                            <button class="route-btn route-btn-main" onclick="openRoute(${route.id}, '${apiSlug}')">
                                View Route
                            </button>
                            <button class="route-btn route-btn-manoeuvre" onclick="openManoeuvre(${route.id}, '${apiSlug}')">
                                Manoeuvres
                            </button>
                        </div>
                    </div>
                `;
            }

            return `
                <div class="route-card">
                    <h3>Route ${index + 1}</h3>
                    <button class="route-btn" onclick="openRoute(${route.id}, '${apiSlug}')">
                        View Route ${index + 1} on Google Maps
                    </button>
                </div>
            `;
        }).join('');
    }

    async function openRoute(routeId, apiSlugOverride) {
        if (!accessToken) {
            alert('Access token not available. Please refresh the page.');
            return;
        }

        const activeSlug = apiSlugOverride || currentApiSlug || routeKey;
        if (!activeSlug) {
            alert('Route information not available. Please refresh the page.');
            return;
        }

        if (new Date() > tokenExpiresAt) {
            alert('Your access has expired. Please refresh the page to get a new token.');
            return;
        }

        const token = localStorage.getItem('auth_token');
        if (token && routesData) {
            try {
                const clickResponse = await fetch(`${API_URL}/routes/record-click`, {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${token}`,
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        centreName: routesData.location,
                        routeId: routeId
                    })
                });

                if (clickResponse.status === 429) {
                    const error = await clickResponse.json();
                    console.log(`Cooldown: ${error.minutesRemaining} minutes remaining`);
                }
            } catch (err) {
                console.error('Error recording route click:', err);
            }
        }

        window.location.href = `${API_URL}/routes/${activeSlug}-route/${accessToken}/${routeId}`;
    }

    window.openRoute = openRoute;

    async function openManoeuvre(routeId, apiSlugOverride) {
        if (!accessToken) {
            alert('Access token not available. Please refresh the page.');
            return;
        }

        const activeSlug = apiSlugOverride || currentApiSlug || routeKey;
        if (!activeSlug) {
            alert('Route information not available. Please refresh the page.');
            return;
        }

        if (new Date() > tokenExpiresAt) {
            alert('Your access has expired. Please refresh the page to get a new token.');
            return;
        }

        window.location.href = `${API_URL}/routes/${activeSlug}-manoeuvre/${accessToken}/${routeId}`;
    }

    window.openManoeuvre = openManoeuvre;

    window.addEventListener('DOMContentLoaded', async () => {
        const config = await loadConfig();
        const routeConfig = config[routeKey] || {};
        const apiSlug = routeConfig.apiSlug || routeKey;
        currentApiSlug = apiSlug;
        const centreName = formatCentreName(routeConfig.centreName);

        renderSharedSections(centreName);

        const token = localStorage.getItem('auth_token');
        const paywallContainer = document.getElementById('paywallContainer');
        const loadingContainer = document.getElementById('loadingContainer');
        const routesContainer = document.getElementById('routesContainer');
        const purchaseSection = document.getElementById('purchaseSection');

        if (!token) {
            paywallContainer.style.display = 'block';
            loadingContainer.style.display = 'none';
            routesContainer.style.display = 'none';
            return;
        }

        await loadRoutes(apiSlug, centreName);
    });
})();
