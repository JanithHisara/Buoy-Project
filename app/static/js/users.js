/**
 * OceanNav — Users Management Logic
 */

document.addEventListener('DOMContentLoaded', () => {
    loadUsers();
});

async function loadUsers() {
    try {
        const users = await fetchJSON('/api/users');
        const tbody = document.getElementById('users-tbody');

        tbody.innerHTML = users.map(u => {
            const statusClass = u.status === 'Active' ? 'status-active' : 'status-offline';
            const isSuperAdmin = CURRENT_USER_ROLE === 'super_admin';

            let roleCell = `<span class="role-badge ${u.role}">${u.role.replace('_', ' ')}</span>`;
            if (isSuperAdmin && u.role !== 'super_admin') {
                roleCell = `
                    <select class="role-select" onchange="changeRole(${u.id}, this.value)">
                        <option value="user" ${u.role === 'user' ? 'selected' : ''}>User</option>
                        <option value="admin" ${u.role === 'admin' ? 'selected' : ''}>Admin</option>
                    </select>
                `;
            }

            let actionsCell = '';
            if (isSuperAdmin && u.role !== 'super_admin') {
                actionsCell = `
                    <td>
                        <div class="user-actions">
                            <button class="btn btn-danger btn-sm" onclick="deleteUser(${u.id}, '${u.name}')">Delete</button>
                        </div>
                    </td>
                `;
            } else if (isSuperAdmin) {
                actionsCell = '<td><span style="color:var(--text-muted);font-size:11px">Protected</span></td>';
            }

            return `
                <tr>
                    <td>
                        <div class="user-cell">
                            <div class="user-avatar" style="background:${u.avatar_bg}">${u.avatar}</div>
                            <span class="user-name">${u.name}</span>
                        </div>
                    </td>
                    <td style="color:var(--text-secondary)">${u.email}</td>
                    <td>${roleCell}</td>
                    <td><span class="${statusClass}">${u.status}</span></td>
                    <td style="color:var(--text-muted);font-size:12px">${u.last_active}</td>
                    ${isSuperAdmin ? actionsCell : ''}
                </tr>
            `;
        }).join('');
    } catch (e) {
        console.error('Failed to load users:', e);
    }
}

async function changeRole(userId, newRole) {
    try {
        const res = await fetchJSON(`/api/users/${userId}/role`, {
            method: 'PUT',
            body: JSON.stringify({ role: newRole })
        });
        if (res.success) {
            showToast('Role updated', 'success');
        } else {
            showToast(res.error, 'error');
            loadUsers();
        }
    } catch (e) {
        showToast('Failed to update role', 'error');
        loadUsers();
    }
}

async function deleteUser(userId, userName) {
    if (!confirm(`Delete user "${userName}"? This cannot be undone.`)) return;

    try {
        const res = await fetchJSON(`/api/users/${userId}`, { method: 'DELETE' });
        if (res.success) {
            showToast('User deleted', 'success');
            loadUsers();
        } else {
            showToast(res.error, 'error');
        }
    } catch (e) {
        showToast('Failed to delete user', 'error');
    }
}

// ── Add User Modal ──
function showAddUserModal() {
    document.getElementById('add-user-modal').classList.add('active');
}

function closeAddUserModal() {
    document.getElementById('add-user-modal').classList.remove('active');
}

async function addUser() {
    const name = document.getElementById('new-user-name').value.trim();
    const email = document.getElementById('new-user-email').value.trim();
    const password = document.getElementById('new-user-password').value;
    const role = document.getElementById('new-user-role').value;

    if (!name || !email || !password) {
        showToast('All fields are required', 'warning');
        return;
    }

    try {
        const res = await fetchJSON('/api/users', {
            method: 'POST',
            body: JSON.stringify({ name, email, password, role })
        });
        if (res.success) {
            showToast(res.message, 'success');
            closeAddUserModal();
            loadUsers();
        } else {
            showToast(res.error, 'error');
        }
    } catch (e) {
        showToast('Failed to add user', 'error');
    }
}
