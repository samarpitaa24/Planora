let currentConversationId = null;

document.addEventListener("DOMContentLoaded", () => {

    loadConversations();

    document
        .getElementById("new-chat-btn")
        .addEventListener(
            "click",
            createConversation
        );

    document
        .querySelector(
            ".chat-input-area button"
        )
        .addEventListener(
            "click",
            sendMessage
        );

    document
        .querySelector(
            ".chat-input-area textarea"
        )
        .addEventListener(
            "keydown",
            (e) => {

                if (
                    e.key === "Enter" &&
                    !e.shiftKey
                ) {

                    e.preventDefault();

                    sendMessage();

                }

            }
        );

        document
            .getElementById("upload-pdf-btn")
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
});

async function loadConversations() {

    const historyContainer =
        document.getElementById(
            "chat-history"
        );

    try {

        const response =
            await fetch(
                "/chatbot/conversations"
            );

        const conversations =
            await response.json();

        historyContainer.innerHTML = "";

        conversations.forEach(
            conversation => {

            const item = document.createElement("div");

            item.className =
                "chat-history-item";

            item.dataset.id =
                conversation.id;

            const title =
                document.createElement("span");

            title.textContent =
                conversation.title;

            const actions =
                document.createElement("div");

            actions.className =
                "chat-actions";

            const pinBtn =
                document.createElement("span");

            pinBtn.textContent =
                conversation.is_pinned
                ? "📌"
                : "📍";

            pinBtn.className =
                "chat-pin-btn";

            pinBtn.addEventListener(
                "click",
                async (e) => {

                    e.stopPropagation();

                    await fetch(
                        `/chatbot/pin/${conversation.id}`,
                        {
                            method: "POST"
                        }
                    );

                    loadConversations();

                }
            );

            const deleteBtn =
                document.createElement("span");

            deleteBtn.textContent =
                "🗑";

            deleteBtn.className =
                "chat-delete-btn";

            deleteBtn.addEventListener(
                "click",
                async (e) => {

                    e.stopPropagation();

                    if (
                        !confirm(
                            "Delete this chat?"
                        )
                    ) {
                        return;
                    }

                    await fetch(
                        `/chatbot/delete/${conversation.id}`,
                        {
                            method: "DELETE"
                        }
                    );

                    loadConversations();

                }
            );

            actions.appendChild(pinBtn);
            actions.appendChild(deleteBtn);

            item.appendChild(title);
            item.appendChild(actions);

            item.addEventListener(
                "click",
                () => {

                    currentConversationId =
                        conversation.id;

                    loadConversation(
                        conversation.id
                    );

                }
            );

            historyContainer.appendChild(item);
            }
        );

    } catch(error) {

        console.error(error);

    }

}

async function loadConversation(
    conversationId
) {

    try {

        const response =
            await fetch(
                `/chatbot/conversation/${conversationId}`
            );

        const messages =
            await response.json();

        const container =
            document.querySelector(
                ".chat-messages"
            );

        container.innerHTML = "";

        if (
            messages.length === 0
        ) {

            container.innerHTML =
                `
                <div class="assistant-message">
                    Start a new conversation 👋
                </div>
                `;

            return;

        }

        messages.forEach(msg => {

            const div =
                document.createElement(
                    "div"
                );

            div.className =
                msg.sender === "user"
                ? "user-message"
                : "assistant-message";

            if (
                msg.sender === "assistant"
            ) {

                div.innerHTML =
                    marked.parse(
                        msg.message
                    );

            } else {

                div.textContent =
                    msg.message;

            }

            container.appendChild(
                div
            );

        });

        container.scrollTop =
            container.scrollHeight;

    } catch(error) {

        console.error(error);

    }

}

async function createConversation() {
    console.log("NEW CHAT CLICKED");
    try {

        const response =
            await fetch(
                "/chatbot/new",
                {
                    method: "POST"
                }
            );

        const data =
            await response.json();

        currentConversationId =
            data.conversation_id;

        await loadConversations();

        await loadConversation(
            currentConversationId
        );

    } catch(error) {

        console.error(error);

    }

}

async function sendMessage() {

    if (!currentConversationId) {

        alert(
            "Please create or select a chat first."
        );

        return;

    }

    const textarea =
        document.querySelector(
            ".chat-input-area textarea"
        );

    const message =
        textarea.value.trim();

    if (!message) {
        return;
    }

    textarea.value = "";

    const container =
        document.querySelector(
            ".chat-messages"
        );

    const userDiv =
        document.createElement(
            "div"
        );

    userDiv.className =
        "user-message";

    userDiv.textContent =
        message;

    container.appendChild(
        userDiv
    );

    const loadingDiv =
        document.createElement(
            "div"
        );

    loadingDiv.className =
        "assistant-message";

    loadingDiv.textContent =
        "Thinking...";

    container.appendChild(
        loadingDiv
    );

    container.scrollTop =
        container.scrollHeight;

    try {

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

        await response.json();

        await loadConversations();

        await loadConversation(
            currentConversationId
        );

    } catch(error) {

        console.error(error);

        loadingDiv.textContent =
            "Something went wrong.";

    }

}