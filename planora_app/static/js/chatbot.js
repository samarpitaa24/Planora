/* ==========================================================
                        GLOBAL STATE
========================================================== */

let currentConversationId = null;

let studySources = [];

let activeSourceId = null;

let selectedTool = null;


/* ==========================================================
                    DOM CONTENT LOADED
========================================================== */

document.addEventListener(

    "DOMContentLoaded",

    () => {

        initializeChatbot();

    }

);


/* ==========================================================
                    INITIALIZATION
========================================================== */

function initializeChatbot() {

    loadConversations();

    document
        .getElementById("new-chat-btn")
        .addEventListener(
            "click",
            createConversation
        );

    document
        .getElementById("send-btn")
        .addEventListener(
            "click",
            sendMessage
        );

    document
        .getElementById("chat-input")
        .addEventListener(

            "keydown",

            handleTextareaKeydown

        );

    document
        .getElementById("chat-input")
        .addEventListener(

            "input",

            autoResizeTextarea

        );

}


/* ==========================================================
                    CREATE NEW CHAT
========================================================== */

async function createConversation() {

    try {

        const response = await fetch(

            "/chatbot/new",

            {

                method: "POST"

            }

        );

        const data = await response.json();

        currentConversationId =

            data.conversation_id;

        studySources = [];

        activeSourceId = null;

        await loadConversations();

        await loadConversation(

            currentConversationId

        );

    }

    catch (error) {

        console.error(error);

    }

}


/* ==========================================================
                LOAD ALL CONVERSATIONS
========================================================== */

async function loadConversations() {

    const historyContainer =

        document.getElementById(

            "chat-history"

        );

    try {

        const response = await fetch(

            "/chatbot/conversations"

        );

        const conversations =

            await response.json();

        historyContainer.innerHTML = "";

        conversations.forEach(

            conversation => {

                const item =

                    document.createElement(

                        "div"

                    );

                item.className =

                    "chat-history-item";

                if (

                    conversation.id ===

                    currentConversationId

                ) {

                    item.classList.add(

                        "active"

                    );

                }

                item.dataset.id =

                    conversation.id;

                /* ---------- Title ---------- */

                const title =

                    document.createElement(

                        "span"

                    );

                title.textContent =

                    conversation.title;

                title.style.flex = "1";

                /* ---------- Actions ---------- */

                const actions =

                    document.createElement(

                        "div"

                    );

                actions.style.display =

                    "flex";

                actions.style.gap =

                    "8px";

                /* ---------- Pin ---------- */

                const pinBtn =

                    document.createElement(

                        "span"

                    );

                pinBtn.className =

                    "chat-pin-btn";

                pinBtn.textContent =

                    conversation.is_pinned

                    ?

                    "📌"

                    :

                    "📍";

                pinBtn.addEventListener(

                    "click",

                    async (event) => {

                        event.stopPropagation();

                        await fetch(

                            `/chatbot/pin/${conversation.id}`,

                            {

                                method: "POST"

                            }

                        );

                        loadConversations();

                    }

                );

                /* ---------- Delete ---------- */

                const deleteBtn =

                    document.createElement(

                        "span"

                    );

                deleteBtn.className =

                    "chat-delete-btn";

                deleteBtn.textContent =

                    "🗑";

                deleteBtn.addEventListener(

                    "click",

                    async (event) => {

                        event.stopPropagation();

                        const confirmDelete =

                            confirm(

                                "Delete this conversation?"

                            );

                        if (

                            !confirmDelete

                        ) {

                            return;

                        }

                        await fetch(

                            `/chatbot/delete/${conversation.id}`,

                            {

                                method: "DELETE"

                            }

                        );

                        if (

                            currentConversationId ===

                            conversation.id

                        ) {

                            currentConversationId =

                                null;

                        }

                        loadConversations();

                        clearChatWindow();

                    }

                );

                actions.appendChild(

                    pinBtn

                );

                actions.appendChild(

                    deleteBtn

                );

                item.appendChild(

                    title

                );

                item.appendChild(

                    actions

                );

                item.addEventListener(

                    "click",

                    () => {

                        currentConversationId =

                            conversation.id;

                        loadConversations();

                        loadConversation(

                            conversation.id

                        );

                    }

                );

                historyContainer.appendChild(

                    item

                );

            }

        );

    }

    catch (error) {

        console.error(error);

    }

}


