/**
 * Shared toast notification system.
 * Replaces the small ad-hoc toast function that used to live only in
 * news.js — now every script (chat, bookmarks, offline detection, etc.)
 * calls the same window.showToast(), so notifications look and behave
 * consistently everywhere.
 */

(function () {
  function ensureContainer() {
    let container = document.getElementById("toastContainer");
    if (!container) {
      container = document.createElement("div");
      container.id = "toastContainer";
      container.className = "toast-container";
      document.body.appendChild(container);
    }
    return container;
  }

  const ICONS = {
    success: "bx-check-circle",
    error: "bx-error-circle",
    info: "bx-info-circle",
  };

  window.showToast = function (message, type = "info", duration = 4000) {
    const container = ensureContainer();
    const toast = document.createElement("div");
    toast.className = `app-toast app-toast-${type}`;
    toast.innerHTML = `<i class='bx ${ICONS[type] || ICONS.info}'></i><span>${escapeHtml(message)}</span>`;
    container.appendChild(toast);

    // Trigger the entrance transition on the next frame
    requestAnimationFrame(() => toast.classList.add("show"));

    setTimeout(() => {
      toast.classList.remove("show");
      toast.classList.add("hide");
      toast.addEventListener("transitionend", () => toast.remove(), { once: true });
    }, duration);
  };

  function escapeHtml(str) {
    const div = document.createElement("div");
    div.textContent = str;
    return div.innerHTML;
  }
})();
