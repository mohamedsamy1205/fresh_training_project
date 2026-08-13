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
  await loadAdminInvestmentRequests();
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
    await loadAdminInvestmentRequests();
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

  container.innerHTML = `<tr><td colspan="5" class="text-center text-muted py-4"><span class="spinner-border spinner-border-sm me-2"></span>Loading projects...</td></tr>`;

  try {
    const res = await fetch("/projects", {
      credentials: "include"
    });

    if (!res.ok) throw new Error("Failed to fetch projects");

    const projects = await res.json();

    if (!projects || projects.length === 0) {
      container.innerHTML = `<tr><td colspan="5" class="text-center text-muted py-4">No investment projects found.</td></tr>`;
      return;
    }

    container.innerHTML = projects.map(p => {
      const status = (p.status || "").toUpperCase();
      let badgeClass = "badge-active";
      if (status === "CLOSED") badgeClass = "badge-closed";
      if (status === "DISTRIBUTED") badgeClass = "bg-info-subtle text-info border border-info-subtle";

      let actionContent = "";
      if (status === "ACTIVE") {
        actionContent = `
          <button class="btn btn-sm btn-outline-warning me-1" onclick="openCloseProjectModal('${p.uuid}', '${escapeHtml(p.name)}')"><i class="bi bi-lock-fill me-1"></i> Close</button>
          <button class="btn btn-sm btn-outline-danger" onclick="handleDeleteProject('${p.uuid}', '${escapeHtml(p.name)}', this)"><i class="bi bi-trash me-1"></i> Delete</button>
        `;
      } else if (status === "CLOSED") {
        actionContent = `
          <button class="btn btn-sm btn-outline-success me-1" onclick="handleDistributeProfits('${p.uuid}', this)"><i class="bi bi-cash-coin me-1"></i> Distribute</button>
          <button class="btn btn-sm btn-outline-danger" onclick="handleDeleteProject('${p.uuid}', '${escapeHtml(p.name)}', this)"><i class="bi bi-trash me-1"></i> Delete</button>
        `;
      } else if (status === "DISTRIBUTED") {
        actionContent = `
          <span class="text-success small fw-semibold me-2"><i class="bi bi-check-circle-fill me-1"></i> Distributed</span>
          <button class="btn btn-sm btn-outline-danger" onclick="handleDeleteProject('${p.uuid}', '${escapeHtml(p.name)}', this)"><i class="bi bi-trash me-1"></i> Delete</button>
        `;
      } else {
        actionContent = `
          <button class="btn btn-sm btn-outline-danger" onclick="handleDeleteProject('${p.uuid}', '${escapeHtml(p.name)}', this)"><i class="bi bi-trash me-1"></i> Delete</button>
        `;
      }

      return `
        <tr>
          <td class="fw-semibold">${escapeHtml(p.name)}</td>
          <td><code class="text-secondarySmall">${p.uuid}</code></td>
          <td><strong>$${p.initial_amount || "0.00"}</strong></td>
          <td>
            <span class="badge badge-status ${badgeClass}">
              ${status || 'ACTIVE'}
            </span>
          </td>
          <td>${actionContent}</td>
        </tr>
      `;
    }).join('');

  } catch (err) {
    console.error("Load projects error:", err);
    container.innerHTML = `<tr><td colspan="5" class="text-center text-danger py-4">Failed to load projects.</td></tr>`;
  }
}

// Open Close Project Modal
function openCloseProjectModal(projectId, projectName) {
  document.getElementById("close-project-id").value = projectId;
  document.getElementById("close-project-name").value = projectName;
  document.getElementById("close-final-amount").value = "";

  const modalEl = document.getElementById("closeProjectModal");
  if (modalEl) {
    const modal = bootstrap.Modal.getOrCreateInstance(modalEl);
    modal.show();
  }
}

// Handle Close Project Submission
async function handleConfirmCloseProject(event) {
  event.preventDefault();

  const projectId = document.getElementById("close-project-id").value;
  const finalAmount = document.getElementById("close-final-amount").value;

  if (!finalAmount || parseFloat(finalAmount) <= 0) {
    showAlert("Please enter a valid positive final valuation amount.", "warning");
    return;
  }

  const submitBtn = document.getElementById("btn-confirm-close-project");
  submitBtn.disabled = true;
  submitBtn.innerHTML = `<span class="spinner-border spinner-border-sm me-1"></span>Closing...`;

  try {
    const res = await fetch(`/admin/projects/${projectId}/close`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      credentials: "include",
      body: JSON.stringify({
        final_amount: finalAmount
      })
    });

    if (!res.ok) {
      const errData = await res.json();
      throw new Error(errData.detail || "Failed to close project");
    }

    showAlert("Project closed successfully!", "success");

    const modalEl = document.getElementById("closeProjectModal");
    if (modalEl) {
      const modal = bootstrap.Modal.getInstance(modalEl);
      if (modal) modal.hide();
    }

    await loadProjects();
  } catch (err) {
    showAlert(`Error: ${err.message}`, "danger");
  } finally {
    submitBtn.disabled = false;
    submitBtn.innerHTML = `<i class="bi bi-check2-square me-1"></i> Close Project`;
  }
}

