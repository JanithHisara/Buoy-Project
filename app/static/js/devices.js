/**
 * OceanNav — Device Setup Logic
 */

let isConnected = false;

document.addEventListener('DOMContentLoaded', () => {
    refreshPorts();
    loadDevicesList();
    checkConnectionStatus();
});

// ── Refresh COM ports ──
async function refreshPorts() {
    try {
        const ports = await fetchJSON('/api/ports');
        const mainSelect = document.getElementById('port-select');
        const buoySelect = document.getElementById('buoy-port-select');

        const options = ports.map(p => `<option value="${p}">${p}</option>`).join('');

        mainSelect.innerHTML = '<option value="">Select COM Port</option>' + options;
        buoySelect.innerHTML = '<option value="">Select buoyancy COM port</option>' + options;
    } catch (e) {
        console.error('Failed to refresh ports:', e);
    }
}

// ── Connect to COM port ──
async function connectPort() {
    const port = document.getElementById('port-select').value;
    if (!port) {
        showToast('Please select a COM port', 'warning');
        return;
    }

    const btn = document.getElementById('connect-btn');
    btn.textContent = 'Connecting...';
    btn.disabled = true;

    try {
        const res = await fetchJSON('/api/connect', {
            method: 'POST',
            body: JSON.stringify({ port })
        });

        if (res.success) {
            isConnected = true;
            btn.textContent = 'Disconnect';
            btn.classList.remove('btn-primary');
            btn.classList.add('btn-danger');
            btn.onclick = disconnectPort;
            showToast(`Connected to ${port}`, 'success');
        } else {
            showToast(res.error || 'Connection failed', 'error');
            btn.textContent = 'Connect';
        }
    } catch (e) {
        showToast('Connection error', 'error');
        btn.textContent = 'Connect';
    }

    btn.disabled = false;
}

// ── Disconnect ──
async function disconnectPort() {
    try {
        await fetchJSON('/api/disconnect', { method: 'POST' });
        isConnected = false;
        const btn = document.getElementById('connect-btn');
        btn.textContent = 'Connect';
        btn.classList.remove('btn-danger');
        btn.classList.add('btn-primary');
        btn.onclick = connectPort;
        showToast('Disconnected', 'info');
    } catch (e) {
        showToast('Disconnect error', 'error');
    }
}

// ── Check connection status ──
async function checkConnectionStatus() {
    try {
        const status = await fetchJSON('/api/status');
        if (status.connected) {
            isConnected = true;
            const btn = document.getElementById('connect-btn');
            btn.textContent = 'Disconnect';
            btn.classList.remove('btn-primary');
            btn.classList.add('btn-danger');
            btn.onclick = disconnectPort;

            // Set port in dropdown
            const select = document.getElementById('port-select');
            if (status.port) {
                for (let opt of select.options) {
                    if (opt.value === status.port) {
                        opt.selected = true;
                        break;
                    }
                }
            }
        }
    } catch (e) {
        console.error('Status check failed:', e);
    }
}

