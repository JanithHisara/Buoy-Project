/**
 * OceanNav — Common JavaScript (theme, sidebar, toast, logout)
 */

// ── Theme Toggle ──
function toggleTheme() {
    const html = document.documentElement;
    const current = html.getAttribute('data-theme');
    const next = current === 'dark' ? 'light' : 'dark';
    html.setAttribute('data-theme', next);
    localStorage.setItem('oceannav-theme', next);
    const label = document.getElementById('theme-label');
    if (label) label.textContent = next === 'dark' ? 'Dark' : 'Light';
}

// Apply saved theme on load
(function() {
    const saved = localStorage.getItem('oceannav-theme') || 'dark';
    document.documentElement.setAttribute('data-theme', saved);
    const label = document.getElementById('theme-label');
    if (label) label.textContent = saved === 'dark' ? 'Dark' : 'Light';
})();

// ── Sidebar Toggle ──
const sidebarToggle = document.getElementById('sidebar-toggle');
if (sidebarToggle) {
    sidebarToggle.addEventListener('click', () => {
        const sidebar = document.getElementById('sidebar');
        sidebar.classList.toggle('collapsed');
    });
}

// ── Logout ──
async function logout() {
    try {
        await fetch('/logout', { method: 'POST' });
        window.location.href = '/';
    } catch (e) {
        window.location.href = '/';
    }
}

// ── Inactivity Auto-Logout ──
let inactivityTimer;
let sessionTimeoutSeconds = 300; // default 5 mins

async function initSessionTimeout() {
    try {
        const settings = await fetchJSON('/api/settings');
        if (settings.session_timeout) {
            sessionTimeoutSeconds = parseInt(settings.session_timeout);
        }
    } catch (e) {
        console.error('Failed to fetch settings for timeout:', e);
    }

    resetInactivityTimer();
    
    // Listen for activity to reset timer
    ['mousemove', 'keydown', 'mousedown', 'touchstart', 'scroll'].forEach(event => {
        document.addEventListener(event, resetInactivityTimer, { passive: true });
    });
}

function resetInactivityTimer() {
    clearTimeout(inactivityTimer);
    inactivityTimer = setTimeout(() => {
        showToast('Session expired due to inactivity. Logging out...', 'warning');
        setTimeout(logout, 2000);
    }, sessionTimeoutSeconds * 1000);
}

document.addEventListener('DOMContentLoaded', () => {
    // Start inactivity timer on all pages except login page
    if (window.location.pathname !== '/' && window.location.pathname !== '/login') {
        initSessionTimeout();
    }
});

// ── Toast Notifications ──
function showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    if (!container) return;

    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.innerHTML = message;
    container.appendChild(toast);

    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateX(100px)';
        setTimeout(() => toast.remove(), 300);
    }, 4000);
}

// ── Fetch JSON Helper ──
async function fetchJSON(url, options = {}) {
    const defaults = {
        headers: { 'Content-Type': 'application/json' },
        cache: 'no-store'
    };
    const response = await fetch(url, { ...defaults, ...options });
    return response.json();
}

// ── Load Stats ──
async function loadStats() {
    try {
        const stats = await fetchJSON('/api/stats');
        const totalEl = document.getElementById('total-buoys');
        const activeEl = document.getElementById('active-buoys');
        const warningEl = document.getElementById('warning-buoys');
        const lostEl = document.getElementById('signal-lost');
        if (totalEl) totalEl.textContent = stats.total_buoys;
        if (activeEl) activeEl.textContent = stats.active_buoys;
        if (warningEl) warningEl.textContent = stats.warning_buoys || 0;
        if (lostEl) lostEl.textContent = stats.signal_lost;

        // Update device count badge
        const badge = document.getElementById('device-count-badge');
        if (badge) badge.textContent = stats.total_buoys;
    } catch (e) {
        console.error('Failed to load stats:', e);
    }
}

// Load stats on pages that need it
if (document.getElementById('total-buoys') || document.getElementById('device-count-badge')) {
    loadStats();
}

// ── Create MapLibre Map ──
async function createMap(containerId, options = {}) {
    let style = null;
    try {
        const res = await fetch('/static/map-style.json');
        style = await res.json();
        if (style && style.sources && style.sources.openmaptiles) {
            style.sources.openmaptiles.tiles = [
                window.location.origin + '/tiles/{z}/{x}/{y}.pbf'
            ];
        }
    } catch (e) {
        console.error('Failed to load map style', e);
        style = '/static/map-style.json'; // fallback
    }

    const defaults = {
        container: containerId,
        style: style,
        center: [79.86, 6.93],  // Sri Lanka default
        zoom: 13,
        attributionControl: false
    };
    return new maplibregl.Map({ ...defaults, ...options });
}

// ── Distance calculation (Haversine) ──
function getDistanceKm(lat1, lon1, lat2, lon2) {
    const R = 6371;
    const dLat = (lat2 - lat1) * Math.PI / 180;
    const dLon = (lon2 - lon1) * Math.PI / 180;
    const a = Math.sin(dLat/2) * Math.sin(dLat/2) +
              Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
              Math.sin(dLon/2) * Math.sin(dLon/2);
    return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
}

// ── Generate circle GeoJSON for LoRa range ──
function createCircleGeoJSON(center, radiusKm, points = 64) {
    const coords = [];
    const distanceX = radiusKm / (111.32 * Math.cos(center[1] * Math.PI / 180));
    const distanceY = radiusKm / 110.574;
    for (let i = 0; i < points; i++) {
        const theta = (i / points) * 2 * Math.PI;
        const x = distanceX * Math.cos(theta);
        const y = distanceY * Math.sin(theta);
        coords.push([center[0] + x, center[1] + y]);
    }
    coords.push(coords[0]);
    return {
        type: 'Feature',
        geometry: { type: 'Polygon', coordinates: [coords] }
    };
}

// ── Global Live Location Poller ──

