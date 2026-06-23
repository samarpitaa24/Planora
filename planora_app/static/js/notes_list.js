document.addEventListener("DOMContentLoaded", () => {
  const notesList = document.getElementById("notesList");
  const noteSearch = document.getElementById("noteSearch");
  const filterType = document.getElementById("filterType");
  const filterDate = document.getElementById("filterDate");
  const filterMonth = document.getElementById("filterMonth");
  const filterYear = document.getElementById("filterYear");
  const applyFilter = document.getElementById("applyFilter");
  const openAddNoteBtn = document.getElementById("openAddNoteBtn");
  const noteModal = document.getElementById("noteModal");
  const closeNoteModal = document.getElementById("closeNoteModal");
  const cancelNoteBtn = document.getElementById("cancelNoteBtn");
  const saveNoteBtn = document.getElementById("saveNoteBtn");
  const noteModalText = document.getElementById("noteModalText");
  const noteModalTitle = document.getElementById("noteModalTitle");

  let allNotes = [];
  let editingNoteId = null;

  // Fetch notes
  function fetchNotes(filterTypeValue = "", filterValue = "") {
    fetch(
      `/notes/fetch?user_id=${USER_ID}&filter_type=${filterTypeValue}&filter_value=${filterValue}`,
    )
      .then((res) => res.json())
      .then((data) => {
        allNotes = data.notes;
        renderNotes(allNotes);
      });
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

  function getFilterValue() {
    if (filterType.value === "date") return filterDate.value;
    if (filterType.value === "month") return filterMonth.value;
    if (filterType.value === "year") return filterYear.value;
    return "";
  }

  function filterNotesBySearch(notes) {
    const term = noteSearch.value.trim().toLowerCase();
    if (!term) return notes;
    return notes.filter((n) => n.text.toLowerCase().includes(term));
  }

  function openNoteModal(editMode = false, note = null) {
    noteModal.style.display = "flex";
    if (editMode && note) {
      noteModalTitle.textContent = "Edit Note";
      noteModalText.value = note.text;
      saveNoteBtn.textContent = "Update Note";
      editingNoteId = note._id;
    } else {
      noteModalTitle.textContent = "Add Note";
      noteModalText.value = "";
      saveNoteBtn.textContent = "Save Note";
      editingNoteId = null;
    }
    noteModalText.focus();
  }

  function closeNoteModalDialog() {
    noteModal.style.display = "none";
    noteModalText.value = "";
    editingNoteId = null;
  }

  function renderNotes(notes) {
    notesList.innerHTML = "";
    notes.forEach((note) => {
      const li = document.createElement("li");
      li.className = "note-item";
      li.dataset.id = note._id;

      const snippet =
        note.text.split(" ").length > 35
          ? note.text.split(" ").slice(0, 35).join(" ") + "..."
          : note.text;

      li.innerHTML = `
        <div class="note-main">
          <div class="note-text" title="Double click to view full note or click to open detail view">
            ${snippet}
          </div>
          <div class="note-meta">
            <span>${formatDateTimeIST(note.created_at)}</span>
            ${note.starred ? '<span class="pinned-label">Pinned</span>' : ''}
          </div>
        </div>
        <div class="note-actions">
          <button class="note-action note-star" aria-label="Toggle pin">
            ${note.starred ? "★" : "☆"}
          </button>
          <button class="note-action note-edit" aria-label="Edit note">✎</button>
          <button class="note-action note-delete" aria-label="Delete note">🗑</button>
        </div>
      `;

      const textDiv = li.querySelector(".note-text");
      textDiv.addEventListener("click", () => {
        window.location.href = `/notes-detail?id=${note._id}`;
      });
      textDiv.addEventListener("dblclick", (e) => {
        e.stopPropagation();
        if (textDiv.textContent === snippet) {
          textDiv.textContent = note.text;
        } else {
          textDiv.textContent = snippet;
        }
      });

      const starButton = li.querySelector(".note-star");
      starButton.addEventListener("click", (e) => {
        e.stopPropagation();
        const newStar = !note.starred;
        fetch("/notes/toggle_star", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ note_id: note._id, starred: newStar }),
        })
          .then((res) => res.json())
          .then((data) => {
            if (data.success) {
              note.starred = newStar;
              fetchNotes(filterType.value, getFilterValue());
            }
          });
      });

      const editButton = li.querySelector(".note-edit");
      editButton.addEventListener("click", (e) => {
        e.stopPropagation();
        openNoteModal(true, note);
      });

      const deleteButton = li.querySelector(".note-delete");
      deleteButton.addEventListener("click", (e) => {
        e.stopPropagation();
        if (!confirm("Delete this note?")) return;
        fetch("/notes/delete", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ note_id: note._id }),
        })
          .then((res) => res.json())
          .then((data) => {
            if (data.success) {
              fetchNotes(filterType.value, getFilterValue());
            } else {
              alert(data.error || "Failed to delete note.");
            }
          });
      });

      notesList.appendChild(li);
    });
  }

  // Search notes
  noteSearch.addEventListener("input", () => {
    renderNotes(filterNotesBySearch(allNotes));
  });

  // Filter type show/hide
  filterType.addEventListener("change", () => {
    filterDate.style.display =
      filterType.value === "date" ? "inline-block" : "none";
    filterMonth.style.display =
      filterType.value === "month" ? "inline-block" : "none";
    filterYear.style.display =
      filterType.value === "year" ? "inline-block" : "none";
  });

  openAddNoteBtn.addEventListener("click", () => {
    openNoteModal();
  });

  closeNoteModal.addEventListener("click", closeNoteModalDialog);
  cancelNoteBtn.addEventListener("click", closeNoteModalDialog);
  noteModal.addEventListener("click", (e) => {
    if (e.target === noteModal) {
      closeNoteModalDialog();
    }
  });

  saveNoteBtn.addEventListener("click", () => {
    const noteText = noteModalText.value.trim();
    if (!noteText) {
      alert("Please enter note text.");
      return;
    }

    const url = editingNoteId ? "/notes/update" : "/notes/save";
    const payload = editingNoteId
      ? { note_id: editingNoteId, text: noteText }
      : { text: noteText };

    fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    })
      .then((res) => res.json())
      .then((data) => {
        if (data.success) {
          closeNoteModalDialog();
          fetchNotes(filterType.value, getFilterValue());
        } else {
          alert(data.error || "Unable to save note.");
        }
      });
  });

  applyFilter.addEventListener("click", () => {
    let val = "";
    if (filterType.value === "date") val = filterDate.value;
    else if (filterType.value === "month") val = filterMonth.value;
    else if (filterType.value === "year") val = filterYear.value;

    fetchNotes(filterType.value, val);
  });

  // Initial fetch
  fetchNotes();
});
