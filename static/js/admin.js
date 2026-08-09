/**
 * ADMIN DASHBOARD CONTROLLER
 */

let currentAdminUser = null;
let allUsers = [];
document.addEventListener("DOMContentLoaded", () => {
  initAdminDashboard();
});

async function initAdminDashboard() {
  await verifyAdminAuth();
  await loadProjects();
  await loadUsers();
}

// 🔐 Auto Auth Check & Role Guard
async function verifyAdminAuth() {
  try {
    const res = await fetch("/auth/me", {
      credentials: "include"
    });

    if (!res.ok) {
      window.location.href = "/auth/google/login";
      return;
    }

    const user = await res.json();
    if (user.role !== "admin") {
      // Redirect investor role attempting to access admin
      window.location.href = "/investor";
      return;
    }

    currentAdminUser = user;
    const adminNameEl = document.getElementById("admin-user-name");
    if (adminNameEl) {
      adminNameEl.textContent = user.name || user.email;
    }
  } catch (err) {
    console.error("Auth check failed:", err);
    window.location.href = "/auth/google/login";
  }
}

// 1. Create Project
async function handleCreateProject(event) {
  event.preventDefault();

  const nameInput = document.getElementById("project-name");
  const name = nameInput.value.trim();

  if (!name) {
    showAlert("Please enter a project name.", "warning");
    return;
  }

  const submitBtn = document.getElementById("btn-create-project");
  submitBtn.disabled = true;
  submitBtn.innerHTML = `<span class="spinner-border spinner-border-sm me-2"></span>Creating...`;

  try {
    const res = await fetch("/projects", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      credentials: "include",
      body: JSON.stringify({
        name: name,
        start_date: new Date().toISOString(),
        end_date: new Date(Date.now() + 365 * 24 * 60 * 60 * 1000).toISOString()
      })
    });

    if (!res.ok) {
      const errData = await res.json();
      throw new Error(errData.detail || "Failed to create project");
    }

    const newProject = await res.json();
    showAlert(`Project "${newProject.name}" created successfully!`, "success");
    nameInput.value = "";
    await loadProjects();
  } catch (err) {
    showAlert(`Error: ${err.message}`, "danger");
  } finally {
    submitBtn.disabled = false;
    submitBtn.innerHTML = `<i class="bi bi-plus-circle me-1"></i> Create Project`;
  }
}

// Load & Display Projects Table
async function loadProjects() {
  const container = document.getElementById("projects-list");
  if (!container) return;

  container.innerHTML = `<tr><td colspan="4" class="text-center text-muted py-4"><span class="spinner-border spinner-border-sm me-2"></span>Loading projects...</td></tr>`;

  try {
    const res = await fetch("/projects", {
      credentials: "include"
    });

    if (!res.ok) throw new Error("Failed to fetch projects");

    const projects = await res.json();

    if (!projects || projects.length === 0) {
      container.innerHTML = `<tr><td colspan="4" class="text-center text-muted py-4">No investment projects found.</td></tr>`;
      return;
    }

    container.innerHTML = projects.map(p => `
      <tr>
        <td class="fw-semibold">${escapeHtml(p.name)}</td>
        <td><code class="text-secondarySmall">${p.uuid}</code></td>
        <td><strong>$${p.initial_amount || "0.00"}</strong></td>
        <td>
          <span class="badge badge-status ${p.status === 'ACTIVE' ? 'badge-active' : 'badge-closed'}">
            ${p.status || 'ACTIVE'}
          </span>
        </td>
      </tr>
    `).join('');

  } catch (err) {
    console.error("Load projects error:", err);
    container.innerHTML = `<tr><td colspan="4" class="text-center text-danger py-4">Failed to load projects.</td></tr>`;
  }
}

// 2. List Users
async function loadUsers() {
  const container = document.getElementById("users-list");
  const userSelect = document.getElementById("movement-user-id");

  if (!container) return;

  container.innerHTML = `<tr><td colspan="4" class="text-center text-muted py-4"><span class="spinner-border spinner-border-sm me-2"></span>Loading users...</td></tr>`;

  try {
    const res = await fetch("/admin/users/users", {
      credentials: "include"
    });

    if (!res.ok) throw new Error("Failed to fetch users");

    allUsers = await res.json();

    if (!allUsers || allUsers.length === 0) {
      container.innerHTML = `<tr><td colspan="4" class="text-center text-muted py-4">No users found in system.</td></tr>`;
      return;
    }

    container.innerHTML = allUsers.map(u => `
      <tr>
        <td class="fw-bold">${escapeHtml(u.name)}</td>
        <td><code class="text-muted">${u.uuid}</code></td>
        <td><span class="badge bg-light text-dark border">${u.role}</span></td>
        <td>
          <button class="btn btn-sm btn-outline-primary" onclick="inspectUserWallets('${u.uuid}', '${escapeHtml(u.name)}')">
            <i class="bi bi-wallet2 me-1"></i> View Wallets
          </button>
        </td>
      </tr>
    `).join('');

    // Populate Deposit/Withdraw user dropdown
    if (userSelect) {
      userSelect.innerHTML = `<option value="">Select User...</option>` +
        allUsers.map(u => `<option value="${u.uuid}">${escapeHtml(u.name)} (${u.role})</option>`).join('');
    }

  } catch (err) {
    console.error("Load users error:", err);
    container.innerHTML = `<tr><td colspan="4" class="text-center text-danger py-4">Failed to load users.</td></tr>`;
  }
}

