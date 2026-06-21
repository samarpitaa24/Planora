document.addEventListener("DOMContentLoaded", function () {
  const saveBtn = document.getElementById("saveNoteBtn");
  const noteText = document.getElementById("noteText");
  const recentNoteEl = document.getElementById("recentNote");
  const recentNoteText = document.getElementById("recentNoteText");
  const recentNoteTime = document.getElementById("recentNoteTime");
  const statusEl = document.getElementById("noteStatus");

  function showStatus(msg, isError=false) {
    if (!statusEl) return;
    statusEl.style.display = "block";
    statusEl.textContent = msg;
    statusEl.style.color = isError ? "crimson" : "green";
    setTimeout(()=> { statusEl.style.display = "none"; }, 3000);
  }

  function formatDateTimeIST(timestamp) {
    if (!timestamp) return "";
    let dateObj = new Date(timestamp);
    if (Number.isNaN(dateObj.getTime())) {
      dateObj = new Date(timestamp.replace(" ", "T"));
    }
    if (Number.isNaN(dateObj.getTime())) return timestamp;
    return dateObj.toLocaleString("en-IN", {
      timeZone: "Asia/Kolkata",
      weekday: "short",
      year: "numeric",
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
      hour12: true,
    });
  }

  async function fetchLatest() {
    try {
      const res = await fetch("/notes/latest");
      if (!res.ok) return;
      const data = await res.json();
      const n = data.latest_note;
      if (!n) {
        if (recentNoteEl) recentNoteEl.style.display = "none";
        return;
      }
      if (recentNoteEl) recentNoteEl.style.display = "block";
      if (recentNoteText) recentNoteText.textContent = n.text;
      if (recentNoteTime) recentNoteTime.textContent = formatDateTimeIST(n.created_at) || "";
    } catch (err) {
      console.error("Failed to fetch latest note:", err);
    }
  }

  async function saveNote() {
    const text = noteText.value.trim();
    if (!text) {
      showStatus("Please type a note before saving.", true);
      return;
    }

    saveBtn.disabled = true;
    try {
      const res = await fetch("/notes/save", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text })
      });
      const data = await res.json();
      if (!res.ok) {
        showStatus(data.error || "Failed to save note", true);
        return;
      }
      noteText.value = ""; // clear input
      showStatus("Note saved!");
      await fetchLatest(); // update UI with newest note
    } catch (err) {
      console.error("Failed to save note:", err);
      showStatus("Network error while saving note", true);
    } finally {
      saveBtn.disabled = false;
    }
  }

  if (saveBtn) {
    saveBtn.addEventListener("click", saveNote);
  }

  // initial load
  fetchLatest();
});
