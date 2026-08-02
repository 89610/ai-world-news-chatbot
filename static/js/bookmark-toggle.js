/**
 * Bookmark button handler (event delegation).
 * Attached once on document — works for both the server-rendered
 * first page load and cards injected later by news.js.
 */

document.addEventListener("click", async (e) => {
  const btn = e.target.closest(".bookmark-btn");
  if (!btn) return;
  e.preventDefault();

  const payload = {
    title: btn.dataset.title,
    url: btn.dataset.url,
    image: btn.dataset.image,
    source: btn.dataset.source,
  };

  btn.disabled = true;
  try {
    const resp = await fetch("/api/bookmarks", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const data = await resp.json();

    if (resp.status === 401 || data.auth_required) {
      window.location.href = "/auth/login";
      return;
    }

    if (!resp.ok || !data.ok) {
      console.error("Bookmark save failed:", resp.status, data);
      window.showToast?.(data.error || `Save failed (status ${resp.status})`, "error");
      return;
    }

    btn.querySelector("i").className = "bx bxs-bookmark";
    btn.style.color = "var(--color-primary)";
    window.showToast?.(data.already_saved ? "Already saved!" : "Saved to your bookmarks!", "success");
  } catch (err) {
    console.error("Bookmark network error:", err);
    window.showToast?.("Network error — check your connection.", "error");
  } finally {
    btn.disabled = false;
  }
});