/**
 * OceanNav — Dashboard Logic
 */

let dashMap = null;
let userMarker = null;
let userLat = null, userLon = null;
let rangeCircleAdded = false;

// Initialize dashboard
document.addEventListener('DOMContentLoaded', async () => {
    await initDashboardMap();
    loadStats();
    loadNearbyBuoys();
    getUserLocation();
});

async function initDashboardMap() {
    dashMap = await createMap('dashboard-map', { 
        zoom: 14,
        interactive: false
    });

    dashMap.on('load', () => {
        // Map is ready
        loadNearbyBuoys();
    });
}

function getUserLocation() {
    if ('geolocation' in navigator) {
        navigator.geolocation.watchPosition(
            (pos) => {
                userLat = pos.coords.latitude;
                userLon = pos.coords.longitude;

                if (dashMap) {
                    // Update or create user marker
                    if (userMarker) {
                        userMarker.setLngLat([userLon, userLat]);
                        dashMap.easeTo({ center: [userLon, userLat] });
                    } else {
                        const el = document.createElement('div');
                        el.className = 'user-marker';
                        userMarker = new maplibregl.Marker({ element: el })
                            .setLngLat([userLon, userLat])
                            .addTo(dashMap);

                        dashMap.flyTo({ center: [userLon, userLat], zoom: dashMap.getZoom() });
                    }

                    // Add 1km LoRa range circle
                    addRangeCircle();
                    loadNearbyBuoys();
                }
            },
            (err) => {
                console.warn('Geolocation error:', err);
                document.getElementById('nearby-buoys').innerHTML =
                    '<div class="empty-state">Location unavailable</div>';
            },
            { enableHighAccuracy: true, timeout: 10000 }
        );
    }
}

function addRangeCircle() {
    if (!dashMap || userLat === null) return;

    const circleData = createCircleGeoJSON([userLon, userLat], 1);

    if (dashMap.getSource('range-circle')) {
        dashMap.getSource('range-circle').setData(circleData);
    } else {
        dashMap.addSource('range-circle', {
            type: 'geojson',
            data: circleData
        });
        dashMap.addLayer({
            id: 'range-circle-fill',
            type: 'fill',
            source: 'range-circle',
            paint: {
                'fill-color': '#00d4ff',
                'fill-opacity': 0.08
            }
        });
        dashMap.addLayer({
            id: 'range-circle-line',
            type: 'line',
            source: 'range-circle',
            paint: {
                'line-color': '#00d4ff',
                'line-width': 2,
                'line-opacity': 0.4,
                'line-dasharray': [4, 4]
            }
        });
    }
}

async function loadNearbyBuoys() {
    try {
        const devices = await fetchJSON('/api/devices?bound_only=true');
        const container = document.getElementById('nearby-buoys');

        if (!devices.length) {
            container.innerHTML = '<div class="empty-state">No buoys registered</div>';
            return;
        }

        // Filter to 2km range if user location available
        let filtered = devices;
        if (userLat !== null) {
            filtered = devices.map(d => ({
                ...d,
                distance: getDistanceKm(userLat, userLon, d.lat, d.lon)
            })).filter(d => d.distance <= 2).sort((a, b) => a.distance - b.distance);
        }

        if (!filtered.length) {
            container.innerHTML = '<div class="empty-state">No buoys within 2km</div>';
            return;
        }

        container.innerHTML = filtered.map(d => `
            <div class="nearby-buoy-item">
                <div class="buoy-dot ${d.status}"></div>
                <span class="buoy-name">${d.name || d.id}</span>
                <span class="buoy-distance">${d.distance ? d.distance.toFixed(1) + ' km' : '--'}</span>
            </div>
        `).join('');

        // Add buoy markers to map
        if (dashMap && dashMap.loaded()) {
            filtered.forEach(d => {
                if (d.lat && d.lon && (d.lat !== 0 || d.lon !== 0)) {
                    const color = d.status === 'online' ? '#00e5a0' :
                                  d.status === 'warning' ? '#ffb830' : '#ff4757';
                    const el = document.createElement('div');
                    el.className = 'buoy-marker';
                    el.style.background = color;
                    el.style.width = '16px';
                    el.style.height = '16px';
                    el.style.borderWidth = '2px';

                    new maplibregl.Marker({ element: el })
                        .setLngLat([d.lon, d.lat])
                        .setPopup(new maplibregl.Popup({ offset: 10 })
                            .setHTML(`<strong>${d.name || d.id}</strong><br>
                                     <small>${d.lat.toFixed(6)}, ${d.lon.toFixed(6)}</small>`))
                        .addTo(dashMap);
                }
            });
        }
    } catch (e) {
        console.error('Failed to load nearby buoys:', e);
    }
}
