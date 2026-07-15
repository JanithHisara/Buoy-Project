/**
 * OceanNav — Live Map Logic
 * Full map with buoy tracking, color coding, scan GPS, update location
 */

let liveMap = null;
let buoyMarkers = {};
let buoyPopups = {};
let userMarker = null;
let highlightedBuoy = null;
let allDevices = [];
let defaultZoomLevel = 10;

document.addEventListener('DOMContentLoaded', async () => {
    await initLiveMap();
    loadStats();
    loadDevices();

    // Search filter
    document.getElementById('buoy-search').addEventListener('input', (e) => {
        filterBuoyList(e.target.value.trim().toLowerCase());
    });
});

async function initLiveMap() {
    try {
        const settings = await fetchJSON('/api/settings');
        if (settings.default_zoom) {
            defaultZoomLevel = parseInt(settings.default_zoom) || 10;
        }
    } catch (e) {
        console.error(e);
    }
    
    liveMap = await createMap('live-map', { zoom: defaultZoomLevel });

    liveMap.on('load', () => {
        // Get user location
        if ('geolocation' in navigator) {
            navigator.geolocation.watchPosition((pos) => {
                const lat = pos.coords.latitude;
                const lon = pos.coords.longitude;

                if (userMarker) {
                    userMarker.setLngLat([lon, lat]);
                } else {
                    const el = document.createElement('div');
                    el.className = 'user-marker';
                    userMarker = new maplibregl.Marker({ element: el })
                        .setLngLat([lon, lat])
                        .addTo(liveMap);
                    
                    // Center the map on the user's location on first load
                    liveMap.flyTo({ center: [lon, lat], zoom: defaultZoomLevel });
                }
            }, null, { enableHighAccuracy: true });
        }

        // Add navigation controls
        liveMap.addControl(new maplibregl.NavigationControl(), 'top-right');
        liveMap.addControl(new maplibregl.GeolocateControl({
            positionOptions: { enableHighAccuracy: true },
            trackUserLocation: true
        }), 'top-right');
    });
}

async function loadDevices() {
    try {
        allDevices = await fetchJSON('/api/devices?bound_only=true');
        renderBuoyList(allDevices);
        renderBuoyMarkers(allDevices);
        if (typeof loadStats === 'function') {
            loadStats();
        }
        
        // Handle ?locate=ID parameter
        const urlParams = new URLSearchParams(window.location.search);
        const locateId = urlParams.get('locate');
        if (locateId) {
            const tryHighlight = () => {
                if (liveMap && buoyMarkers[locateId]) {
                    if (highlightedBuoy !== locateId) {
                        toggleHighlight(locateId);
                    }
                } else {
                    setTimeout(tryHighlight, 100);
                }
            };
            tryHighlight();
            // Remove parameter from URL so it doesn't trigger again on reload
            window.history.replaceState({}, document.title, window.location.pathname);
        }

    } catch (e) {
        console.error('Failed to load devices:', e);
    }
}

function renderBuoyList(devices) {
    const container = document.getElementById('buoy-list');

    if (!devices.length) {
        container.innerHTML = '<div class="empty-state">No buoy devices found</div>';
        return;
    }

    container.innerHTML = devices.map(d => {
        const color = d.status === 'online' ? 'green' :
                      d.status === 'warning' ? 'yellow' : 'red';
        const isHighlighted = highlightedBuoy === d.id;

        return `
            <div class="buoy-card ${isHighlighted ? 'highlighted' : ''}"
                 id="buoy-card-${d.id}" onclick="toggleHighlight('${d.id}')">
                <div class="buoy-indicator ${color}"></div>
                <div class="buoy-info">
                    <div class="buoy-id">${d.name || d.id}</div>
                    <div class="buoy-name">ID: ${d.id}</div>
                    <div class="buoy-coords">${d.lat.toFixed(6)}, ${d.lon.toFixed(6)}</div>
                </div>
                <div class="buoy-actions">
                    <button id="led-btn-${d.id}" class="btn btn-sm" onclick="event.stopPropagation(); toggleLEDMenu(event, '${d.id}', this)" title="LED Controls" style="width: 32px; padding: 0; display: flex; align-items: center; justify-content: center; background-color: ${d.led_color || '#0000ff'}; color: white; border: 1px solid rgba(255,255,255,0.2); text-shadow: 0 0 3px rgba(0,0,0,0.5);">
                        <i class="ph-bold ph-palette"></i>
                    </button>
                    <button class="btn btn-outline btn-sm" onclick="event.stopPropagation(); updateBuoyLocation('${d.id}')" title="Update location">
                        <i class="ph-bold ph-arrows-clockwise"></i>
                    </button>
                </div>
            </div>
        `;
    }).join('');
}