/* ==========================================================
                LOAD SINGLE CONVERSATION
========================================================== */

async function loadConversation(

    conversationId

) {

    try {

        const response = await fetch(

            `/chatbot/conversation/${conversationId}`

        );

        const messages =

            await response.json();

        const container =

            document.getElementById(

                "chat-messages"

            );

        container.innerHTML = "";

        if (

            messages.length === 0

        ) {

            container.innerHTML =

            `

            <div class="assistant-message">

                👋 Start a new study conversation.

            </div>

            `;

            return;

        }

        messages.forEach(

            message => {

                const div =

                    document.createElement(

                        "div"

                    );

                div.className =

                    message.sender ===

                    "user"

                    ?

                    "user-message"

                    :

                    "assistant-message";

                if (

                    message.sender ===

                    "assistant"

                ) {

                    div.innerHTML =

                        marked.parse(

                            message.message

                        );

                }

                else {

                    div.textContent =

                        message.message;

                }

                container.appendChild(

                    div

                );

            }

        );

        scrollChatToBottom();

    }

    catch (error) {

        console.error(error);

    }

}

// PART 2 

/* ==========================================================
                    STUDY SOURCES
========================================================== */

const MAX_STUDY_SOURCES = 2;


/* ==========================================================
                    REGISTER EVENTS
========================================================== */

document.addEventListener(

    "DOMContentLoaded",

    () => {

        document

            .getElementById(

                "add-pdf-btn"

            )

            .addEventListener(

                "click",

                () => {

                    document

                        .getElementById(

                            "pdf-upload"

                        )

                        .click();

                }

            );

        document

            .getElementById(

                "pdf-upload"

            )

            .addEventListener(

                "change",

                handlePdfSelection

            );

    }

);


/* ==========================================================
                HANDLE PDF SELECTION
========================================================== */

function handlePdfSelection(event) {

    const file =

        event.target.files[0];

    if (!file) {

        return;

    }

    if (

        studySources.length >=

        MAX_STUDY_SOURCES

    ) {

        alert(

            "Maximum 2 study sources allowed."

        );

        event.target.value = "";

        return;

    }

    const duplicate =

        studySources.some(

            source =>

            source.name ===

            file.name

        );

    if (duplicate) {

        alert(

            "This PDF is already attached."

        );

        event.target.value = "";

        return;

    }

    const source = {

        id:

            crypto.randomUUID(),

        name:

            file.name,

        file:

            file,

        uploaded:

            false,

        documentId:

            null

    };

    studySources.push(

        source

    );

    activeSourceId =

        source.id;

    renderStudySources();

    event.target.value = "";

}


/* ==========================================================
                RENDER STUDY SOURCES
========================================================== */

function renderStudySources() {

    const container =

        document.getElementById(

            "study-source-list"

        );

    container.innerHTML = "";

    if (

        studySources.length === 0

    ) {

        container.innerHTML =

        `

        <div

            style="color:#777;font-size:14px;"

        >

            No study sources added yet.

        </div>

        `;

        return;

    }

    studySources.forEach(

        source => {

            const card =

                document.createElement(

                    "div"

                );

            card.className =

                "study-source";

            if (

                source.id ===

                activeSourceId

            ) {

                card.classList.add(

                    "active"

                );

            }

            card.innerHTML =

            `

            <span>

                📄

            </span>

            <span

                class="study-source-name"

            >

                ${source.name}

            </span>

            <span

                class="remove-source"

            >

                ✕

            </span>

            `;

            card.addEventListener(

                "click",

                () => {

                    setActiveStudySource(

                        source.id

                    );

                }

            );

            const removeButton =

                card.querySelector(

                    ".remove-source"

                );

            removeButton.addEventListener(

                "click",

                (event) => {

                    event.stopPropagation();

                    removeStudySource(

                        source.id

                    );

                }

            );

            container.appendChild(

                card

            );

        }

    );

}


