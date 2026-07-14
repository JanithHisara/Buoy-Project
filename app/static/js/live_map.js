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
                    <label id="led-btn-${d.id}" class="btn btn-sm" title="Set LED Color" style="position:relative; overflow:hidden; padding: 0; width: 32px; display: flex; align-items: center; justify-content: center; cursor: pointer; background-color: ${d.led_color || '#0000ff'}; color: white; border: 1px solid rgba(255,255,255,0.2); text-shadow: 0 0 3px rgba(0,0,0,0.5);">
                        <i class="ph-bold ph-palette"></i>
                        <input type="color" value="${d.led_color || '#0000ff'}" onchange="event.stopPropagation(); setLEDColor('${d.id}', this.value)" style="position:absolute; opacity:0; width:100%; height:100%; left:0; top:0; cursor:pointer;">
                    </label>
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
            marker.getElement().style.boxShadow = '';
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
                prevMarker.getElement().style.boxShadow = '';
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
            marker.getElement().style.boxShadow = `0 0 20px 8px ${device.led_color || '#0000ff'}80`;
            marker.getElement().style.backgroundColor = device.led_color || '#0000ff';
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

async function setLEDColor(buoyId, hexColor) {
    try {
        const res = await fetchJSON(`/api/devices/${buoyId}/led`, {
            method: 'POST',
            body: JSON.stringify({ color: hexColor })
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


