/**
 * Phase 5: UI/animation polish.
 * Everything here is additive — it doesn't touch the Phase 1-4 logic
 * in app.js/news.js/chat.js, it just layers presentation and small
 * conveniences on top.
 */

document.addEventListener("DOMContentLoaded", () => {
  initPageLoader();
  initBackToTop();
  initOfflineDetection();
  initScrollReveal();
  initAutoRefresh();
  initShareButtons();
  initNewsletterForm();
});

/** Full-page loading overlay shown briefly on first paint, so the
 *  page never "pops" — fades out once everything's rendered. */
function initPageLoader() {
  const overlay = document.getElementById("pageLoader");
  if (!overlay) return;
  window.addEventListener("load", () => {
    setTimeout(() => overlay.classList.add("page-loader-hidden"), 250);
  });
}

/** Back-to-top button — appears after scrolling past one viewport height. */
function initBackToTop() {
  const btn = document.getElementById("backToTopBtn");
  if (!btn) return;

  window.addEventListener("scroll", () => {
    btn.classList.toggle("show", window.scrollY > window.innerHeight * 0.6);
  });

  btn.addEventListener("click", () => {
    window.scrollTo({ top: 0, behavior: "smooth" });
  });
}

/** Offline/online banner — tells the user connectivity changed, since
 *  search/chat/bookmarks all depend on network requests. */
function initOfflineDetection() {
  const showStatus = (isOnline) => {
    if (isOnline) {
      window.showToast?.("Back online.", "success", 2500);
    } else {
      window.showToast?.("You're offline — search, chat, and bookmarks won't work until connection returns.", "error", 6000);
    }
  };
  window.addEventListener("online", () => showStatus(true));
  window.addEventListener("offline", () => showStatus(false));
}

/** Fade/slide-in animation for cards as they scroll into view, using
 *  IntersectionObserver so it costs nothing until elements are near
 *  the viewport. Re-runs automatically for cards added later by
 *  news.js (search/load more) via a MutationObserver. */
function initScrollReveal() {
  const revealSelector = ".news-card, .category-chip";
  const observer = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        entry.target.classList.add("reveal-visible");
        observer.unobserve(entry.target);
      }
    });
  }, { threshold: 0.1 });

  function observeAll() {
    document.querySelectorAll(revealSelector).forEach((el) => {
      if (!el.classList.contains("reveal-init")) {
        el.classList.add("reveal-init");
        observer.observe(el);
      }
    });
  }

  observeAll();

  // Cards injected later (search results, load more, category clicks)
  // need the same treatment — watch the grid for additions.
  const grid = document.getElementById("newsGrid");
  if (grid) {
    new MutationObserver(observeAll).observe(grid, { childList: true });
  }
}

/** Silently refreshes the top-headlines view every 5 minutes, so a
 *  tab left open stays current without the user lifting a finger.
 *  Only runs on the home page's default view (not mid-search) so it
 *  doesn't clobber a search someone's actively looking at. */
function initAutoRefresh() {
  const grid = document.getElementById("newsGrid");
  const refreshBtn = document.getElementById("refreshBtn");
  if (!grid || !refreshBtn) return;

  const FIVE_MINUTES = 5 * 60 * 1000;
  setInterval(() => {
    if (window.newsState && window.newsState.mode === "top-headlines" && window.newsState.page === 1) {
      refreshBtn.click();
    }
  }, FIVE_MINUTES);
}

/** Share button — uses the native Web Share sheet on mobile/supported
 *  browsers, falls back to copying the link on desktop. */
function initShareButtons() {
  document.addEventListener("click", async (e) => {
    const btn = e.target.closest(".news-card-actions .icon-btn[aria-label='Share']");
    if (!btn) return;

    const card = btn.closest(".news-card");
    const link = card?.querySelector(".news-card-footer a")?.href;
    const title = card?.querySelector("h3")?.textContent || "Check out this article";
    if (!link) return;

    if (navigator.share) {
      try {
        await navigator.share({ title, url: link });
      } catch (err) {
        // user cancelled the share sheet — no error needed
      }
    } else {
      try {
        await navigator.clipboard.writeText(link);
        window.showToast?.("Link copied to clipboard.", "success");
      } catch (err) {
        window.showToast?.("Couldn't copy link.", "error");
      }
    }
  });
}

/** Newsletter form — POSTs to /api/newsletter/subscribe, which stores
 *  the email and sends a real confirmation email via Gmail SMTP. */
function initNewsletterForm() {
  const form = document.querySelector(".newsletter-form");
  if (!form) return;

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const input = form.querySelector("input[type=email]");
    const email = input.value.trim();
    if (!email) return;

    const btn = form.querySelector("button[type=submit]");
    btn.disabled = true;

    try {
      const resp = await fetch("/api/newsletter/subscribe", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email }),
      });
      const data = await resp.json();

      if (!data.ok) {
        window.showToast?.(data.error || "Couldn't subscribe right now.", "error");
        return;
      }
      if (data.already_subscribed) {
        window.showToast?.("You're already subscribed.", "info");
      } else if (data.email_sent) {
        window.showToast?.("Subscribed! Check your inbox for a confirmation email.", "success", 5000);
      } else {
        window.showToast?.("Subscribed! (Confirmation email couldn't be sent — check server mail config.)", "info", 5000);
      }
      input.value = "";
    } catch (err) {
      window.showToast?.("Network error — please try again.", "error");
    } finally {
      btn.disabled = false;
    }
  });
}