/* ==========================================================
                SET ACTIVE SOURCE
========================================================== */

function setActiveStudySource(

    sourceId

) {

    activeSourceId =

        sourceId;

    renderStudySources();

}


/* ==========================================================
                REMOVE SOURCE
========================================================== */

function removeStudySource(

    sourceId

) {

    studySources =

        studySources.filter(

            source =>

            source.id !==

            sourceId

        );

    if (

        activeSourceId ===

        sourceId

    ) {

        if (

            studySources.length

        ) {

            activeSourceId =

                studySources[

                    studySources.length - 1

                ].id;

        }

        else {

            activeSourceId =

                null;

        }

    }

    renderStudySources();

}


/* ==========================================================
                GET ACTIVE SOURCE
========================================================== */

function getActiveStudySource() {

    return studySources.find(

        source =>

        source.id ===

        activeSourceId

    );

}

// PART 3

/* ==========================================================
                    TEXTAREA
========================================================== */

function autoResizeTextarea() {

    const textarea =
        document.getElementById(
            "chat-input"
        );

    textarea.style.height =
        "auto";

    textarea.style.height =
        textarea.scrollHeight + "px";

}


function handleTextareaKeydown(event) {

    if (

        event.key === "Enter"

        &&

        !event.shiftKey

    ) {

        event.preventDefault();

        sendMessage();

    }

}


/* ==========================================================
                    SEND MESSAGE
========================================================== */

async function sendMessage() {

    if (!currentConversationId) {

        alert(
            "Please create or select a chat first."
        );

        return;

    }

    const textarea =
        document.getElementById(
            "chat-input"
        );

    const message =
        textarea.value.trim();

    if (!message) {

        return;

    }

    textarea.value = "";

    autoResizeTextarea();

    appendUserMessage(
        message
    );

    const loadingElement =
        appendLoadingMessage();

    scrollChatToBottom();

    try {

        /*
        ---------------------------------------

        Future Flow

        Upload pending PDFs

        Generate flashcards

        Generate quiz

        Generate mindmap

        ---------------------------------------
        */

        const response =
            await fetch(

                "/chatbot/send",

                {

                    method: "POST",

                    headers: {

                        "Content-Type":

                        "application/json"

                    },

                    body: JSON.stringify({

                        conversation_id:

                        currentConversationId,

                        message:

                        message

                    })

                }

            );

        const data =
            await response.json();

        loadingElement.remove();

        appendAssistantMessage(

            data.reply

        );

        await loadConversations();

        scrollChatToBottom();

    }

    catch (error) {

        console.error(error);

        loadingElement.innerHTML =

            "Something went wrong.";

    }

}


/* ==========================================================
                USER MESSAGE
========================================================== */

function appendUserMessage(message) {

    const container =
        document.getElementById(
            "chat-messages"
        );

    const div =
        document.createElement(
            "div"
        );

    div.className =
        "user-message";

    div.textContent =
        message;

    container.appendChild(
        div
    );

}


/* ==========================================================
                ASSISTANT MESSAGE
========================================================== */

function appendAssistantMessage(message) {

    const container =
        document.getElementById(
            "chat-messages"
        );

    const div =
        document.createElement(
            "div"
        );

    div.className =
        "assistant-message";

    div.innerHTML =
        marked.parse(
            message
        );

    container.appendChild(
        div
    );

}


/* ==========================================================
                THINKING MESSAGE
========================================================== */

function appendLoadingMessage() {

    const container =
        document.getElementById(
            "chat-messages"
        );

    const div =
        document.createElement(
            "div"
        );

    div.className =
        "assistant-message";

    div.innerHTML =

        `
        <strong>

            Thinking...

        </strong>
        `;

    container.appendChild(
        div
    );

    return div;

}


/* ==========================================================
                CHAT HELPERS
========================================================== */

function scrollChatToBottom() {

    const container =
        document.getElementById(
            "chat-messages"
        );

    container.scrollTop =
        container.scrollHeight;

}


