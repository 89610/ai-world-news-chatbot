/**
 * Share button handler (event delegation).
 * Uses the native Web Share API where available (mobile browsers,
 * some desktop browsers) — this opens the device's real share sheet
 * (WhatsApp, Messages, Email, etc.). Falls back to copying the link
 * to the clipboard on browsers that don't support it (most desktop
 * browsers).
 */

document.addEventListener("click", async (e) => {
  const btn = e.target.closest(".share-btn");
  if (!btn) return;
  e.preventDefault();

  const title = btn.dataset.title || "Check out this article";
  const url = btn.dataset.url;
  if (!url) return;

  if (navigator.share) {
    try {
      await navigator.share({ title, url });
    } catch (err) {
      // user cancelled the share sheet — not an error, do nothing
    }
    return;
  }

  try {
    await navigator.clipboard.writeText(url);
    window.showToast?.("Link copied to clipboard!", "success");
  } catch (err) {
    window.showToast?.("Couldn't copy link.", "error");
  }
});