function renderBuoyMarkers(devices) {
    // Clear old markers
    Object.values(buoyMarkers).forEach(m => m.remove());
    buoyMarkers = {};

    devices.forEach(d => {
        if (d.lat === 0 && d.lon === 0) return;

        const color = d.status === 'online' ? 'green' :
                      d.status === 'warning' ? 'yellow' : 'red';

        const el = document.createElement('div');
        el.className = `buoy-marker ${color}`;
        el.id = `marker-${d.id}`;

        const popup = new maplibregl.Popup({ offset: 15, closeButton: false })
            .setHTML(`
                <strong>${d.name || d.id}</strong><br>
                <small>ID: ${d.id}</small><br>
                <small><i class="ph-bold ph-map-pin"></i> ${d.lat.toFixed(6)}, ${d.lon.toFixed(6)}</small><br>
                <small>Status: <span style="color:${color === 'green' ? '#00e5a0' : color === 'yellow' ? '#ffb830' : '#ff4757'}">${d.status}</span></small>
                ${d.last_gps_time ? `<br><small>Last GPS: ${d.last_gps_time} <span style="color:var(--text-secondary)">(${d.is_cached ? 'Last Save' : 'Live'})</span></small>` : ''}
                <button class="btn btn-primary" style="width: 100%; margin-top: 8px; font-size: 0.85rem;" onclick="toggleHistoryTrail('${d.id}')" id="btn-trail-${d.id}">Show Trail</button>
            `);

        const marker = new maplibregl.Marker({ element: el })
            .setLngLat([d.lon, d.lat])
            .addTo(liveMap);

        el.addEventListener('click', (e) => {
            e.stopPropagation();
            toggleHighlight(d.id);
        });

        buoyMarkers[d.id] = marker;
        buoyPopups[d.id] = popup;
    });
}

function toggleHighlight(buoyId) {
    const device = allDevices.find(d => d.id === buoyId);
    if (!device) return;

    if (highlightedBuoy === buoyId) {
        // De-highlight
        highlightedBuoy = null;
        const card = document.getElementById(`buoy-card-${buoyId}`);
        if (card) {
            card.classList.remove('highlighted');
            card.style.borderColor = '';
            card.style.boxShadow = '';
        }
        const marker = buoyMarkers[buoyId];
        if (marker) {
            marker.getElement().classList.remove('pulse');
            marker.getElement().style.removeProperty('--pulse-color');
            marker.getElement().style.removeProperty('--pulse-color-transparent');
            marker.getElement().style.backgroundColor = '';
            const popup = buoyPopups[buoyId];
            if (popup && popup.isOpen()) popup.remove();
        }
    } else {
        // Remove previous highlight
        if (highlightedBuoy) {
            const prevCard = document.getElementById(`buoy-card-${highlightedBuoy}`);
            if (prevCard) {
                prevCard.classList.remove('highlighted');
                prevCard.style.borderColor = '';
                prevCard.style.boxShadow = '';
            }
            const prevMarker = buoyMarkers[highlightedBuoy];
            if (prevMarker) {
                prevMarker.getElement().classList.remove('pulse');
                prevMarker.getElement().style.removeProperty('--pulse-color');
                prevMarker.getElement().style.removeProperty('--pulse-color-transparent');
                prevMarker.getElement().style.backgroundColor = '';
                const prevPopup = buoyPopups[highlightedBuoy];
                if (prevPopup && prevPopup.isOpen()) prevPopup.remove();
            }
        }

        // Highlight new
        highlightedBuoy = buoyId;
        const card = document.getElementById(`buoy-card-${buoyId}`);
        if (card) {
            card.classList.add('highlighted');
            card.style.borderColor = device.led_color || '#0000ff';
            card.style.boxShadow = `0 0 15px ${device.led_color || '#0000ff'}40`;
        }

        const marker = buoyMarkers[buoyId];
        if (marker) {
            marker.getElement().classList.add('pulse');
            
            // Set CSS variables for the pulse animation to use
            const color = device.led_color || '#0000ff';
            marker.getElement().style.setProperty('--pulse-color', `${color}99`);
            marker.getElement().style.setProperty('--pulse-color-transparent', `${color}00`);
            
            marker.getElement().style.backgroundColor = color;
            const popup = buoyPopups[buoyId];
            if (popup && !popup.isOpen()) {
                popup.setLngLat([device.lon, device.lat]).addTo(liveMap);
            }
            liveMap.flyTo({ center: [device.lon, device.lat], zoom: 15 });
        }
    }
}

