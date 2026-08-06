/**
 * Core application JavaScript — Phase 1.
 * Only the dark/light mode toggle exists so far; later phases add
 * their own JS files (news.js, chat.js, etc.) rather than growing
 * this one file indefinitely.
 */

document.addEventListener("DOMContentLoaded", () => {
  initPageLoader();
  initThemeToggle();
  initBackToTop();
  initNewsletterForm();
  initScrollReveal();
  initAnchorSmoothScroll();
  initCategoryCarousel();
});

/** Left/right arrow buttons for the category carousel — scrolls by
 *  roughly 3 chips' width per click, using the row's native smooth
 *  scrolling (scroll-behavior: smooth is set on .category-grid in
 *  CSS). Touch/trackpad swiping works natively too since the row is
 *  just a horizontally scrollable flex container. */
function initCategoryCarousel() {
  const grid = document.getElementById("categoryGrid");
  const leftBtn = document.getElementById("categoryArrowLeft");
  const rightBtn = document.getElementById("categoryArrowRight");
  if (!grid || !leftBtn || !rightBtn) return;

  const scrollAmount = () => grid.clientWidth * 0.7;

  leftBtn.addEventListener("click", () => {
    grid.scrollBy({ left: -scrollAmount(), behavior: "smooth" });
  });
  rightBtn.addEventListener("click", () => {
    grid.scrollBy({ left: scrollAmount(), behavior: "smooth" });
  });

  function updateArrowState() {
    leftBtn.disabled = grid.scrollLeft <= 4;
    rightBtn.disabled = grid.scrollLeft >= grid.scrollWidth - grid.clientWidth - 4;
  }

  grid.addEventListener("scroll", updateArrowState);
  window.addEventListener("resize", updateArrowState);
  updateArrowState();
}

/** Smooth scrolling ONLY for in-page anchor links (e.g. navbar "News"
 *  linking to #newsSection) — not applied globally, so normal mouse
 *  wheel/trackpad scrolling stays fast and responsive instead of
 *  feeling heavy.
 *
 *  Uses a custom eased animation instead of the browser's native
 *  scrollIntoView(behavior:"smooth") — native smooth-scroll speed
 *  and easing varies inconsistently across browsers and can feel
 *  abrupt; this version gives a fixed, comfortable duration with a
 *  gentle ease-in-out curve every time. */
function initAnchorSmoothScroll() {
  document.querySelectorAll('a[href*="#"]').forEach((link) => {
    link.addEventListener("click", (e) => {
      const url = new URL(link.href, window.location.href);
      const isSamePage = url.pathname === window.location.pathname;
      if (!isSamePage || !url.hash) return;

      const target = document.querySelector(url.hash);
      if (!target) return;

      e.preventDefault();

      if (link.hasAttribute("data-instant-scroll")) {
        target.scrollIntoView({ block: "start" }); // no animation — instant jump
      } else {
        smoothScrollTo(target, 900);
      }
    });
  });
}

window.smoothScrollTo = smoothScrollTo;

function smoothScrollTo(target, duration = 900) {
  const startY = window.scrollY;
  const targetY = target.getBoundingClientRect().top + window.scrollY;
  const distance = targetY - startY;
  let startTime = null;

  function easeInOutCubic(t) {
    return t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;
  }

  function step(currentTime) {
    if (startTime === null) startTime = currentTime;
    const elapsed = currentTime - startTime;
    const progress = Math.min(elapsed / duration, 1);
    const eased = easeInOutCubic(progress);

    window.scrollTo(0, startY + distance * eased);

    if (progress < 1) {
      requestAnimationFrame(step);
    }
  }

  requestAnimationFrame(step);
}

/** Fades and slides cards/chips into view as they scroll into the
 *  viewport, using IntersectionObserver so it costs nothing until
 *  elements are near the viewport. Re-observes automatically for
 *  cards added later by news.js (search/category/infinite scroll)
 *  via a MutationObserver on the news grid. */
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

  const grid = document.getElementById("newsGrid");
  if (grid) {
    new MutationObserver(observeAll).observe(grid, { childList: true });
  }
}


/** Shown briefly on every page load (including navigating to
 *  About/Bookmarks from the menu, since those are full page loads
 *  too, not single-page-app transitions) — fades out once the page
 *  has fully rendered, so nothing ever "pops" into view unstyled. */
function initPageLoader() {
  const overlay = document.getElementById("pageLoader");
  if (!overlay) return;
  window.addEventListener("load", () => {
    setTimeout(() => overlay.classList.add("page-loader-hidden"), 250);
  });
}

function initNewsletterForm() {
  const form = document.querySelector(".newsletter-form");
  if (!form) return;

  form.addEventListener("submit", (e) => {
    e.preventDefault();
    const input = form.querySelector("input[type=email]");
    if (!input.value.trim()) return;
    alert("Thanks! No email service is connected yet — this confirms the form works.");
    input.value = "";
  });
}

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

function initThemeToggle() {
  const root = document.documentElement;
  const toggleBtn = document.getElementById("themeToggle");
  if (!toggleBtn) return;
  const icon = toggleBtn.querySelector("i");

  const saved = localStorage.getItem("theme") || "light";
  root.setAttribute("data-theme", saved);
  updateIcon(saved);

  toggleBtn.addEventListener("click", () => {
    const current = root.getAttribute("data-theme");
    const next = current === "dark" ? "light" : "dark";
    root.setAttribute("data-theme", next);
    localStorage.setItem("theme", next);
    updateIcon(next);
  });

  function updateIcon(theme) {
    icon.className = theme === "dark" ? "bx bx-sun" : "bx bx-moon";
  }
}