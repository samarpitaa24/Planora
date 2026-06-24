/* ==========================================================
                        GLOBAL STATE
========================================================== */

let currentConversationId = null;

let studySources = [];

let activeSourceId = null;

/* ==========================================================
                    DOM CONTENT LOADED
========================================================== */

document.addEventListener(
  "DOMContentLoaded",

  () => {
    initializeChatbot();
  },
);

/* ==========================================================
                    INITIALIZATION
========================================================== */

function initializeChatbot() {
  const params = new URLSearchParams(window.location.search);

  const conversationId = params.get("conversation");

  loadConversations().then(() => {
    if (conversationId && conversationId !== "null" && conversationId !== "None") {
      currentConversationId = conversationId;

      loadConversation(conversationId);
    }
  });

  document
    .getElementById("new-chat-btn")
    .addEventListener("click", createConversation);

  document.getElementById("send-btn").addEventListener("click", sendMessage);

  document.getElementById("chat-input").addEventListener(
    "keydown",

    handleTextareaKeydown,
  );

  document.getElementById("chat-input").addEventListener(
    "input",

    autoResizeTextarea,
  );
}

/* ==========================================================
                    CREATE NEW CHAT
========================================================== */
async function createConversation() {
  currentConversationId = null;

  studySources = [];

  activeSourceId = null;

  renderStudySources();

  const container = document.getElementById("chat-messages");

  container.innerHTML = `
    <div class="assistant-message">
      👋 Start a new study conversation.
    </div>
  `;

  window.history.replaceState({}, "", "/chatbot");
}
/* ==========================================================
                ENSURE CONVERSATION
========================================================== */

async function ensureConversation() {
  if (currentConversationId && currentConversationId !== "null" && currentConversationId !== "None") {
    return currentConversationId;
  }

  try {
    const response = await fetch("/chatbot/new", {
      method: "POST",
    });

    const data = await response.json();

    currentConversationId = data.conversation_id;
    window.history.replaceState(
      {},
      "",
      `/chatbot/?conversation=${currentConversationId}`,
    );

    await loadConversations();

    return currentConversationId;
  } catch (error) {
    console.error(error);

    throw error;
  }
}

/* ==========================================================
                LOAD ALL CONVERSATIONS
========================================================== */

async function loadConversations() {
  const historyContainer = document.getElementById("chat-history");

  try {
    const response = await fetch("/chatbot/conversations");

    const conversations = await response.json();

    historyContainer.innerHTML = "";

    conversations.forEach((conversation) => {
      const item = document.createElement("div");

      item.className = "chat-history-item";

      if (conversation.id === currentConversationId) {
        item.classList.add("active");
      }

      item.dataset.id = conversation.id;

      /* ---------- Title ---------- */

      const title = document.createElement("span");

      title.textContent = conversation.title;

      title.style.flex = "1";

      /* ---------- Actions ---------- */

      const actions = document.createElement("div");

      actions.style.display = "flex";

      actions.style.gap = "8px";

      /* ---------- Pin ---------- */

      const pinBtn = document.createElement("span");

      pinBtn.className = "chat-pin-btn";

      pinBtn.textContent = conversation.is_pinned ? "📌" : "📍";

      pinBtn.addEventListener(
        "click",

        async (event) => {
          event.stopPropagation();

          await fetch(
            `/chatbot/pin/${conversation.id}`,

            {
              method: "POST",
            },
          );

          loadConversations();
        },
      );

      /* ---------- Delete ---------- */

      const deleteBtn = document.createElement("span");

      deleteBtn.className = "chat-delete-btn";

      deleteBtn.textContent = "🗑";

      deleteBtn.addEventListener(
        "click",

        async (event) => {
          event.stopPropagation();

          const confirmDelete = confirm("Delete this conversation?");

          if (!confirmDelete) {
            return;
          }

          await fetch(
            `/chatbot/delete/${conversation.id}`,

            {
              method: "DELETE",
            },
          );

          if (currentConversationId === conversation.id) {
            currentConversationId = null;
            window.history.replaceState({}, "", "/chatbot");
          }

          await loadConversations();

          clearChatWindow();
        },
      );

      actions.appendChild(pinBtn);

      actions.appendChild(deleteBtn);

      item.appendChild(title);

      item.appendChild(actions);

      item.addEventListener(
        "click",

        () => {
          currentConversationId = conversation.id;
          window.history.replaceState(
            {},
            "",
            `/chatbot/?conversation=${conversation.id}`,
          );

          loadConversations();

          loadConversation(conversation.id);
        },
      );

      historyContainer.appendChild(item);
    });
  } catch (error) {
    console.error(error);
  }
}