function clearChatWindow() {

    const container =
        document.getElementById(
            "chat-messages"
        );

    container.innerHTML =

        `
        <div class="assistant-message">

            👋 Start a new study conversation.

        </div>
        `;

}

// PART 4

/* ==========================================================
                    TOOL MODAL STATE
========================================================== */

let currentTool = null;

let selectedToolSourceId = null;


/* ==========================================================
                    REGISTER TOOL EVENTS
========================================================== */

document.addEventListener(

    "DOMContentLoaded",

    () => {

        document

            .getElementById(

                "flashcards-btn"

            )

            .addEventListener(

                "click",

                () => {

                    openToolModal(

                        "flashcards"

                    );

                }

            );

        document

            .getElementById(

                "quiz-btn"

            )

            .addEventListener(

                "click",

                () => {

                    openToolModal(

                        "quiz"

                    );

                }

            );

        document

            .getElementById(

                "mindmap-btn"

            )

            .addEventListener(

                "click",

                () => {

                    openToolModal(

                        "mindmap"

                    );

                }

            );

        document

            .getElementById(

                "flashcards-cancel"

            )

            .addEventListener(

                "click",

                () => {

                    closeToolModal(

                        "flashcards"

                    );

                }

            );

        document

            .getElementById(

                "quiz-cancel"

            )

            .addEventListener(

                "click",

                () => {

                    closeToolModal(

                        "quiz"

                    );

                }

            );

        document

            .getElementById(

                "mindmap-cancel"

            )

            .addEventListener(

                "click",

                () => {

                    closeToolModal(

                        "mindmap"

                    );

                }

            );

        document

            .getElementById(

                "flashcards-generate"

            )

            .addEventListener(

                "click",

                generateFlashcards

            );

        document

            .getElementById(

                "quiz-generate"

            )

            .addEventListener(

                "click",

                generateQuiz

            );

        document

            .getElementById(

                "mindmap-generate"

            )

            .addEventListener(

                "click",

                generateMindmap

            );

    }

);


/* ==========================================================
                    OPEN MODAL
========================================================== */

function openToolModal(tool) {

    currentTool = tool;

    selectedToolSourceId =

        activeSourceId;

    const modal =

        document.getElementById(

            `${tool}-modal`

        );

    modal.classList.remove(

        "hidden"

    );

    renderToolSourceList(

        tool

    );

}


/* ==========================================================
                    CLOSE MODAL
========================================================== */

function closeToolModal(tool) {

    document

        .getElementById(

            `${tool}-modal`

        )

        .classList.add(

            "hidden"

        );

}


/* ==========================================================
                RENDER SOURCE LIST
========================================================== */

function renderToolSourceList(tool) {

    const container =

        document.getElementById(

            `${tool}-source-list`

        );

    container.innerHTML = "";

    studySources.forEach(

        source => {

            const item =

                document.createElement(

                    "div"

                );

            item.className =

                "tool-source-item";

            if (

                source.id ===

                selectedToolSourceId

            ) {

                item.classList.add(

                    "active"

                );

            }

            item.innerHTML =

            `

            📄 ${source.name}

            `;

            item.addEventListener(

                "click",

                () => {

                    selectedToolSourceId =

                        source.id;

                    renderToolSourceList(

                        tool

                    );

                }

            );

            container.appendChild(

                item

            );

        }

    );

}


/* ==========================================================
                FLASHCARDS
========================================================== */

async function generateFlashcards() {

    closeToolModal(

        "flashcards"

    );

    appendAssistantMessage(

`🧠 Flashcards generation started.

Your flashcards will be prepared from the selected study source.

(Open Flashcards UI will appear here after backend integration.)`

    );

}


/* ==========================================================
                QUIZ
========================================================== */

async function generateQuiz() {

    const count =

        document.getElementById(

            "quiz-count"

        ).value;

    closeToolModal(

        "quiz"

    );

    appendAssistantMessage(

`📝 Quiz generation started.

Questions : ${count}

(Quiz page will open after backend integration.)`

    );

}


