/**
 * INVESTOR DASHBOARD CONTROLLER
 */

let currentInvestorUser = null;
let allInvestorWallets = [];
let currentInvestorWallet = null;

document.addEventListener("DOMContentLoaded", () => {
  initInvestorDashboard();
});

async function initInvestorDashboard() {
  await verifyInvestorAuth();
  await loadInvestorWallet();
  await loadInvestorProjects();
}

// 🔐 Auto Auth Check & Role Guard
async function verifyInvestorAuth() {
  try {
    const res = await fetch("/auth/me", {
      credentials: "include"
    });

    if (!res.ok) {
      window.location.href = "/auth/google/login";
      return;
    }

    const user = await res.json();
    currentInvestorUser = user;

    const investorNameEl = document.getElementById("investor-user-name");
    const investorEmailEl = document.getElementById("investor-user-email");

    if (investorNameEl) investorNameEl.textContent = user.name || "Investor";
    if (investorEmailEl) investorEmailEl.textContent = user.email || "";

  } catch (err) {
    console.error("Auth check error:", err);
    window.location.href = "/auth/google/login";
  }
}

// 2. Wallet Info & Multi-Wallet Switcher
async function loadInvestorWallet() {
  const balanceEl = document.getElementById("investor-wallet-balance");
  const nameEl = document.getElementById("investor-wallet-name");
  const uuidEl = document.getElementById("investor-wallet-uuid");
  const menuEl = document.getElementById("wallet-switch-menu");

  if (balanceEl) balanceEl.textContent = "$--.--";

  try {
    const res = await fetch("/wallet/me", {
      credentials: "include"
    });

    if (!res.ok) throw new Error("Failed to load wallet details");

    const wallets = await res.json();
    allInvestorWallets = wallets || [];

    if (allInvestorWallets.length === 0) {
      if (balanceEl) balanceEl.textContent = "$0.00";
      if (nameEl) nameEl.textContent = "No Wallet Found";
      if (menuEl) menuEl.innerHTML = `<li class="dropdown-item disabled text-muted">No wallets available</li>`;
      return;
    }

    // Restore saved active wallet or default to first wallet
    const savedWalletId = localStorage.getItem("active_investor_wallet_id");
    let activeWallet = allInvestorWallets.find(w => (w.Wallet_id || w.uuid) === savedWalletId);

    if (!activeWallet) {
      activeWallet = allInvestorWallets[0];
    }

    setActiveWallet(activeWallet, false);

    // Load recent transaction history if user ID is present
    if (currentInvestorUser && currentInvestorUser.uuid) {
      await loadRecentTransactions(currentInvestorUser.uuid);
    }

  } catch (err) {
    console.error("Load investor wallet error:", err);
    if (balanceEl) balanceEl.textContent = "$0.00";
    showAlert("Could not retrieve wallet balance.", "warning");
  }
}

function setActiveWallet(wallet, showNotification = true) {
  if (!wallet) return;
  currentInvestorWallet = wallet;
  const walletId = wallet.Wallet_id || wallet.uuid || "";
  localStorage.setItem("active_investor_wallet_id", walletId);

  const balanceEl = document.getElementById("investor-wallet-balance");
  const nameEl = document.getElementById("investor-wallet-name");
  const uuidEl = document.getElementById("investor-wallet-uuid");

  const walletName = wallet.wallet_name || wallet.name || "Investor Wallet";
  const balanceStr = wallet.balance !== undefined ? wallet.balance : "0.00";

  if (balanceEl) balanceEl.textContent = `$${balanceStr}`;
  if (nameEl) nameEl.textContent = walletName;
  if (uuidEl) uuidEl.textContent = walletId;

  renderWalletSwitchMenu();

  if (showNotification) {
    showAlert(`Switched active wallet to "${walletName}" ($${balanceStr})`, "info");
  }
}

function renderWalletSwitchMenu() {
  const menuEl = document.getElementById("wallet-switch-menu");
  if (!menuEl) return;

  if (!allInvestorWallets || allInvestorWallets.length === 0) {
    menuEl.innerHTML = `<li class="dropdown-item disabled text-muted">No wallets available</li>`;
    return;
  }

  const activeId = currentInvestorWallet ? (currentInvestorWallet.Wallet_id || currentInvestorWallet.uuid) : null;

  let itemsHtml = `<li class="dropdown-header text-uppercase small text-muted mb-1"><i class="bi bi-wallet2 me-1"></i>Select Active Wallet</li>`;

  itemsHtml += allInvestorWallets.map((w, index) => {
    const wId = w.Wallet_id || w.uuid;
    const wName = w.wallet_name || w.name || `Wallet ${index + 1}`;
    const isActive = wId === activeId;

    return `
      <li>
        <button class="dropdown-item d-flex justify-content-between align-items-center py-2 ${isActive ? 'active bg-primary text-white fw-bold' : ''}" 
                type="button" 
                onclick="selectWalletById('${wId}')">
          <div>
            <div class="fw-semibold">${escapeHtml(wName)}</div>
            <div class="small ${isActive ? 'text-white-50' : 'text-muted'}"><code>${wId.substring(0, 8)}...</code></div>
          </div>
          <span class="badge ${isActive ? 'bg-light text-dark' : 'bg-secondary text-white'} ms-2">
            $${w.balance !== undefined ? w.balance : "0.00"}
          </span>
        </button>
      </li>
    `;
  }).join('');

  menuEl.innerHTML = itemsHtml;
}

function selectWalletById(walletId) {
  const wallet = allInvestorWallets.find(w => (w.Wallet_id || w.uuid) === walletId);
  if (wallet) {
    setActiveWallet(wallet, true);
  }
}