// Handle Delete Project
async function handleDeleteProject(projectId, projectName, btnElement) {
  if (!confirm(`Are you sure you want to delete project "${projectName}"? This will transactionally delete all associated investment requests and records.`)) {
    return;
  }

  if (btnElement) {
    btnElement.disabled = true;
    btnElement.innerHTML = `<span class="spinner-border spinner-border-sm me-1"></span>Deleting...`;
  }

  try {
    const res = await fetch(`/admin/projects/${projectId}`, {
      method: "DELETE",
      credentials: "include"
    });

    if (!res.ok) {
      const errData = await res.json();
      throw new Error(errData.detail || "Failed to delete project");
    }

    const data = await res.json();
    showAlert(data.message || "Project deleted successfully!", "success");

    await loadProjects();
    await loadAdminInvestmentRequests();
  } catch (err) {
    showAlert(`Error: ${err.message}`, "danger");
    if (btnElement) {
      btnElement.disabled = false;
      btnElement.innerHTML = `<i class="bi bi-trash me-1"></i> Delete`;
    }
  }
}

// Handle Distribute Profits
async function handleDistributeProfits(projectId, btnElement) {
  if (btnElement) {
    btnElement.disabled = true;
    btnElement.innerHTML = `<span class="spinner-border spinner-border-sm me-1"></span>Distributing...`;
  }

  const idempotencyKey = 'dist-' + Date.now() + '-' + Math.random().toString(36).substring(2, 9);

  try {
    const res = await fetch(`/admin/projects/${projectId}/distribute-profits`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      credentials: "include",
      body: JSON.stringify({
        idempotency_key: idempotencyKey
      })
    });

    if (!res.ok) {
      const errData = await res.json();
      throw new Error(errData.detail || "Failed to distribute profits");
    }

    showAlert("Profits distributed successfully to investors!", "success");
    await loadProjects();
  } catch (err) {
    showAlert(`Error: ${err.message}`, "danger");
    if (btnElement) {
      btnElement.disabled = false;
      btnElement.innerHTML = `<i class="bi bi-cash-coin me-1"></i> Distribute Profits`;
    }
  }
}

