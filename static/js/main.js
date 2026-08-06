/**
 * GLOBAL AUTH & UTILITY SCRIPT
 */

// Global Notification Alert Helper
function showAlert(message, type = 'info') {
  const alertContainer = document.getElementById('alert-container');
  if (!alertContainer) return;

  const alertId = 'alert-' + Date.now();
  const alertHtml = `
    <div id="${alertId}" class="alert alert-${type} alert-dismissible fade show shadow-sm" role="alert">
      <div>${message}</div>
      <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    </div>
  `;

  alertContainer.insertAdjacentHTML('beforeend', alertHtml);

  setTimeout(() => {
    const el = document.getElementById(alertId);
    if (el) {
      el.classList.remove('show');
      setTimeout(() => el.remove(), 150);
    }
  }, 4000);
}

// Global Logout Handler
async function logout() {
  try {
    await fetch("/auth/logout", {
      method: "POST",
      credentials: "include"
    });
  } catch (err) {
    console.error("Logout request error:", err);
  } finally {
    window.location.href = "/";
  }
}

// Automatic Global Authentication Check on Index / Landing Page
async function checkAuth() {
  try {
    const res = await fetch("/auth/me", {
      credentials: "include"
    });

    if (!res.ok) {
      window.location.href = "/auth/google/login";
      return;
    }

    const data = await res.json();

    if (data.role === "admin") {
      window.location.href = "/admin";
    } else {
      window.location.href = "/investor";
    }

  } catch (err) {
    console.error("Auth check exception:", err);
    window.location.href = "/auth/google/login";
  }
}

// Auto-execute checkAuth only on index page (where script is invoked directly)
if (window.location.pathname === "/" || window.location.pathname === "/index.html") {
  checkAuth();
}
