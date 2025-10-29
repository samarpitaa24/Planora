document.addEventListener("DOMContentLoaded", async () => {
  const container = document.getElementById("dashboard-task-list");
  container.innerHTML = "<div class='task-row'><em>Loading tasks...</em></div>";

  try {
    const response = await fetch("/tasks/api/top");
    const data = await response.json();

    if (!data.success || !data.tasks.length) {
      container.innerHTML = "<div class='task-row'><em>No upcoming tasks.</em></div>";
      return;
    }

    container.innerHTML = "";
    data.tasks.forEach((task) => {
      const deadline = task.deadline
        ? new Date(task.deadline).toLocaleDateString("en-GB", {
            day: "2-digit",
            month: "short",
            year: "numeric",
          })
        : "No deadline";

      const row = document.createElement("div");
      row.className = "task-row";
      row.setAttribute("role", "listitem");
      row.innerHTML = `
        <div class="task-dot" aria-hidden="true"></div>
        <div class="task-meta">
          <strong class="task-name">${task.name}</strong>
          <span class="task-deadline">Due: ${deadline}</span>
        </div>
      `;
      container.appendChild(row);
    });
  } catch (err) {
    console.error("Failed to load top tasks:", err);
    container.innerHTML = "<div class='task-row'><em>Error loading tasks.</em></div>";
  }
});
