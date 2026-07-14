/**
 * OceanNav — Login / Signup Logic
 */

function switchTab(tab) {
    document.querySelectorAll('.auth-tab').forEach(t => t.classList.remove('active'));
    document.querySelector(`[data-tab="${tab}"]`).classList.add('active');

    document.getElementById('login-form').style.display = tab === 'login' ? 'block' : 'none';
    document.getElementById('signup-form').style.display = tab === 'signup' ? 'block' : 'none';

    document.getElementById('login-error').textContent = '';
    document.getElementById('signup-error').textContent = '';
}

async function handleLogin(e) {
    e.preventDefault();
    const email = document.getElementById('login-email').value.trim();
    const password = document.getElementById('login-password').value;
    const errorEl = document.getElementById('login-error');
    const btn = document.getElementById('login-btn');

    btn.textContent = 'Signing in...';
    btn.disabled = true;

    try {
        const res = await fetch('/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password })
        });
        const data = await res.json();

        if (data.success) {
            window.location.href = '/dashboard';
        } else {
            errorEl.textContent = data.error;
        }
    } catch (err) {
        errorEl.textContent = 'Network error. Please try again.';
    }

    btn.textContent = 'Sign In';
    btn.disabled = false;
}

async function handleSignup(e) {
    e.preventDefault();
    const name = document.getElementById('signup-name').value.trim();
    const email = document.getElementById('signup-email').value.trim();
    const password = document.getElementById('signup-password').value;
    const errorEl = document.getElementById('signup-error');
    const btn = document.getElementById('signup-btn');

    btn.textContent = 'Creating account...';
    btn.disabled = true;

    try {
        const res = await fetch('/signup', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name, email, password })
        });
        const data = await res.json();

        if (data.success) {
            window.location.href = '/dashboard';
        } else {
            errorEl.textContent = data.error;
        }
    } catch (err) {
        errorEl.textContent = 'Network error. Please try again.';
    }

    btn.textContent = 'Create Account';
    btn.disabled = false;
}
