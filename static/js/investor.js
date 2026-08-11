/**
 * INVESTOR DASHBOARD CONTROLLER
 */

let currentInvestorUser = null;
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

// 2. Wallet Info
async function loadInvestorWallet() {
  const balanceEl = document.getElementById("investor-wallet-balance");
  const nameEl = document.getElementById("investor-wallet-name");
  const uuidEl = document.getElementById("investor-wallet-uuid");

  if (balanceEl) balanceEl.textContent = "$--.--";

  try {
    const res = await fetch("/wallet/me", {
      credentials: "include"
    });

    if (!res.ok) throw new Error("Failed to load wallet details");

    const wallets = await res.json();

    if (!wallets || wallets.length === 0) {
      if (balanceEl) balanceEl.textContent = "$0.00";
      if (nameEl) nameEl.textContent = "No Wallet Found";
      return;
    }

    const primaryWallet = wallets[0];
    currentInvestorWallet = primaryWallet;

    if (balanceEl) balanceEl.textContent = `$${primaryWallet.balance || "0.00"}`;
    if (nameEl) nameEl.textContent = primaryWallet.wallet_name || primaryWallet.name || "Primary Investor Wallet";
    if (uuidEl) uuidEl.textContent = primaryWallet.Wallet_id || primaryWallet.uuid || "";

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

    if (!projects || projects.length === 0) {
      container.innerHTML = `<tr><td colspan="4" class="text-center text-muted py-4">No investment projects currently available.</td></tr>`;
      return;
    }

    container.innerHTML = projects.map(p => `
      <tr>
        <td class="fw-bold">${escapeHtml(p.name)}</td>
        <td><strong>$${p.initial_amount || "0.00"}</strong></td>
        <td>
          <span class="badge badge-status ${p.status === 'ACTIVE' ? 'badge-active' : 'badge-closed'}">
            ${p.status || 'ACTIVE'}
          </span>
        </td>
        <td>
          <button class="btn btn-sm btn-custom-primary" onclick="handleInvestmentRequest('${p.uuid}', '${escapeHtml(p.name)}')">
            <i class="bi bi-piggy-bank me-1"></i> Invest
          </button>
        </td>
      </tr>
    `).join('');

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

  const amountStr = prompt(`Enter investment amount for project "${projectName}":`, "100.00");
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
