/**
 * Planora Flashcards Script - Enhanced with Smooth Flip Animation
 * Features:
 * - Upload PDF/TXT/DOCX documents
 * - Smooth 3D card flip animation on click
 * - Arrow navigation below cards (not overlapping)
 * - Progress tracking with disabled state
 * - Keyboard support (arrow keys)
 */

const uploadInput = document.getElementById("doc-upload")
const uploadBtn = document.querySelector(".upload-btn")
const cancelBtn = document.querySelector(".cancel-btn")
const uploadStatus = document.getElementById("upload-status")

const flashInner = document.getElementById("flashcard-inner")
const flashFront = document.getElementById("flashcard-front")
const flashBack = document.getElementById("flashcard-back")
const flashLeft = document.getElementById("flash-left")
const flashRight = document.getElementById("flash-right")
const flashProgress = document.getElementById("flash-progress")

let flashcards = []
let currentIndex = 0
let controller = null

// Pastel color palette - light and professional
const cardColors = [
  "#ffe5ed", // Pastel pink
  "#e5f0ff", // Pastel lavender
  "#e5ffe9", // Pastel mint
  "#fff5e5", // Pastel peach
  "#f0e5ff", // Pastel purple
  "#e8fff8", // Pastel cyan
]

uploadBtn?.addEventListener("click", handleUpload)
cancelBtn?.addEventListener("click", cancelUpload)
flashInner?.addEventListener("click", flipCard)
flashLeft?.addEventListener("click", showPrev)
flashRight?.addEventListener("click", showNext)

document.addEventListener("keydown", (e) => {
  if (flashcards.length === 0) return
  if (e.key === "ArrowLeft") showPrev()
  if (e.key === "ArrowRight") showNext()
  if (e.key === " ") {
    e.preventDefault()
    flipCard()
  }
})

function handleUpload() {
  const file = uploadInput.files[0]
  if (!file) {
    alert("Please select a file to upload.")
    return
  }

  const formData = new FormData()
  formData.append("file", file)
  formData.append("user_id", "6743c9d81d4d9d98ab11487b")

  controller = new AbortController()
  const signal = controller.signal

  uploadStatus.textContent = "📄 Processing document..."
  cancelBtn.style.display = "inline-block"

  setTimeout(() => {
    if (uploadStatus.textContent.includes("Processing")) {
      uploadStatus.textContent = "✨ Generating flashcards..."
    }
  }, 2000)

  fetch("/flashcards/upload", {
    method: "POST",
    body: formData,
    signal,
  })
    .then((res) => {
      if (!res.ok) throw new Error("Upload failed")
      return res.json()
    })
    .then((data) => {
      cancelBtn.style.display = "none"
      if (data.error) {
        uploadStatus.textContent = `❌ Error: ${data.error}`
        return
      }
      flashcards = data.flashcards || []
      currentIndex = 0
      if (flashcards.length > 0) {
        uploadStatus.textContent = ""
        showCard(currentIndex)
      } else {
        uploadStatus.textContent = "No flashcards generated from document."
      }
    })
    .catch((err) => {
      if (err.name === "AbortError") {
        uploadStatus.textContent = "Upload canceled."
      } else {
        uploadStatus.textContent = `❌ Error: ${err.message}`
      }
      cancelBtn.style.display = "none"
    })
}

function cancelUpload() {
  if (controller) {
    controller.abort()
    cancelBtn.style.display = "none"
  }
}

function showCard(index) {
  if (!flashcards[index]) return

  const card = flashcards[index]
  const color = cardColors[index % cardColors.length]

  // Reset to front side when navigating
  flashInner.classList.remove("flipped")

  // Apply pastel color background
  const flashCard = document.getElementById("flashcard-card")
  if (flashCard) {
    flashCard.style.background = color
  }

  if (card.type === "concept") {
    flashFront.innerHTML = `<strong>${escapeHtml(card.front)}</strong>`
    flashBack.innerHTML = `<p>${escapeHtml(card.back)}</p>`
  } else if (card.type === "question") {
    flashFront.innerHTML = `<strong>Q: ${escapeHtml(card.front)}</strong>`
    flashBack.innerHTML = `<p><strong>A:</strong> ${escapeHtml(card.back)}</p>`
  } else {
    flashFront.innerHTML = `<strong>${escapeHtml(card.front || "Card")}</strong>`
    flashBack.innerHTML = `<p>${escapeHtml(card.back || "")}</p>`
  }

  updateProgress()
  updateNavigation()
}

function escapeHtml(text) {
  const div = document.createElement("div")
  div.textContent = text
  return div.innerHTML
}

function flipCard() {
  if (flashcards.length === 0) return
  flashInner.classList.toggle("flipped")
}

function showNext() {
  if (currentIndex < flashcards.length - 1) {
    currentIndex++
    showCard(currentIndex)
  }
}

function showPrev() {
  if (currentIndex > 0) {
    currentIndex--
    showCard(currentIndex)
  }
}

function updateProgress() {
  if (flashProgress) {
    flashProgress.textContent = `${currentIndex + 1} / ${flashcards.length}`
  }
}

function updateNavigation() {
  if (flashLeft) {
    flashLeft.classList.toggle("disabled", currentIndex === 0)
    flashLeft.tabIndex = currentIndex === 0 ? -1 : 0
  }
  if (flashRight) {
    flashRight.classList.toggle("disabled", currentIndex === flashcards.length - 1)
    flashRight.tabIndex = currentIndex === flashcards.length - 1 ? -1 : 0
  }
}