// 1. View Projects
async function loadInvestorProjects() {
  const container = document.getElementById("investor-projects-list");
  if (!container) return;

  container.innerHTML = `<tr><td colspan="4" class="text-center text-muted py-4"><span class="spinner-border spinner-border-sm me-2"></span>Loading available projects...</td></tr>`;

  try {
    const res = await fetch("/projects", {
      credentials: "include"
    });

    if (!res.ok) throw new Error("Failed to fetch investment projects");

    const projects = await res.json();

    const activeProjects = (projects || []).filter(p => p.status && p.status.toUpperCase() === 'ACTIVE');

    if (activeProjects.length === 0) {
      container.innerHTML = `<tr><td colspan="4" class="text-center text-muted py-4">No active investment projects available.</td></tr>`;
      return;
    }

    container.innerHTML = activeProjects.map(p => {
      let actionHtml = '';

      if (p.user_request_status) {
        const reqStatus = String(p.user_request_status).toLowerCase();
        let badgeClass = 'bg-secondary text-white';
        let statusLabel = String(p.user_request_status).toUpperCase();

        if (reqStatus === 'pending') {
          badgeClass = 'bg-warning text-dark';
          statusLabel = 'Pending';
        } else if (reqStatus === 'approved' || reqStatus === 'accepted') {
          badgeClass = 'bg-success text-white';
          statusLabel = 'Approved';
        } else if (reqStatus === 'rejected') {
          badgeClass = 'bg-danger text-white';
          statusLabel = 'Rejected';
        }

        actionHtml = `
          <button class="btn btn-sm btn-secondary" disabled style="cursor: not-allowed; opacity: 0.8;">
            <span class="badge ${badgeClass} me-1">${statusLabel}</span>
          </button>
        `;
      } else {
        actionHtml = `
          <button class="btn btn-sm btn-custom-primary" onclick="handleInvestmentRequest('${p.uuid}', '${escapeHtml(p.name)}')">
            <i class="bi bi-piggy-bank me-1"></i> Invest
          </button>
        `;
      }

      return `
        <tr>
          <td class="fw-bold">${escapeHtml(p.name)}</td>
          <td><strong>$${p.initial_amount || "0.00"}</strong></td>
          <td>
            <span class="badge badge-status badge-active">
              ${p.status ? p.status.toUpperCase() : 'ACTIVE'}
            </span>
          </td>
          <td>
            ${actionHtml}
          </td>
        </tr>
      `;
    }).join('');

  } catch (err) {
    console.error("Load investor projects error:", err);
    container.innerHTML = `<tr><td colspan="4" class="text-center text-danger py-4">Failed to load projects.</td></tr>`;
  }
}

// Investment Request Handler
async function handleInvestmentRequest(projectId, projectName) {
  if (!currentInvestorWallet) {
    showAlert("No wallet available to perform investment.", "warning");
    return;
  }

  const walletName = currentInvestorWallet.wallet_name || currentInvestorWallet.name || "Active Wallet";
  const walletBal = currentInvestorWallet.balance !== undefined ? currentInvestorWallet.balance : "0.00";

  const amountStr = prompt(`Enter investment amount for project "${projectName}":\n(Active Wallet: ${walletName} | Available Balance: $${walletBal})`, "100.00");
  if (!amountStr) return;

  const amount = parseFloat(amountStr);
  if (isNaN(amount) || amount <= 0) {
    showAlert("Please enter a valid positive amount.", "warning");
    return;
  }

  try {
    const res = await fetch(`/investor/projects/${projectId}/investment-requests`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      credentials: "include",
      body: JSON.stringify({
        wallet_id: currentInvestorWallet.Wallet_id || currentInvestorWallet.uuid,
        amount: amountStr
      })
    });

    if (!res.ok) {
      const errData = await res.json();
      throw new Error(errData.detail || "Investment request failed");
    }

    const data = await res.json();
    showAlert(`Investment request of $${data.amount || amountStr} submitted successfully!`, "success");
    await loadInvestorWallet();
    await loadInvestorProjects();
  } catch (err) {
    showAlert(`Error: ${err.message}`, "danger");
  }
}

// Load Recent Transactions using Page/Limit Pagination
async function loadRecentTransactions(userId) {
  const container = document.getElementById("transactions-list");
  if (!container) return;

  container.innerHTML = `<tr><td colspan="4" class="text-center text-muted py-3">Loading transactions...</td></tr>`;

  try {
    const res = await fetch(`/investor/transactions/user/${userId}?page=1&limit=20`, {
      credentials: "include"
    });

    if (!res.ok) throw new Error("Failed to load transactions");

    const result = await res.json();
    const transactions = result.data || [];

    if (transactions.length === 0) {
      container.innerHTML = `<tr><td colspan="4" class="text-center text-muted py-3">No recent transactions found.</td></tr>`;
      return;
    }

    container.innerHTML = transactions.map(tx => `
      <tr>
        <td class="fw-semibold">${tx.type || 'TRANSFER'}</td>
        <td class="fw-bold">$${tx.amount}</td>
        <td>
          <span class="badge badge-status ${tx.status === 'SUCCESS' ? 'badge-success' : 'badge-pending'}">
            ${tx.status}
          </span>
        </td>
        <td class="text-muted small">${new Date(tx.created_at).toLocaleString()}</td>
      </tr>
    `).join('');

  } catch (err) {
    console.error("Transactions load error:", err);
    container.innerHTML = `<tr><td colspan="4" class="text-center text-muted py-3">No transaction history.</td></tr>`;
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
