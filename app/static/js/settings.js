/**
 * OceanNav — Settings Logic
 */

const SETTING_GROUPS = {
    device: ['auto_scan_gps', 'auto_connect_startup', 'baud_rate', 'gps_poll_interval'],
    map: ['show_buoy_trails', 'auto_center_gps', 'default_zoom', 'offline_tiles_cache'],
    alert: ['low_battery_alert', 'offline_buoy_alert', 'gps_drift_alert'],
    security: ['two_factor_auth', 'session_timeout', 'api_access_logs']
};

const TOGGLE_SETTINGS = [
    'auto_scan_gps', 'auto_connect_startup', 'show_buoy_trails', 'auto_center_gps',
    'offline_tiles_cache', 'low_battery_alert', 'offline_buoy_alert', 'gps_drift_alert',
    'two_factor_auth', 'api_access_logs'
];

document.addEventListener('DOMContentLoaded', () => {
    loadSettings();
});

async function loadSettings() {
    try {
        const settings = await fetchJSON('/api/settings');

        for (const [key, value] of Object.entries(settings)) {
            const el = document.getElementById(key);
            if (!el) continue;

            if (TOGGLE_SETTINGS.includes(key)) {
                el.checked = value === 'true';
            } else {
                el.value = value;
            }
        }
    } catch (e) {
        console.error('Failed to load settings:', e);
    }
}

async function saveSettings(group) {
    const keys = SETTING_GROUPS[group];
    if (!keys) return;

    const data = {};
    for (const key of keys) {
        const el = document.getElementById(key);
        if (!el) continue;

        if (TOGGLE_SETTINGS.includes(key)) {
            data[key] = el.checked ? 'true' : 'false';
        } else {
            data[key] = el.value;
        }
    }

    try {
        const res = await fetchJSON('/api/settings', {
            method: 'PUT',
            body: JSON.stringify(data)
        });
        if (res.success) {
            showToast('Settings saved successfully', 'success');
        } else {
            showToast(res.message || 'Error saving settings', 'error');
        }
    } catch (e) {
        showToast('Error saving settings', 'error');
        console.error(e);
    }
}

function downloadApiLogs() {
    window.location.href = '/api/logs/export';
}
