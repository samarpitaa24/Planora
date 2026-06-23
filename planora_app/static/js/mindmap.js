let mindmaps = [];

let currentMindmap = null;

document.addEventListener(
  "DOMContentLoaded",

  () => {
    mermaid.initialize({
      startOnLoad: false,
    });

    const backButton = document.getElementById("back-to-chat");

    if (backButton && CONVERSATION_ID) {
      backButton.href = `/chatbot/?conversation=${CONVERSATION_ID}`;
    }

    loadMindmapHistory();
  },
);

async function loadMindmapHistory() {
  const response = await fetch("/mindmap/history");

  mindmaps = await response.json();

  renderHistory();

  if (!mindmaps.length) {
    showEmptyState();

    return;
  }

  let mapId = SELECTED_MAP;

  if (!mapId) {
    mapId = mindmaps[0].id;
  }

  loadMindmap(mapId);
}

function renderHistory() {
  const container = document.getElementById("mindmap-history");

  container.innerHTML = "";

  if (!mindmaps.length) {
    container.innerHTML = `

        <div class="empty-history">

            No mindmaps yet.

        </div>

        `;

    return;
  }

  mindmaps.forEach((map) => {
    const item = document.createElement("div");

    item.className = "mindmap-history-item";

    if (currentMindmap && currentMindmap._id === map.id) {
      item.classList.add("active");
    }

    item.innerHTML = `

            <div>

                <div>

                    🧠 ${map.title}

                </div>

                <div
                    style="font-size:13px;color:var(--muted);margin-top:4px;"
                >

                    Mindmap

                </div>

            </div>

            <span
                class="delete-mindmap"
            >

                🗑

            </span>

            `;

    item.addEventListener(
      "click",

      () => loadMindmap(map.id),
    );

    item

      .querySelector(".delete-mindmap")

      .addEventListener(
        "click",

        (event) => {
          event.stopPropagation();

          deleteMindmap(map.id);
        },
      );

    container.appendChild(item);
  });
}

async function loadMindmap(mapId) {
  const response = await fetch(`/mindmap/map/${mapId}`);

  currentMindmap = await response.json();

  renderHistory();

  renderMindmap();
}

async function renderMindmap() {

  if (!currentMindmap) {
    showEmptyState();
    return;
  }

  document.getElementById("mindmap-title").textContent =
    currentMindmap.title;

  const oldContainer =
    document.getElementById("mindmap-render");

  const newContainer =
    oldContainer.cloneNode(false);

  newContainer.removeAttribute("data-processed");

  newContainer.className = "mermaid";

  newContainer.textContent =
    currentMindmap.mindmap;

  oldContainer.parentNode.replaceChild(
    newContainer,
    oldContainer
  );

  await mermaid.run({
    nodes: [newContainer],
  });

}

async function deleteMindmap(mapId) {
  const confirmed = confirm("Delete this mindmap?");

  if (!confirmed) {
    return;
  }

  await fetch(
    `/mindmap/delete/${mapId}`,

    {
      method: "DELETE",
    },
  );

  currentMindmap = null;

  loadMindmapHistory();
}

function showEmptyState() {
  document.getElementById("mindmap-title").textContent = "Mindmap";

  document.getElementById("mindmap-render").innerHTML = `

        <div
            style="color:var(--muted);font-size:18px;"
        >

            Generate a mindmap from the Study Assistant to begin.

        </div>

        `;
}