/* ==========================================================
                LOAD SINGLE CONVERSATION
========================================================== */

async function loadConversation(conversationId) {
  currentConversationId = conversationId;
  try {
    const response = await fetch(`/chatbot/conversation/${conversationId}`);

    const messages = await response.json();

    const container = document.getElementById("chat-messages");

    container.innerHTML = "";
    studySources = [];

    activeSourceId = null;

    renderStudySources();

    if (messages.length === 0) {
      container.innerHTML = `

            <div class="assistant-message">

                👋 Start a new study conversation.

            </div>

            `;

      await loadStudySources(conversationId);

      return;
    }

    messages.forEach((message) => {
      if (message.message_type === "flashcards") {
        appendToolCard(
          "flashcards",
          message.tool_title,
          "Flashcards generated",
          message.tool_id,
        );
        return;
      }

      if (message.message_type === "mindmap") {
        appendToolCard(
          "mindmap",
          message.tool_title,
          "Mindmap generated",
          message.tool_id,
        );
        return;
      }

      const div = document.createElement("div");

      div.className =
        message.sender === "user" ? "user-message" : "assistant-message";

      if (message.sender === "assistant") {
        div.innerHTML = marked.parse(message.message);
      } else {
        div.textContent = message.message;
      }

      container.appendChild(div);
    });

    scrollChatToBottom();

    await loadStudySources(conversationId);
  } catch (error) {
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

      .getElementById("add-pdf-btn")

      .addEventListener(
        "click",

        () => {
          document

            .getElementById("pdf-upload")

            .click();
        },
      );

    document

      .getElementById("pdf-upload")

      .addEventListener(
        "change",

        handlePdfSelection,
      );
  },
);

/* ==========================================================
                HANDLE PDF SELECTION
========================================================== */

function handlePdfSelection(event) {
  const file = event.target.files[0];

  if (!file) {
    return;
  }

  if (studySources.length >= MAX_STUDY_SOURCES) {
    alert("Maximum 2 study sources allowed.");

    event.target.value = "";

    return;
  }

  const duplicate = studySources.some((source) => source.name === file.name);

  if (duplicate) {
    alert("This PDF is already attached.");

    event.target.value = "";

    return;
  }

  const source = {
    id: crypto.randomUUID(),

    name: file.name,

    file: file,

    uploaded: false,

    documentId: null,
  };

  studySources.push(source);

  activeSourceId = source.id;

  renderStudySources();

  event.target.value = "";
}

/* ==========================================================
                RENDER STUDY SOURCES
========================================================== */