// 3. User Wallets Inspection
async function inspectUserWallets(userId, userName) {
  const container = document.getElementById("user-wallets-list");
  const titleEl = document.getElementById("selected-user-name");
  
  if (titleEl) titleEl.textContent = userName ? `Wallets for: ${userName}` : `User Wallets`;
  if (container) container.innerHTML = `<tr><td colspan="3" class="text-center text-muted py-4"><span class="spinner-border spinner-border-sm me-2"></span>Fetching wallet details...</td></tr>`;

  // Pre-select user in deposit/withdraw form
  const userSelect = document.getElementById("movement-user-id");
  if (userSelect) {
    userSelect.value = userId;
    await handleUserSelectedForMovement(userId);
  }

  try {
    const res = await fetch(`/wallet/admin/${userId}`, {
      credentials: "include"
    });

    if (!res.ok) throw new Error("Failed to load wallets");

    const wallets = await res.json();

    if (!wallets || wallets.length === 0) {
      container.innerHTML = `<tr><td colspan="3" class="text-center text-muted py-4">No wallets found for this user.</td></tr>`;
      return;
    }

    container.innerHTML = wallets.map(w => `
      <tr>
        <td class="fw-semibold">${escapeHtml(w.wallet_name || w.name || 'Default Wallet')}</td>
        <td class="text-success fw-bold">$${w.balance}</td>
        <td><code class="text-muted">${w.Wallet_id || w.uuid}</code></td>
      </tr>
    `).join('');

  } catch (err) {
    console.error("Inspect wallets error:", err);
    container.innerHTML = `<tr><td colspan="3" class="text-center text-danger py-4">Failed to load user wallets.</td></tr>`;
  }
}

// Helper when user is picked in movement form
async function handleUserSelectedForMovement(userId) {
  const walletSelect = document.getElementById("movement-wallet-id");
  if (!walletSelect || !userId) return;

  walletSelect.innerHTML = `<option value="">Loading wallets...</option>`;

  try {
    const res = await fetch(`/wallet/admin/${userId}`, {
      credentials: "include"
    });

    if (!res.ok) throw new Error("Could not load user wallets");
    const wallets = await res.json();

    if (wallets.length === 0) {
      walletSelect.innerHTML = `<option value="">No wallets found for user</option>`;
      return;
    }

    walletSelect.innerHTML = `<option value="">Select Wallet...</option>` +
      wallets.map(w => `<option value="${w.Wallet_id || w.uuid}">${escapeHtml(w.wallet_name || w.name || 'Wallet')} (Balance: $${w.balance})</option>`).join('');

  } catch (err) {
    walletSelect.innerHTML = `<option value="">Error loading wallets</option>`;
  }
}

// 4. Handle Deposit / Withdraw Money Movements
async function handleMoneyMovement(type) {
  const userId = document.getElementById("movement-user-id").value;
  const amount = document.getElementById("movement-amount").value;
  const description = document.getElementById("movement-description").value;

  if (!userId || !amount || parseFloat(amount) <= 0) {
    showAlert("Please select a valid user and enter a positive amount.", "warning");
    return;
  }

  const endpoint = type === 'deposit' ? '/admin/money-movements/deposit' : '/admin/money-movements/withdraw';
  const actionText = type === 'deposit' ? 'Depositing' : 'Withdrawing';

  const btn = document.getElementById(`btn-${type}`);
  if (btn) {
    btn.disabled = true;
    btn.innerHTML = `<span class="spinner-border spinner-border-sm me-1"></span>${actionText}...`;
  }

  try {
    const res = await fetch(endpoint, {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      credentials: "include",
      body: JSON.stringify({
        user_id: userId,
        amount: amount,
        description: description || `Admin ${type.toUpperCase()}`
      })
    });

    if (!res.ok) {
      const errData = await res.json();
      throw new Error(errData.detail || `Failed to process ${type}`);
    }

    const data = await res.json();
    showAlert(`Successfully processed ${type} of $${data.amount || amount}!`, "success");

    // Clear form and refresh wallet view
    document.getElementById("movement-amount").value = "";
    document.getElementById("movement-description").value = "";
    await inspectUserWallets(userId);
  } catch (err) {
    showAlert(`Error: ${err.message}`, "danger");
  } finally {
    if (btn) {
      btn.disabled = false;
      btn.innerHTML = type === 'deposit' ? `<i class="bi bi-arrow-down-circle me-1"></i> Deposit` : `<i class="bi bi-arrow-up-circle me-1"></i> Withdraw`;
    }
  }
}

function escapeHtml(str) {
  if (!str) return '';
  return str.replace(/[&<>"']/g, function(m) {
    return {
      '&': '&amp;',
      '<': '&lt;',
      '>': '&gt;',
      '"': '&quot;',
      "'": '&#039;'
    }[m];
  });
}
