/**
 * News interaction layer.
 * Talks to /api/news/top-headlines and /api/news/search (routes/news.py).
 *
 * WHY INFINITE SCROLL (not just a "Load More" button):
 * An IntersectionObserver watches a 1px sentinel element at the
 * bottom of the news grid — when it scrolls into view, the next page
 * loads automatically. This matches "Infinite Scroll" as its own
 * listed feature (distinct from manual pagination).
 */

const state = {
  mode: "top-headlines", // "top-headlines" | "search"
  query: "",
  category: "general",
  page: 1,
  loading: false,
  hasMore: true,
};

window.newsState = state;

// Namespaced per logged-in user (or "guest") so switching accounts
// on the same browser doesn't restore the previous person's search.
const SEARCH_STATE_KEY = "ai_news_last_search_" + (window.CURRENT_USER_ID || "guest");

function saveSearchState() {
  localStorage.setItem(SEARCH_STATE_KEY, JSON.stringify({
    mode: state.mode,
    query: state.query,
    category: state.category,
  }));
}

function restoreSearchState() {
  const saved = localStorage.getItem(SEARCH_STATE_KEY);
  if (!saved) return false;

  try {
    const parsed = JSON.parse(saved);
    if (parsed.mode === "search" && parsed.query) {
      state.mode = "search";
      state.query = parsed.query;
      state.page = 1;
      state.hasMore = true;
      updateSectionHeading(`Results for "${parsed.query}"`, "Live search results");
      fetchAndRender({ replace: true });
      return true;
    }
    if (parsed.mode === "top-headlines" && parsed.category && parsed.category !== "general") {
      state.mode = "top-headlines";
      state.category = parsed.category;
      state.page = 1;
      state.hasMore = true;
      updateSectionHeading(`${capitalize(parsed.category)} News`, "Top headlines for this category");
      fetchAndRender({ replace: true });
      return true;
    }
  } catch (err) {
    // corrupted localStorage value — fall back to the default view
  }
  return false;
}

document.addEventListener("DOMContentLoaded", () => {
  const grid = document.getElementById("newsGrid");
  if (!grid) return; // not on a page with the news grid

  wireSearchForms();
  wireCategoryChips();
  wireRefreshButton();
  wireInfiniteScroll();
  restoreSearchState();
});

function wireSearchForms() {
  const heroForm = document.getElementById("heroSearchForm");
  const heroInput = document.getElementById("heroSearchInput");
  if (heroForm) {
    heroForm.addEventListener("submit", (e) => {
      e.preventDefault();
      const query = heroInput.value.trim();
      if (!query) return;

      runSearch(query);

      // Auto-scroll down to the news results after searching, so the
      // person doesn't have to manually scroll to see what they searched for.
      const newsSection = document.getElementById("newsSection");
      if (newsSection) {
        if (window.smoothScrollTo) {
          window.smoothScrollTo(newsSection, 900);
        } else {
          newsSection.scrollIntoView({ block: "start" });
        }
      }
    });
  }
}

function wireCategoryChips() {
  document.querySelectorAll(".category-chip").forEach((chip) => {
    chip.addEventListener("click", (e) => {
      e.preventDefault();
      const category = chip.dataset.category;
      state.mode = "top-headlines";
      state.category = category;
      state.page = 1;
      state.hasMore = true;
      updateSectionHeading(`${capitalize(category)} News`, "Top headlines for this category");
      fetchAndRender({ replace: true });
      showSwipeHint();

      const newsSection = document.getElementById("newsSection");
      if (newsSection) {
        if (window.smoothScrollTo) {
          window.smoothScrollTo(newsSection, 900);
        } else {
          newsSection.scrollIntoView({ block: "start" });
        }
      }
    });
  });
}

function wireRefreshButton() {
  const btn = document.getElementById("refreshBtn");
  if (!btn) return;
  btn.addEventListener("click", () => {
    state.page = 1;
    state.hasMore = true;
    fetchAndRender({ replace: true });
  });
}

function wireInfiniteScroll() {
  const sentinel = document.getElementById("infiniteScrollSentinel");
  if (!sentinel) return;

  const observer = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting && !state.loading && state.hasMore) {
        state.page += 1;
        fetchAndRender({ replace: false });
      }
    });
  }, { rootMargin: "200px" }); // start loading a bit before it's fully visible

  observer.observe(sentinel);
}

function runSearch(query) {
  if (!query) return;
  state.mode = "search";
  state.query = query;
  state.page = 1;
  state.hasMore = true;
  updateSectionHeading(`Results for "${query}"`, "Live search results");
  fetchAndRender({ replace: true });
  showSwipeHint();
}

function updateSectionHeading(title, subtitle) {
  const titleEl = document.getElementById("newsSectionTitle");
  const subEl = document.getElementById("newsSectionSubtitle");
  if (titleEl) titleEl.textContent = title;
  if (subEl) subEl.textContent = subtitle;
}