/* ==========================================================
                MINDMAP
========================================================== */

async function generateMindmap() {

    closeToolModal(

        "mindmap"

    );

    appendAssistantMessage(

`🧠 Mindmap generation started.

(Mindmap viewer will open after backend integration.)`

    );

}

// PART 5

/* ==========================================================
                    TOOL CARDS
========================================================== */

function appendToolCard(tool, title, description, id = null) {

    const container =
        document.getElementById(
            "chat-messages"
        );

    const wrapper =
        document.createElement(
            "div"
        );

    wrapper.className =
        "assistant-message";

    let icon = "📄";

    if (tool === "flashcards") {

        icon = "📚";

    }

    else if (tool === "quiz") {

        icon = "📝";

    }

    else if (tool === "mindmap") {

        icon = "🧠";

    }

    wrapper.innerHTML = `

        <div class="generated-tool-card">

            <div class="generated-tool-icon">

                ${icon}

            </div>

            <div class="generated-tool-content">

                <div class="generated-tool-title">

                    ${title}

                </div>

                <div class="generated-tool-description">

                    ${description}

                </div>

            </div>

            <button

                class="generated-tool-button"

            >

                Open

            </button>

        </div>

    `;

    wrapper
        .querySelector(
            ".generated-tool-button"
        )
        .addEventListener(

            "click",

            () => {

                if (

                    tool === "flashcards"

                ) {

                    window.location.href =
                        "/flashcards";

                }

                else if (

                    tool === "quiz"

                ) {

                    window.location.href =
                        "/quiz";

                }

                else if (

                    tool === "mindmap"

                ) {

                    window.location.href =
                        "/mindmap";

                }

            }

        );

    container.appendChild(

        wrapper

    );

    scrollChatToBottom();

}


/* ==========================================================
                    FUTURE PDF UPLOAD
========================================================== */

async function uploadPendingSources() {

    for (

        const source

        of

        studySources

    ) {

        if (

            source.uploaded

        ) {

            continue;

        }

        /*
        -------------------------------------------------

        Future Backend

        FormData

        PDF

        conversation_id

        POST /chatbot/upload-pdf

        document_id

        uploaded = true

        -------------------------------------------------
        */

    }

}


/* ==========================================================
                    LOADING STATE
========================================================== */

function disableChat() {

    document

        .getElementById(

            "send-btn"

        )

        .disabled = true;

    document

        .getElementById(

            "chat-input"

        )

        .disabled = true;

}


function enableChat() {

    document

        .getElementById(

            "send-btn"

        )

        .disabled = false;

    document

        .getElementById(

            "chat-input"

        )

        .disabled = false;

}


/* ==========================================================
                    RESET CHAT STATE
========================================================== */

function resetStudySources() {

    studySources = [];

    activeSourceId = null;

    renderStudySources();

}


/* ==========================================================
                    LOADING HELPERS
========================================================== */

function showThinking() {

    return appendLoadingMessage();

}


function hideThinking(element) {

    if (

        element

    ) {

        element.remove();

    }

}


/* ==========================================================
                    EMPTY CHAT
========================================================== */

function emptyConversation() {

    const container =

        document.getElementById(

            "chat-messages"

        );

    container.innerHTML =

    `

    <div class="assistant-message">

        👋

        Start learning by

        uploading a study source

        or asking a question.

    </div>

    `;

}


/* ==========================================================
                    FUTURE WORKFLOW

Conversation

↓

Study Sources

↓

Active PDF

↓

Ask Question

↓

Upload Pending PDFs

↓

Backend

↓

Gemini

↓

Reply

↓

Chat


Flashcards

↓

Choose Source

↓

Backend

↓

flashcards collection

↓

Assistant Card

↓

Open Flashcards


Quiz

↓

Choose Source

↓

Backend

↓

quiz collection

↓

Assistant Card

↓

Open Quiz


Mindmap

↓

Choose Source

↓

Backend

↓

mindmap collection

↓

Assistant Card

↓

Open Mindmap

========================================================== */