// Load & Display Admin Investment Requests
async function loadAdminInvestmentRequests() {
  const container = document.getElementById("admin-requests-list");
  if (!container) return;

  container.innerHTML = `<tr><td colspan="7" class="text-center text-muted py-4"><span class="spinner-border spinner-border-sm me-2"></span>Loading investment requests...</td></tr>`;

  try {
    const projRes = await fetch("/projects", { credentials: "include" });
    if (!projRes.ok) throw new Error("Failed to fetch projects");
    const projects = await projRes.json();

    if (!allUsers || allUsers.length === 0) {
      const usersRes = await fetch("/admin/users/users", { credentials: "include" });
      if (usersRes.ok) {
        allUsers = await usersRes.json();
      }
    }

    const userMap = {};
    (allUsers || []).forEach(u => { userMap[u.uuid] = u.name; });

    const projectMap = {};
    (projects || []).forEach(p => { projectMap[p.uuid] = p.name; });

    if (!projects || projects.length === 0) {
      container.innerHTML = `<tr><td colspan="7" class="text-center text-muted py-4">No projects found.</td></tr>`;
      return;
    }

    const requestPromises = projects.map(p =>
      fetch(`/admin/projects/${p.uuid}/investment-requests`, { credentials: "include" })
        .then(r => r.ok ? r.json() : [])
        .catch(() => [])
    );

    const results = await Promise.all(requestPromises);
    const allRequests = [].concat(...results);

    allRequests.sort((a, b) => new Date(b.created_at) - new Date(a.created_at));

    if (allRequests.length === 0) {
      container.innerHTML = `<tr><td colspan="7" class="text-center text-muted py-4">No investment requests submitted yet.</td></tr>`;
      return;
    }

    container.innerHTML = allRequests.map(req => {
      const status = (req.status || "").toUpperCase();
      let badgeClass = "badge-pending";
      if (status === "APPROVED") badgeClass = "badge-success";
      if (status === "REJECTED") badgeClass = "badge-closed";

      const userName = userMap[req.user_id];
      const userDisplay = userName ? `${escapeHtml(userName)}` : `<code class="text-muted">${req.user_id ? req.user_id.substring(0, 8) + '...' : '--'}</code>`;

      const projectName = projectMap[req.project_id];
      const projectDisplay = projectName ? `${escapeHtml(projectName)}` : `<code class="text-muted">${req.project_id ? req.project_id.substring(0, 8) + '...' : '--'}</code>`;

      let actionBtns = "";
      if (status === "PENDING") {
        actionBtns = `
          <button class="btn btn-sm btn-success me-1" onclick="handleApproveRequest('${req.uuid}', this)">
            <i class="bi bi-check-circle me-1"></i> Approve
          </button>
          <button class="btn btn-sm btn-danger" onclick="handleRejectRequest('${req.uuid}', this)">
            <i class="bi bi-x-circle me-1"></i> Reject
          </button>
        `;
      } else {
        actionBtns = `<span class="text-muted small">--</span>`;
      }

      const createdDateStr = req.created_at ? new Date(req.created_at).toLocaleString() : '--';

      return `
        <tr>
          <td><code class="text-muted" title="${req.uuid}">${req.uuid ? req.uuid.substring(0, 8) + '...' : '--'}</code></td>
          <td class="fw-semibold">${userDisplay}</td>
          <td class="fw-semibold">${projectDisplay}</td>
          <td><strong>$${req.amount}</strong></td>
          <td>
            <span class="badge badge-status ${badgeClass}">
              ${status}
            </span>
          </td>
          <td class="text-muted small">${createdDateStr}</td>
          <td>${actionBtns}</td>
        </tr>
      `;
    }).join('');

  } catch (err) {
    console.error("Load admin investment requests error:", err);
    container.innerHTML = `<tr><td colspan="7" class="text-center text-danger py-4">Failed to load investment requests.</td></tr>`;
  }
}

// Handle Approve Request
async function handleApproveRequest(requestId, btnElement) {
  const cell = btnElement ? btnElement.parentElement : null;
  if (cell) {
    const btns = cell.querySelectorAll("button");
    btns.forEach(b => { b.disabled = true; });
    btnElement.innerHTML = `<span class="spinner-border spinner-border-sm me-1"></span>Approving...`;
  }

  const idempotencyKey = 'idemp-' + Date.now() + '-' + Math.random().toString(36).substring(2, 9);

  try {
    const res = await fetch(`/admin/projects/requests/${requestId}/approve?idempotency_key=${encodeURIComponent(idempotencyKey)}`, {
      method: "POST",
      credentials: "include"
    });

    if (!res.ok) {
      const errData = await res.json();
      throw new Error(errData.detail || "Failed to approve investment request");
    }

    showAlert("Investment request approved successfully!", "success");
    await loadAdminInvestmentRequests();
    await loadProjects();
  } catch (err) {
    showAlert(`Error: ${err.message}`, "danger");
    if (cell) {
      const btns = cell.querySelectorAll("button");
      btns.forEach(b => { b.disabled = false; });
      btnElement.innerHTML = `<i class="bi bi-check-circle me-1"></i> Approve`;
    }
  }
}

// Handle Reject Request
async function handleRejectRequest(requestId, btnElement) {
  const cell = btnElement ? btnElement.parentElement : null;
  if (cell) {
    const btns = cell.querySelectorAll("button");
    btns.forEach(b => { b.disabled = true; });
    btnElement.innerHTML = `<span class="spinner-border spinner-border-sm me-1"></span>Rejecting...`;
  }

  try {
    const res = await fetch(`/admin/projects/requests/${requestId}/reject`, {
      method: "POST",
      credentials: "include"
    });

    if (!res.ok) {
      const errData = await res.json();
      throw new Error(errData.detail || "Failed to reject investment request");
    }

    showAlert("Investment request rejected successfully.", "info");
    await loadAdminInvestmentRequests();
  } catch (err) {
    showAlert(`Error: ${err.message}`, "danger");
    if (cell) {
      const btns = cell.querySelectorAll("button");
      btns.forEach(b => { b.disabled = false; });
      btnElement.innerHTML = `<i class="bi bi-x-circle me-1"></i> Reject`;
    }
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