function filterBuoyList(query) {
    const filtered = allDevices.filter(d => {
        const name = (d.name || '').toLowerCase();
        const id = d.id.toLowerCase();
        return name.includes(query) || id.includes(query);
    });
    renderBuoyList(filtered);
}


// ── Scan Bound (Status) ──
async function scanBound() {
    const btn = document.getElementById('scan-bound-btn');
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner"></span> Pinging...';

    try {
        const res = await fetchJSON('/api/scan_bound', { method: 'POST' });
        if (res.success) {
            showToast('Scanning...', 'info');

            let attempts = 0;
            let glowedBuoys = new Set();
            
            const pollInterval = setInterval(async () => {
                attempts++;
                const status = await fetchJSON('/api/status');

                // Apply glow instantly as they respond
                if (status.responded_buoys && status.responded_buoys.length > 0) {
                    status.responded_buoys.forEach(buoyId => {
                        if (!glowedBuoys.has(buoyId)) {
                            glowedBuoys.add(buoyId);
                            const marker = buoyMarkers[buoyId];
                            const device = allDevices.find(d => d.id === buoyId);
                            if (marker && device) {
                                const el = marker.getElement();
                                const color = device.led_color || '#00e5a0';
                                
                                const origShadow = el.style.boxShadow;
                                const origBg = el.style.backgroundColor;
                                
                                el.style.transition = 'all 0.5s ease';
                                el.style.boxShadow = `0 0 25px 10px ${color}`;
                                el.style.backgroundColor = color;
                                
                                setTimeout(() => {
                                    el.style.boxShadow = origShadow;
                                    el.style.backgroundColor = origBg;
                                    setTimeout(() => { el.style.transition = ''; }, 500);
                                }, 5000);
                            }
                        }
                    });
                }

                if (status.scan_complete || attempts > 20) {
                    clearInterval(pollInterval);
                    btn.disabled = false;
                    btn.innerHTML = '<span><i class="ph-bold ph-broadcast"></i></span> Scan';
                    showToast('Scan complete!', 'success');
                    
                    loadDevices();
                    loadStats();
                }
            }, 1000);
        } else {
            showToast(res.message || 'Scan failed', 'error');
            btn.disabled = false;
            btn.innerHTML = '<span><i class="ph-bold ph-broadcast"></i></span> Scan';
        }
    } catch (e) {
        showToast('Scan error: ' + e.message, 'error');
        btn.disabled = false;
        btn.innerHTML = '<span><i class="ph-bold ph-broadcast"></i></span> Scan';
    }
}

// ── Update single buoy location ──
async function updateBuoyLocation(buoyId) {
    showToast(`Fetching last saved location for ${buoyId}...`, 'info');

    try {
        const res = await fetchJSON(`/api/devices/${buoyId}/update-location`, { method: 'POST' });

        if (res.success) {
            if (res.lat === 0.0 && res.lon === 0.0) {
                showToast(`<i class="ph-bold ph-info"></i> No previous location saved. Waiting for LIVE lock...`, 'warning');
            } else {
                const label = res.is_cached ? '(last save)' : '(live)';
                const toastType = res.is_cached ? 'warning' : 'success';
                showToast(`<i class="ph-bold ph-check-circle"></i> Location updated ${label}: ${res.lat.toFixed(6)}, ${res.lon.toFixed(6)}`, toastType);
            }
            loadDevices();

        } else {
            // Show fallback location warning
            if (res.fallback && res.fallback.lat) {
                showToast(`<i class="ph-bold ph-warning"></i> ${res.error} Showing last known: ${res.fallback.lat.toFixed(4)}, ${res.fallback.lon.toFixed(4)}`, 'warning');
            } else {
                showToast(`<i class="ph-bold ph-warning"></i> ${res.error}`, 'warning');
            }
        }
    } catch (e) {
        showToast('Update error: ' + e.message, 'error');
    }
}