function renderStudySources() {
  const container = document.getElementById("study-source-list");

  container.innerHTML = "";

  if (studySources.length === 0) {
    container.innerHTML = `

        <div

            style="color:#777;font-size:14px;"

        >

            No study sources added yet.

        </div>

        `;

    return;
  }

  studySources.forEach((source) => {
    const card = document.createElement("div");

    card.className = "study-source";

    if (source.id === activeSourceId) {
      card.classList.add("active");
    }

    card.innerHTML = `

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
        setActiveStudySource(source.id);
      },
    );

    const removeButton = card.querySelector(".remove-source");

    removeButton.addEventListener(
      "click",

      (event) => {
        event.stopPropagation();

        removeStudySource(source.id);
      },
    );

    container.appendChild(card);
  });
}

/* ==========================================================
                SET ACTIVE SOURCE
========================================================== */

function setActiveStudySource(sourceId) {
  activeSourceId = sourceId;

  renderStudySources();
}

/* ==========================================================
                REMOVE SOURCE
========================================================== */

function removeStudySource(sourceId) {
  studySources = studySources.filter((source) => source.id !== sourceId);

  if (activeSourceId === sourceId) {
    if (studySources.length) {
      activeSourceId = studySources[studySources.length - 1].id;
    } else {
      activeSourceId = null;
    }
  }

  renderStudySources();
}

/* ==========================================================
                GET ACTIVE SOURCE
========================================================== */

function getActiveStudySource() {
  return studySources.find((source) => source.id === activeSourceId);
}

async function loadStudySources(conversationId) {
  studySources = [];

  activeSourceId = null;

  renderStudySources();

  try {
    const response = await fetch(`/chatbot/documents/${conversationId}`);

    const documents = await response.json();

    studySources = documents.map((document) => ({
      id: document.id,

      name: document.original_filename,

      uploaded: true,

      documentId: document.id,

      file: null,

      isActive: document.is_active,
    }));

    const activeDocument = studySources.find((source) => source.isActive);

    if (activeDocument) {
      activeSourceId = activeDocument.id;
    }

    renderStudySources();
  } catch (error) {
    console.error(error);
  }
}
// PART 3

/* ==========================================================
                    TEXTAREA
========================================================== */

function autoResizeTextarea() {
  const textarea = document.getElementById("chat-input");

  textarea.style.height = "auto";

  textarea.style.height = textarea.scrollHeight + "px";
}

function handleTextareaKeydown(event) {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();

    sendMessage();
  }
}

/* ==========================================================
                    SEND MESSAGE
========================================================== */

async function sendMessage() {
  try {
    await ensureConversation();
  } catch (error) {
    alert("Unable to create a conversation.");

    return;
  }

  const textarea = document.getElementById("chat-input");

  const message = textarea.value.trim();

  if (!message) {
    return;
  }

  textarea.value = "";

  autoResizeTextarea();

  appendUserMessage(message);

  const loadingElement = appendLoadingMessage();

  scrollChatToBottom();

  try {
    const documentId = await uploadPendingSources();
    const response = await fetch(
      "/chatbot/send",

      {
        method: "POST",

        headers: {
          "Content-Type": "application/json",
        },

        body: JSON.stringify({
          conversation_id: currentConversationId,

          message: message,
        }),
      },
    );

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.content || data.error || "Request failed");
    }

    if (loadingElement) {
      loadingElement.remove();
    }

    if (data.type === "flashcards") {
      appendToolCard(
        "flashcards",

        data.content.title,

        `${data.content.card_count} flashcards generated`,

        data.content.id,
      );
    } else {
      appendAssistantMessage(data.content || data.reply);
    }

    await loadConversations();

    scrollChatToBottom();
  } catch (error) {
    console.error(error);

    loadingElement.innerHTML =
      "⚠️ Unable to generate a response right now.<br>Please try again.";
  }
}

/* ==========================================================
                USER MESSAGE
========================================================== */

function appendUserMessage(message) {
  const container = document.getElementById("chat-messages");

  const div = document.createElement("div");

  div.className = "user-message";

  div.textContent = message;

  container.appendChild(div);
}

/* ==========================================================
                ASSISTANT MESSAGE
========================================================== */

function appendAssistantMessage(message) {
  const container = document.getElementById("chat-messages");

  const div = document.createElement("div");

  div.className = "assistant-message";

  if (message.includes("<")) {
    div.innerHTML = message;
  } else {
    div.innerHTML = marked.parse(message);
  }

  container.appendChild(div);

  return div;
}

/* ==========================================================
                THINKING MESSAGE
========================================================== */

function appendLoadingMessage() {
  const container = document.getElementById("chat-messages");

  const div = document.createElement("div");

  div.className = "assistant-message";

  div.innerHTML = `
        <strong>

            Thinking...

        </strong>
        `;

  container.appendChild(div);

  return div;
}

/* ==========================================================
                CHAT HELPERS
========================================================== */

function scrollChatToBottom() {
  const container = document.getElementById("chat-messages");

  container.scrollTop = container.scrollHeight;
}

function clearChatWindow() {
  const container = document.getElementById("chat-messages");

  container.innerHTML = `
        <div class="assistant-message">

            👋 Start a new study conversation.

        </div>
        `;
}

// PART 4

/* ==========================================================
                    TOOL MODAL STATE
========================================================== */

let selectedToolSourceId = null;

/* ==========================================================
                    REGISTER TOOL EVENTS
========================================================== */

document.addEventListener(
  "DOMContentLoaded",

  () => {
    document

      .getElementById("flashcards-btn")

      .addEventListener(
        "click",

        () => {
          openToolModal("flashcards");
        },
      );

    document

      .getElementById("mindmap-btn")

      .addEventListener(
        "click",

        () => {
          openToolModal("mindmap");
        },
      );

    document

      .getElementById("flashcards-cancel")

      .addEventListener(
        "click",

        () => {
          closeToolModal("flashcards");
        },
      );

    document

      .getElementById("mindmap-cancel")

      .addEventListener(
        "click",

        () => {
          closeToolModal("mindmap");
        },
      );

    document

      .getElementById("flashcards-history-btn")

      .addEventListener(
        "click",

        () => {
          closeToolModal("flashcards");

          window.location.href = `/flashcards?conversation=${currentConversationId}`;
        },
      );

    document

      .getElementById("mindmap-history-btn")

      .addEventListener(
        "click",

        () => {
          closeToolModal("mindmap");

          window.location.href = `/mindmap?conversation=${currentConversationId}`;
        },
      );

    document

      .getElementById("flashcards-generate")

      .addEventListener(
        "click",

        generateFlashcards,
      );

    document

      .getElementById("mindmap-generate")

      .addEventListener(
        "click",

        generateMindmap,
      );
  },
);
/* ==========================================================
                    OPEN MODAL
========================================================== */

function openToolModal(tool) {
  selectedToolSourceId = activeSourceId;

  const modal = document.getElementById(`${tool}-modal`);

  modal.classList.remove("hidden");

  renderToolSourceList(tool);
}

/* ==========================================================
                    CLOSE MODAL
========================================================== */

function closeToolModal(tool) {
  document

    .getElementById(`${tool}-modal`)

    .classList.add("hidden");
}

/* ==========================================================
                RENDER SOURCE LIST
========================================================== */

function renderToolSourceList(tool) {
  const container = document.getElementById(`${tool}-source-list`);

  container.innerHTML = "";

  studySources.forEach((source) => {
    const item = document.createElement("div");

    item.className = "tool-source-item";

    if (source.id === selectedToolSourceId) {
      item.classList.add("active");
    }

    item.innerHTML = `

            📄 ${source.name}

            `;

    item.addEventListener(
      "click",

      () => {
        selectedToolSourceId = source.id;

        renderToolSourceList(tool);
      },
    );

    container.appendChild(item);
  });
}

/* ==========================================================
                FLASHCARDS
========================================================== */

async function generateFlashcards() {
  closeToolModal("flashcards");
  try {
    await ensureConversation();
  } catch (error) {
    appendAssistantMessage("⚠️ Unable to create a conversation.");

    return;
  }
  const source = studySources.find((item) => item.id === selectedToolSourceId);

  if (!source) {
    appendAssistantMessage("Please select a study source.");

    return;
  }

  const loading = appendAssistantMessage(
    `
        <strong>📚 Creating flashcards...</strong>

        <br><br>

        ⏳ Reading study material...

        <br>

        🧠 Generating questions...
        `,
  );

  scrollChatToBottom();

  try {
    activeSourceId = source.id;

    const documentId = await uploadPendingSources();

    source.documentId = documentId;

    renderStudySources();

    const response = await fetch(
      "/flashcards/generate",

      {
        method: "POST",

        headers: {
          "Content-Type": "application/json",
        },

        body: JSON.stringify({
          conversation_id: currentConversationId,
          document_id: documentId,
          card_count: 10,
        }),
      },
    );

    const data = await response.json();

    loading.remove();

    if (!data.success) {
      appendAssistantMessage("⚠️ Unable to generate flashcards.");

      return;
    }

    appendToolCard(
      "flashcards",

      data.flashcard_set.title,

      `${data.flashcard_set.card_count} flashcards generated`,

      data.flashcard_set.id,
    );

    scrollChatToBottom();
  } catch (error) {
    console.error(error);

    loading.innerHTML = `
        <strong>⚠️ Flashcard generation failed</strong>

        <br><br>

        Please try again in a few moments.
        `;
  }
}

/* ==========================================================
                MINDMAP
========================================================== */

async function generateMindmap() {
  closeToolModal("mindmap");
  try {
    await ensureConversation();
  } catch (error) {
    appendAssistantMessage("⚠️ Unable to create a conversation.");

    return;
  }
  const source = studySources.find((item) => item.id === selectedToolSourceId);

  if (!source) {
    appendAssistantMessage("Please select a study source.");

    return;
  }

  const loading = appendAssistantMessage(
    `

        <strong>🧠 Creating mindmap...</strong>

        <br><br>

        ⏳ Reading study material...

        <br>

        🌳 Building concept hierarchy...

        `,
  );

  scrollChatToBottom();

  try {
    activeSourceId = source.id;
    const documentId = await uploadPendingSources();
    source.documentId = documentId;
    renderStudySources();

    const response = await fetch(
      "/mindmap/generate",

      {
        method: "POST",

        headers: {
          "Content-Type": "application/json",
        },

        body: JSON.stringify({
          conversation_id: currentConversationId,
          document_id: source.documentId,
        }),
      },
    );

    const data = await response.json();

    loading.remove();

    if (!data.success) {
      appendAssistantMessage("⚠️ Unable to generate mindmap.");
      return;
    }

    appendToolCard(
      "mindmap",
      data.mindmap.title,
      "Mindmap generated",
      data.mindmap.id,
    );

    scrollChatToBottom();
  } catch (error) {
    console.error(error);

    loading.innerHTML = `

        <strong>⚠️ Mindmap generation failed</strong>
        <br><br>
        Please try again in a few moments.
        `;
  }
}

// PART 5

/* ==========================================================
                    TOOL CARDS
========================================================== */

function appendToolCard(tool, title, description, id = null) {
  const container = document.getElementById("chat-messages");

  const wrapper = document.createElement("div");

  wrapper.className = "assistant-message";

  let icon = "📄";

  if (tool === "flashcards") {
    icon = "📚";
  } else if (tool === "mindmap") {
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

  wrapper.querySelector(".generated-tool-button").addEventListener(
    "click",

    () => {
      if (tool === "flashcards") {
        window.location.href = `/flashcards?set=${id}&conversation=${currentConversationId}`;
      } else if (tool === "mindmap") {
        window.location.href = `/mindmap?map=${id}&conversation=${currentConversationId}`;
      }
    },
  );

  container.appendChild(wrapper);

  scrollChatToBottom();
}

/* ==========================================================
                    FUTURE PDF UPLOAD
========================================================== */

async function uploadPendingSources() {
  const activeSource = getActiveStudySource();

  if (!activeSource) {
    return null;
  }

  if (activeSource.uploaded) {
    return activeSource.documentId;
  }

  const formData = new FormData();

  formData.append("file", activeSource.file);

  formData.append("conversation_id", currentConversationId);

  const response = await fetch(
    "/chatbot/upload-pdf",

    {
      method: "POST",
      body: formData,
    },
  );

  const data = await response.json();
  console.log(data);
  activeSource.uploaded = true;

  activeSource.documentId = data.document_id;

  return data.document_id;
}
