// Theme management
let currentTheme = 'dark';

function toggleTheme() {
    currentTheme = currentTheme === 'dark' ? 'light' : 'dark';
    document.documentElement.setAttribute('data-theme', currentTheme === 'light' ? 'light' : '');
    const themeLabel = document.getElementById('theme-label');
    if (themeLabel) themeLabel.textContent = currentTheme === 'dark' ? 'Dark' : 'Light';
    if (window.map) setTimeout(() => map.invalidateSize(), 50);
    
    // Dispatch a custom event for other components to react to theme change
    const event = new CustomEvent('themechanged', { detail: { theme: currentTheme } });
    document.dispatchEvent(event);
}

// Sidebar toggle
function toggleSidebar() {
    const sidebar = document.getElementById('sidebar');
    if (sidebar) sidebar.classList.toggle('collapsed');
}

// Navigation
function navigateTo(path) {
    window.location.href = path;
}

// Notification system
let notifTimer;

function showNotif(message) {
    const notif = document.getElementById('notif');
    const msgSpan = document.getElementById('notif-msg');
    if (!notif || !msgSpan) return;
    
    msgSpan.textContent = message;
    notif.classList.add('show');
    clearTimeout(notifTimer);
    notifTimer = setTimeout(() => notif.classList.remove('show'), 3500);
}

// Logout function
async function logout() {
    try {
        await fetch('/logout', { method: 'POST' });
        window.location.href = '/';
    } catch (error) {
        window.location.href = '/';
    }
}

// Load ports for device connection
async function loadPorts() {
    try {
        const response = await fetch('/ports');
        const ports = await response.json();
        const select = document.getElementById('ports');
        if (select) {
            const currentValue = select.value;
            select.innerHTML = '';
            ports.forEach(port => {
                const option = document.createElement('option');
                option.value = port;
                option.text = port;
                if (port === currentValue) option.selected = true;
                select.appendChild(option);
            });
        }
    } catch (error) {
        console.error('Failed to load ports:', error);
    }
}

// Connect to device
async function connectToDevice() {
    const portSelect = document.getElementById('ports');
    if (!portSelect) return;
    
    const port = portSelect.value;
    try {
        const response = await fetch('/connect', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ port: port })
        });
        const data = await response.json();
        showNotif(data.message || `Connected to ${port}`);
    } catch (error) {
        showNotif(`Connect command sent to ${port}`);
    }
}

// Scan GPS
async function scanGPS() {
    try {
        await fetch('/scan');
        showNotif('GPS scan started — awaiting data');
    } catch (error) {
        showNotif('Scan sent (no server response)');
    }
}

// Initialize theme on page load
document.addEventListener('DOMContentLoaded', () => {
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme === 'light') {
        currentTheme = 'light';
        document.documentElement.setAttribute('data-theme', 'light');
        const themeLabel = document.getElementById('theme-label');
        if (themeLabel) themeLabel.textContent = 'Light';
    }
});

// Save theme preference
function saveThemePreference() {
    localStorage.setItem('theme', currentTheme);
}