// ── GPS History Trail ──
async function toggleHistoryTrail(buoyId) {
    const btn = document.getElementById(`btn-trail-${buoyId}`);
    const sourceId = `trail-source-${buoyId}`;
    const layerId = `trail-layer-${buoyId}`;

    if (liveMap.getLayer(layerId)) {
        // Trail exists, remove it
        liveMap.removeLayer(layerId);
        liveMap.removeSource(sourceId);
        if (btn) btn.innerText = 'Show Trail';
        return;
    }

    if (btn) btn.innerText = 'Loading...';
    showToast(`Fetching history trail for ${buoyId}...`, 'info');

    try {
        const res = await fetchJSON(`/api/devices/${buoyId}/history`, { method: 'POST' });
        
        if (res.success && res.history && res.history.length > 0) {
            // Draw the trail
            let coordinates = res.history.map(point => [point.lon, point.lat]).reverse();
            
            // Connect to current live location
            const device = allDevices.find(d => d.id === buoyId);
            if (device && Math.abs(device.lat) > 0.01 && Math.abs(device.lon) > 0.01) {
                coordinates.push([device.lon, device.lat]);
            }
            
            liveMap.addSource(sourceId, {
                'type': 'geojson',
                'data': {
                    'type': 'Feature',
                    'properties': {},
                    'geometry': {
                        'type': 'LineString',
                        'coordinates': coordinates
                    }
                }
            });

            liveMap.addLayer({
                'id': layerId,
                'type': 'line',
                'source': sourceId,
                'layout': {
                    'line-join': 'round',
                    'line-cap': 'round'
                },
                'paint': {
                    'line-color': '#00e5a0',
                    'line-width': 4,
                    'line-dasharray': [2, 2]
                }
            });

            if (btn) btn.innerText = 'Hide Trail';
            showToast(`Trail loaded with ${res.history.length} points.`, 'success');
        } else if (res.success && res.history && res.history.length === 0) {
            showToast('No GPS history found saved on the Buoyancy.', 'warning');
            if (btn) btn.innerText = 'Show Trail';
        } else {
            showToast(res.error || 'Failed to fetch history.', 'error');
            if (btn) btn.innerText = 'Show Trail';
        }
    } catch (err) {
        console.error(err);
        showToast('Error fetching history', 'error');
        if (btn) btn.innerText = 'Show Trail';
    }
}

let activeLEDMenuBuoy = null;

function createGlobalLEDMenu() {
    if (document.getElementById('global-led-menu')) return;
    
    const menuHTML = `
        <div id="global-led-menu" style="display:none; position:fixed; background: #1f2937; border: 1px solid #374151; padding: 12px; border-radius: 8px; z-index: 99999; width: 220px; box-shadow: 0 4px 20px rgba(0,0,0,0.6);" onclick="event.stopPropagation();">
            <div style="margin-bottom: 12px; font-weight: bold; font-size: 12px; color: #d1d5db; display: flex; justify-content: space-between; align-items: center;">
                <span>LED Controls</span>
                <label style="display: flex; align-items: center; cursor: pointer; gap: 6px;">
                    <span style="font-size: 10px; font-weight: normal; color: #9ca3af;">Power</span>
                    <div style="position: relative; width: 32px; height: 18px;">
                        <input type="checkbox" id="global-led-power" style="opacity: 0; width: 0; height: 0; position: absolute;" checked>
                        <span style="position: absolute; cursor: pointer; top: 0; left: 0; right: 0; bottom: 0; background-color: #4b5563; transition: .4s; border-radius: 18px;" class="slider round"></span>
                        <style>
                            #global-led-power:checked + .slider { background-color: #3b82f6; }
                            .slider:before { position: absolute; content: ""; height: 14px; width: 14px; left: 2px; bottom: 2px; background-color: white; transition: .4s; border-radius: 50%; }
                            #global-led-power:checked + .slider:before { transform: translateX(14px); }
                        </style>
                    </div>
                </label>
            </div>
            <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 12px;">
                <label style="font-size: 11px; color: #9ca3af; width: 60px;">Color:</label>
                <input type="color" id="global-led-color" value="#0000ff" style="width: 100%; height: 28px; cursor: pointer; border: none; padding: 0; background: transparent;">
            </div>
            <div style="display: flex; flex-direction: column; gap: 4px; margin-bottom: 12px;">
                <div style="display: flex; justify-content: space-between;">
                    <label style="font-size: 11px; color: #9ca3af;">Blink Off Time:</label>
                    <span id="global-led-time-val" style="font-size: 11px; color: #fff;">0s</span>
                </div>
                <input type="range" id="global-led-time" min="0" max="5" value="0" step="1" oninput="document.getElementById('global-led-time-val').innerText = this.value + 's';" style="width: 100%;">
            </div>
            <button class="btn btn-primary btn-sm" style="width: 100%;" onclick="applyLEDMenu()">Apply</button>
        </div>
    `;
    document.body.insertAdjacentHTML('beforeend', menuHTML);
}