// ── Load devices list ──
async function loadDevicesList() {
    try {
        const [devices, updateStatus] = await Promise.all([
            fetchJSON('/api/devices'),
            fetchJSON('/api/update_status')
        ]);
        
        const container = document.getElementById('devices-list');

        // Update badge
        const badge = document.getElementById('device-count-badge');
        if (badge) badge.textContent = devices.length;

        if (!devices.length) {
            container.innerHTML = '<div class="empty-state">No devices added yet</div>';
            return;
        }

        container.innerHTML = devices.map(d => {
            const hasUpdate = updateStatus.buoy_version && d.firmware_version !== updateStatus.buoy_version;
            return `
            <div class="device-card ${d.is_bound === 0 ? 'unbound' : ''}">
                <div class="device-icon"><i class="ph-bold ph-broadcast"></i></div>
                <div class="device-info">
                    <div class="device-id">
                        <div class="buoy-dot ${d.status}" style="width: 10px; height: 10px; border-radius: 50%; display: inline-block; margin-right: 8px; background: ${d.status === 'online' ? 'var(--accent-green)' : d.status === 'warning' ? 'var(--accent-orange)' : 'var(--accent-red)'}"></div>
                        ${d.id}
                        ${d.is_bound === 0 ? '<span style="font-size: 10px; padding: 2px 6px; background: var(--accent-orange); color: #000; border-radius: 12px; margin-left: 8px; font-weight: bold;">UNBOUND</span>' : ''}
                    </div>
                    <div class="device-name">${d.name || 'Unnamed'}</div>
                    <div class="device-meta">
                        <span><i class="ph-bold ph-map-pin"></i> ${d.lat.toFixed(4)}, ${d.lon.toFixed(4)}</span>
                        <span><i class="ph-bold ph-clock"></i> ${d.last_gps_time || 'Never'}</span>
                        <span><i class="ph-bold ph-cpu"></i> FW: ${d.firmware_version || '1.0.0'}</span>
                        <span><i class="ph-bold ph-wifi-high"></i> ${d.ip_address || 'Offline'}</span>
                    </div>
                </div>
                <div class="device-actions">
                    <button class="btn btn-warning btn-sm" onclick="flashBuoy('${d.id}')" title="Test OTA Update"><i class="ph-bold ph-download-simple"></i> OTA Update</button>
                    ${d.is_bound === 0 
                        ? `<button class="btn btn-primary btn-sm" onclick="bindDevice('${d.id}')" title="Bind Device"><i class="ph-bold ph-link"></i> Bind</button>`
                        : `<button class="btn btn-warning btn-sm" onclick="unbindDevice('${d.id}')" title="Unbind Device"><i class="ph-bold ph-link-break"></i></button>`
                    }
                    <button class="btn btn-outline btn-sm" onclick="locateDevice('${d.id}')" title="Locate on map"><i class="ph-bold ph-map-pin"></i></button>
                    <button class="btn btn-danger btn-sm" onclick="deleteDevice('${d.id}')" title="Delete"><i class="ph-bold ph-trash"></i></button>
                </div>
            </div>`;
        }).join('');
    } catch (e) {
        console.error('Failed to load devices:', e);
    }
}

// ── Bind / Unbind Device ──
async function bindDevice(id) {
    try {
        const res = await fetchJSON(`/api/devices/${id}/bind`, { method: 'POST' });
        if (res.success) {
            showToast('Bind command sent to ' + id, 'success');
            loadDevicesList();
        } else {
            showToast(res.error || 'Failed to send bind command', 'error');
        }
    } catch (e) {
        showToast('Error binding device', 'error');
    }
}

async function unbindDevice(id) {
    if (!confirm('Are you sure you want to unbind this device? It will stop responding to commands until bound again.')) return;
    try {
        const res = await fetchJSON(`/api/devices/${id}/unbind`, { method: 'POST' });
        if (res.success) {
            showToast('Unbind command sent to ' + id, 'success');
            loadDevicesList();
        } else {
            showToast(res.error || 'Failed to send unbind command', 'error');
        }
    } catch (e) {
        showToast('Error unbinding device', 'error');
    }
}

async function flashBuoy(id) {
    if (!confirm(`Are you sure you want to update the firmware for Buoy ${id} over WiFi? Ensure the buoy is connected to the same WiFi network.`)) return;
    showToast('Flashing firmware over WiFi... Do not turn off buoy!', 'warning');
    
    try {
        const res = await fetchJSON(`/api/devices/${id}/ota-update`, { method: 'POST' });
        if (res.success) {
            showToast(res.message, 'success');
            setTimeout(loadDevicesList, 5000); // Wait for reboot
        } else {
            showToast(res.error || 'Firmware flash failed', 'error');
        }
    } catch (e) {
        showToast('Error flashing device', 'error');
    }
}

// ── Show Add Device Modal ──
function showAddDeviceModal() {
    document.getElementById('add-device-modal').classList.add('active');
}

function closeAddDeviceModal() {
    document.getElementById('add-device-modal').classList.remove('active');
    document.getElementById('new-device-id').value = '';
    document.getElementById('new-device-name').value = '';
}

// ── Add Device ──
async function addDevice() {
    const id = document.getElementById('new-device-id').value.trim().toUpperCase();
    const name = document.getElementById('new-device-name').value.trim();
    const btn = document.querySelector('#add-device-modal .btn-primary');

    if (!id || !name) {
        showToast('Device ID and name are required', 'warning');
        return;
    }

    if (id.length !== 12) {
        showToast('Device ID must be 12 characters (ESP32 chip ID)', 'warning');
        return;
    }

    if (!isConnected) {
        showToast('Transceiver is not connected. Please connect the Transceiver COM port first.', 'warning');
        return;
    }

    btn.textContent = 'Registering...';
    btn.disabled = true;

    try {
        const res = await fetchJSON('/api/devices', {
            method: 'POST',
            body: JSON.stringify({ id, name, lat: 0.0, lon: 0.0 })
        });

        if (res.success) {
            showToast('Device added successfully!', 'success');
            closeAddDeviceModal();
            loadDevicesList();
            
        } else {
            showToast(res.error, 'error');
        }
    } catch (e) {
        showToast('Failed to add device', 'error');
    } finally {
        btn.textContent = 'Add Buoyancy';
        btn.disabled = false;
    }
}

