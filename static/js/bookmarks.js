/**
 * Bookmarks page controller.
 * Talks to GET/DELETE /api/bookmarks (routes/bookmark.py).
 */

document.addEventListener("DOMContentLoaded", loadBookmarks);

async function loadBookmarks() {
  const grid = document.getElementById("bookmarksGrid");
  const emptyMsg = document.getElementById("emptyBookmarksMsg");
  if (!grid) return;

  try {
    const resp = await fetch("/api/bookmarks");
    const data = await resp.json();

    if (!data.ok || !data.bookmarks.length) {
      emptyMsg.classList.remove("d-none");
      return;
    }

    data.bookmarks.forEach((b) => grid.insertAdjacentHTML("beforeend", bookmarkCardHTML(b)));

    document.querySelectorAll(".remove-bookmark-btn").forEach((btn) => {
      btn.addEventListener("click", () => removeBookmark(btn.dataset.id, btn));
    });
  } catch (err) {
    emptyMsg.classList.remove("d-none");
  }
}

async function removeBookmark(id, btn) {
  try {
    const resp = await fetch(`/api/bookmarks/${id}`, { method: "DELETE" });
    const data = await resp.json();
    if (data.ok) {
      const card = btn.closest(".news-item");
      if (card) card.remove();
    }
  } catch (err) {
    // no-op
  }
}

function bookmarkCardHTML(b) {
  const title = escapeHtml(b.title);
  const source = escapeHtml(b.source || "Unknown Source");
  const image = b.image || "https://images.unsplash.com/photo-1495020689067-958852a7765e?q=80&w=800";

  return `
    <div class="col-md-6 col-lg-4 news-item">
      <div class="news-card">
        <div class="news-card-image" style="background-image:url('${image}')">
          <button class="news-card-bookmark remove-bookmark-btn" data-id="${b.id}" aria-label="Remove bookmark" style="color:var(--color-primary);">
            <i class='bx bxs-bookmark'></i>
          </button>
        </div>
        <div class="news-card-body">
          <h3>${title}</h3>
          <div class="news-card-meta">
            <span><i class='bx bx-news'></i> ${source}</span>
          </div>
          <div class="news-card-footer">
            <a href="${b.url}" target="_blank" rel="noopener" class="btn btn-sm btn-primary-gradient">Read More</a>
          </div>
        </div>
      </div>
    </div>`;
}

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str;
  return div.innerHTML;
}