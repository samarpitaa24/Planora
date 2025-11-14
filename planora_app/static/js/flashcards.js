/**
 * Planora Flashcards Script - Enhanced
 * Features:
 * - Upload PDF/TXT/DOCX
 * - Flippable flashcards with smooth 3D animation
 * - Smooth left/right navigation
 * - Arrow controls positioned below cards
 * - Progress tracking
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
let isFlipped = false

// Pastel color palette for cards
const cardColors = [
  "#FFE5E9", // Pastel pink
  "#E5F0FF", // Pastel blue
  "#E5FFE9", // Pastel mint
  "#FFF5E5", // Pastel peach
  "#F0E5FF", // Pastel purple
  "#E5FFF5", // Pastel cyan
]

uploadBtn?.addEventListener("click", handleUpload)
cancelBtn?.addEventListener("click", cancelUpload)
flashInner?.addEventListener("click", flipCard)
flashLeft?.addEventListener("click", showPrev)
flashRight?.addEventListener("click", showNext)

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

  uploadStatus.textContent = "📄 Processing PDF..."
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
      flashcards = data.flashcards
      currentIndex = 0
      isFlipped = false
      if (flashcards.length > 0) {
        uploadStatus.textContent = ""
        showCard(currentIndex)
        updateProgress()
      } else {
        uploadStatus.textContent = "No flashcards found in document."
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

  // Reset flip state when changing cards
  isFlipped = false
  flashInner.classList.remove("flipped")

  // const flashCard = document.getElementById("flashcard-card")
  // if (flashCard) {
  //   flashCard.style.background = color
  // }


  const flashCard = document.getElementById("flashcard-card")
  if (flashCard) {
  flashCard.style.background = "#FFFFFF"  // ✅ string
  }


  if (card.type === "concept") {
    flashFront.innerHTML = `<strong>${card.front}</strong>`
    flashBack.innerHTML = `<p>${card.back}</p>`
  } else if (card.type === "question") {
    flashFront.innerHTML = `<strong>Q: ${card.front}</strong>`
    flashBack.innerHTML = `<p><strong>A:</strong> ${card.back}</p>`
  } else {
    flashFront.innerHTML = `<strong>${card.front || "Card"}</strong>`
    flashBack.innerHTML = `<p>${card.back || ""}</p>`
  }

  updateProgress()
  updateNavigation()
}

function flipCard() {
  isFlipped = !isFlipped
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
  if (flashLeft) flashLeft.classList.toggle("disabled", currentIndex === 0)
  if (flashRight) flashRight.classList.toggle("disabled", currentIndex === flashcards.length - 1)
}