function showSwipeHint() {
  let hint = document.getElementById("swipeHint");
  if (!hint) {
    hint = document.createElement("div");
    hint.id = "swipeHint";
    hint.className = "swipe-hint";
    hint.innerHTML = `<i class='bx bx-chevron-down'></i> Scroll down to explore more news`;
    const heading = document.querySelector(".section-heading.with-action");
    heading?.insertAdjacentElement("afterend", hint);
  }
  hint.classList.add("show");

  const dismiss = () => hint.classList.remove("show");
  window.addEventListener("scroll", dismiss, { once: true });
  setTimeout(dismiss, 4000);
}

async function fetchAndRender({ replace }) {
  if (state.loading) return;
  state.loading = true;
  toggleSkeleton(true);
  hideBanner();

  try {
    const url = buildRequestUrl();
    const resp = await fetch(url);
    const data = await resp.json();

    if (!data.ok) {
      state.hasMore = false;
      toggleNoResults(replace);
      return;
    }

    if (!data.articles || data.articles.length === 0) {
      state.hasMore = false;
      if (replace) clearGrid();
      toggleNoResults(replace);
      return;
    }

    toggleNoResults(false);
    renderArticles(data.articles, { replace });
    saveSearchState();
  } catch (err) {
    state.hasMore = false;
  } finally {
    state.loading = false;
    toggleSkeleton(false);
  }
}

function buildRequestUrl() {
  const params = new URLSearchParams({ page: state.page });
  if (state.mode === "search") {
    params.set("q", state.query);
    return `/api/news/search?${params.toString()}`;
  }
  params.set("category", state.category);
  params.set("country", "us");
  return `/api/news/top-headlines?${params.toString()}`;
}

function renderArticles(articles, { replace }) {
  const grid = document.getElementById("newsGrid");
  if (replace) grid.innerHTML = "";

  articles.forEach((article) => {
    grid.insertAdjacentHTML("beforeend", articleCardHTML(article));
  });
}

function clearGrid() {
  const grid = document.getElementById("newsGrid");
  if (grid) grid.innerHTML = "";
}

function toggleNoResults(show) {
  const el = document.getElementById("noResultsMsg");
  if (el) el.classList.toggle("d-none", !show);
}

function toggleSkeleton(show) {
  const el = document.getElementById("newsSkeleton");
  if (el) el.classList.toggle("d-none", !show);
}

function hideBanner() {
  const banner = document.getElementById("apiBanner");
  if (banner) banner.style.display = "none";
}

function articleCardHTML(article) {
  const title = escapeHtml(article.title);
  const description = escapeHtml(article.description || "No description available.");
  const source = escapeHtml(article.source || "Unknown Source");
  const readingTime = escapeHtml(article.reading_time || "");
  const category = escapeHtml(article.category || "News");
  const image = article.image || "https://images.unsplash.com/photo-1495020689067-958852a7765e?q=80&w=800";
  const url = article.url || "#";
  const published = formatTimeAgo(article.published);

  return `
    <div class="col-md-6 col-lg-4 news-item">
      <div class="news-card">
        <div class="news-card-image" style="background-image:url('${image}')">
          <span class="news-card-category">${category}</span>
          <button class="news-card-bookmark bookmark-btn"
                  data-title="${title.replace(/"/g, '&quot;')}"
                  data-url="${url}"
                  data-image="${image}"
                  data-source="${source.replace(/"/g, '&quot;')}"
                  aria-label="Bookmark article"><i class='bx bx-bookmark'></i></button>
        </div>
        <div class="news-card-body">
          <h3>${title}</h3>
          <p>${description}</p>
          <div class="news-card-meta">
            <span><i class='bx bx-news'></i> ${source}</span>
            <span><i class='bx bx-time-five'></i> ${readingTime}</span>
          </div>
          <div class="news-card-footer">
            <span class="news-card-date">${published}</span>
            <div class="d-flex align-items-center gap-2">
              <button class="icon-btn small share-btn"
                      data-title="${title.replace(/"/g, '&quot;')}"
                      data-url="${url}"
                      aria-label="Share article"><i class='bx bx-share-alt'></i></button>
              <a href="${url}" target="_blank" rel="noopener" class="btn btn-sm btn-primary-gradient">Read More</a>
            </div>
          </div>
        </div>
      </div>
    </div>`;
}

function formatTimeAgo(isoString) {
  if (!isoString) return "";
  const published = new Date(isoString);
  if (isNaN(published)) return isoString;
  const seconds = (Date.now() - published.getTime()) / 1000;
  if (seconds < 3600) return `${Math.max(Math.round(seconds / 60), 1)} min ago`;
  if (seconds < 86400) return `${Math.floor(seconds / 3600)} hours ago`;
  return `${Math.floor(seconds / 86400)} days ago`;
}

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str;
  return div.innerHTML;
}

function capitalize(str) {
  return str.charAt(0).toUpperCase() + str.slice(1);
}