// ── Delete Device ──
async function deleteDevice(deviceId) {
    if (!confirm(`Delete device ${deviceId}?`)) return;

    try {
        const res = await fetchJSON(`/api/devices/${deviceId}`, { method: 'DELETE' });
        if (res.success) {
            showToast('Device deleted', 'success');
            loadDevicesList();
        } else {
            showToast(res.error || 'Delete failed', 'error');
        }
    } catch (e) {
        showToast('Delete error', 'error');
    }
}

// ── Locate Device (go to Live Map) ──
function locateDevice(deviceId) {
    window.location.href = `/map?locate=${deviceId}`;
}

// ── Scan Unbound Buoys ──
async function scanUnboundDevices() {
    const btn = document.getElementById('btn-scan-unbound');
    const resultList = document.getElementById('unbound-devices-list');
    
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner"></span> Scanning...';
    resultList.innerHTML = '<div class="empty-state" style="padding: 20px; text-align: center; color: var(--text-secondary); background: rgba(0,0,0,0.2); border-radius: 8px;">Scanning the network for new buoys...</div>';

    try {
        const res = await fetchJSON('/api/scan_unbound', { method: 'POST' });
        if (res.success) {
            showToast('Unbound scan started. Waiting for responses...', 'info');

            let attempts = 0;
            let displayedBuoysCount = 0;
            
            const pollInterval = setInterval(async () => {
                attempts++;
                const status = await fetchJSON('/api/status');

                // Render buoys as soon as they respond!
                if (status.responded_buoys && status.responded_buoys.length > 0) {
                    if (status.responded_buoys.length > displayedBuoysCount) {
                        displayedBuoysCount = status.responded_buoys.length;
                        
                        resultList.innerHTML = status.responded_buoys.map(id => `
                            <div class="device-card" style="cursor:pointer; background:rgba(0,255,136,0.1); border-color:var(--accent-green); transition: var(--transition);" onclick="prefillAddDevice('${id}')" onmouseover="this.style.background='rgba(0,255,136,0.2)'" onmouseout="this.style.background='rgba(0,255,136,0.1)'">
                                <div class="device-icon" style="color:var(--accent-green)"><i class="ph-bold ph-radar"></i></div>
                                <div class="device-info">
                                    <div class="device-id">${id}</div>
                                    <div class="device-name" style="font-size: 0.8rem; color: var(--text-secondary);">Click to register and name</div>
                                </div>
                                <div class="device-actions">
                                    <i class="ph-bold ph-plus-circle" style="font-size: 24px; color: var(--accent-green);"></i>
                                </div>
                            </div>
                        `).join('');
                    }
                }

                if (status.scan_complete || attempts > 20) {
                    clearInterval(pollInterval);
                    btn.disabled = false;
                    btn.innerHTML = 'Scan Network';
                    
                    if (status.responded_buoys && status.responded_buoys.length > 0) {
                        showToast(`Scan finished. Found ${status.responded_buoys.length} unbound buoys!`, 'success');
                    } else {
                        showToast('No unbound buoys found', 'warning');
                        resultList.innerHTML = '<div class="empty-state" style="padding: 20px; text-align: center; color: var(--text-secondary); background: rgba(0,0,0,0.2); border-radius: 8px;">No new devices found. Ensure they are powered on and unbound.</div>';
                    }
                }
            }, 1000);
        } else {
            showToast(res.message || 'Scan failed', 'error');
            btn.disabled = false;
            btn.innerHTML = 'Scan Network';
            resultList.innerHTML = '<div class="empty-state" style="padding: 20px; text-align: center; color: var(--text-secondary); background: rgba(0,0,0,0.2); border-radius: 8px;">Scan failed.</div>';
        }
    } catch (e) {
        showToast('Scan error: ' + e.message, 'error');
        btn.disabled = false;
        btn.innerHTML = 'Scan Network';
        resultList.innerHTML = '<div class="empty-state" style="padding: 20px; text-align: center; color: var(--text-secondary); background: rgba(0,0,0,0.2); border-radius: 8px;">An error occurred during scan.</div>';
    }
}

function prefillAddDevice(deviceId) {
    document.getElementById('new-device-id').value = deviceId;
    showAddDeviceModal();
    setTimeout(() => {
        document.getElementById('new-device-name').focus();
    }, 100);
}