function toggleLEDMenu(event, buoyId, btnElement) {
    createGlobalLEDMenu();
    const menu = document.getElementById('global-led-menu');
    
    // If clicking the same button and menu is open, close it
    if (activeLEDMenuBuoy === buoyId && menu.style.display === 'block') {
        menu.style.display = 'none';
        return;
    }
    
    activeLEDMenuBuoy = buoyId;
    const device = allDevices.find(d => d.id === buoyId);
    if (device) {
        document.getElementById('global-led-color').value = device.led_color || '#0000ff';
        document.getElementById('global-led-power').checked = (device.led_is_on !== 0 && device.led_is_on !== false);
    }
    
    const rect = btnElement.getBoundingClientRect();
    
    // Position menu below the button
    menu.style.top = (rect.bottom + 8) + 'px';
    
    // Align center horizontally relative to button
    menu.style.left = (rect.left + (rect.width / 2)) + 'px';
    menu.style.transform = 'translateX(-50%)';
    
    menu.style.display = 'block';
    
    // Check if it goes off bottom of screen
    setTimeout(() => {
        const menuRect = menu.getBoundingClientRect();
        if (menuRect.bottom > window.innerHeight) {
            menu.style.top = (rect.top - menuRect.height - 8) + 'px'; // flip above if too low
        }
    }, 0);
}

function applyLEDMenu() {
    if (!activeLEDMenuBuoy) return;
    const colorInput = document.getElementById('global-led-color');
    const timeInput = document.getElementById('global-led-time');
    const powerInput = document.getElementById('global-led-power');
    
    if (colorInput && timeInput && powerInput) {
        setLEDColor(activeLEDMenuBuoy, colorInput.value, timeInput.value, powerInput.checked);
    }
    
    document.getElementById('global-led-menu').style.display = 'none';
}

// Close dropdowns if clicked outside
document.addEventListener('click', () => {
    const menu = document.getElementById('global-led-menu');
    if (menu) menu.style.display = 'none';
});

async function setLEDColor(buoyId, hexColor, offTime, isOn = true) {
    try {
        const payload = { color: hexColor, is_on: isOn };
        if (offTime !== undefined && offTime !== null) {
            payload.off_time = parseInt(offTime) * 1000;
        }

        const res = await fetchJSON(`/api/devices/${buoyId}/led`, {
            method: 'POST',
            body: JSON.stringify(payload)
        });
        
        if (res.success) {
            showToast(`LED color set for ${buoyId}`, 'success');
            // Update in-memory state
            const device = allDevices.find(d => d.id === buoyId);
            if (device) {
                device.led_color = res.color || hexColor;
                
                // Instantly update the full button background colors
                const btn1 = document.getElementById(`led-btn-${buoyId}`);
                if (btn1) btn1.style.backgroundColor = device.led_color;

                // If it's currently highlighted, refresh the highlight UI
                if (highlightedBuoy === buoyId) {
                    toggleHighlight(buoyId); // turn off
                    toggleHighlight(buoyId); // turn on with new color
                }
            }
        } else {
            showToast(res.message || 'Failed to set LED color', 'error');
        }
    } catch (e) {
        showToast('Error setting LED color', 'error');
    }
}


