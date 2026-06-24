let flashcardSets = [];
let currentSet = null;
let currentIndex = 0;
let showingAnswer = false;

document.addEventListener("DOMContentLoaded", () => {

    const backButton = document.getElementById("back-to-chat");

    if (backButton && CONVERSATION_ID && CONVERSATION_ID !== "None" && CONVERSATION_ID !== "null") {
        backButton.href = `/chatbot/?conversation=${CONVERSATION_ID}`;
    } else if (backButton) {
        backButton.href = `/chatbot`;
    }

    loadFlashcardHistory();

    document
        .getElementById("show-answer-btn")
        .addEventListener("click", toggleAnswer);

    document
        .getElementById("next-btn")
        .addEventListener("click", nextCard);

    document
        .getElementById("previous-btn")
        .addEventListener("click", previousCard); });

async function loadFlashcardHistory(){

    const response = await fetch("/flashcards/history");

    flashcardSets = await response.json();

    renderHistory();

    if(!flashcardSets.length){

        showEmptyState();

        return;

    }

    let setId = SELECTED_SET;
    if (setId === "None" || setId === "null") {
        setId = null;
    }

    if(!setId){

        setId = flashcardSets[0].id;

    }

    loadFlashcardSet(setId);

}

function renderHistory(){

    const container =
        document.getElementById("flashcards-history");

    container.innerHTML = "";

    if(!flashcardSets.length){

        container.innerHTML = `
            <div class="empty-history">
                No flashcards yet.
            </div>
        `;

        return;

    }

    flashcardSets.forEach(set => {

        const item =
            document.createElement("div");

        item.className = "history-item";

        if(
            currentSet &&
            currentSet._id === set.id
        ){
            item.classList.add("active");
        }

        item.innerHTML = `
            <div class="history-info">
                <div class="history-title">
                    📚 ${set.title}
                </div>

                <div class="history-subtitle">
                    ${set.card_count} cards
                </div>
            </div>

            <button
                class="history-delete"
            >
                🗑
            </button>
        `;

        item.addEventListener(
            "click",
            () => loadFlashcardSet(set.id)
        );

        item.querySelector(".history-delete")
            .addEventListener(
                "click",
                event => {

                    event.stopPropagation();

                    deleteFlashcardSet(set.id);

                }
            );

        container.appendChild(item);

    });

}

async function loadFlashcardSet(setId){

    const response =
        await fetch(`/flashcards/set/${setId}`);

    currentSet =
        await response.json();

    currentIndex = 0;

    showingAnswer = false;

    renderHistory();

    renderCard();

}

function renderCard(){

    if(
        !currentSet ||
        !currentSet.cards.length
    ){

        showEmptyState();

        return;

    }

    const card =
        currentSet.cards[currentIndex];

    document.getElementById(
        "flashcards-title"
    ).textContent =
        currentSet.title;

    document.getElementById(
        "flashcard-front"
    ).textContent =
        showingAnswer
            ? card.back
            : card.front;

    document.getElementById(
        "show-answer-btn"
    ).textContent =
        showingAnswer
            ? "Show Question"
            : "Show Answer";

    document.getElementById(
        "progress-text"
    ).textContent =
        `${currentIndex + 1} / ${currentSet.cards.length}`;

    document.getElementById(
        "progress-fill"
    ).style.width =
        `${((currentIndex + 1) / currentSet.cards.length) * 100}%`;

}

function toggleAnswer(){

    if(!currentSet){
        return;
    }

    showingAnswer = !showingAnswer;

    renderCard();

}

function nextCard(){

    if(
        !currentSet ||
        currentIndex >= currentSet.cards.length - 1
    ){
        return;
    }

    currentIndex++;

    showingAnswer = false;

    renderCard();

}

function previousCard(){

    if(
        !currentSet ||
        currentIndex <= 0
    ){
        return;
    }

    currentIndex--;

    showingAnswer = false;

    renderCard();

}

async function deleteFlashcardSet(setId){

    const confirmed =
        confirm(
            "Delete this flashcard set?"
        );

    if(!confirmed){
        return;
    }

    await fetch(
        `/flashcards/delete/${setId}`,
        {
            method:"DELETE"
        }
    );

    currentSet = null;

    currentIndex = 0;

    showingAnswer = false;

    loadFlashcardHistory();

}

function showEmptyState(){

    document.getElementById(
        "flashcards-title"
    ).textContent =
        "Flashcards";

    document.getElementById(
        "flashcard-front"
    ).textContent =
        "Generate flashcards from the Study Assistant to begin.";

    document.getElementById(
        "progress-text"
    ).textContent =
        "0 / 0";

    document.getElementById(
        "progress-fill"
    ).style.width =
        "0%";

}