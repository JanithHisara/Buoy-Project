/**
 * OceanNav — Settings Logic
 */

const SETTING_GROUPS = {
    device: ['auto_scan_gps', 'auto_connect_startup', 'baud_rate', 'gps_poll_interval', 'led_blink_off_time'],
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
        const [settings, wifiSettings] = await Promise.all([
            fetchJSON('/api/settings'),
            fetchJSON('/api/settings/wifi')
        ]);

        for (const [key, value] of Object.entries(settings)) {
            const el = document.getElementById(key);
            if (!el) continue;

            if (TOGGLE_SETTINGS.includes(key)) {
                el.checked = value === 'true';
            } else {
                el.value = value;
            }
        }
        
        if (wifiSettings && wifiSettings.success) {
            if (document.getElementById('wifi_ssid')) document.getElementById('wifi_ssid').value = wifiSettings.ssid || '';
            if (document.getElementById('wifi_password')) document.getElementById('wifi_password').value = wifiSettings.password || '';
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

async function saveWifiSettings() {
    const ssid = document.getElementById('wifi_ssid').value.trim();
    const password = document.getElementById('wifi_password').value;

    if (!ssid) {
        showToast('Please enter a WiFi SSID', 'error');
        return;
    }

    try {
        const res = await fetchJSON('/api/settings/wifi', {
            method: 'POST',
            body: JSON.stringify({ ssid, password })
        });
        
        if (res.success) {
            showToast(res.message, 'success');
        } else {
            showToast(res.error || 'Failed to save WiFi settings', 'error');
        }
    } catch (e) {
        showToast('Error saving WiFi settings', 'error');
        console.error(e);
    }
}
