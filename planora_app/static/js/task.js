// planora_app/static/js/task.js
document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("task-form");
  const tasksList = document.getElementById("tasks-list");
  const cancelBtn = document.getElementById("cancel-edit-btn");
  const createBtn = document.getElementById("create-btn");

  let editingId = null;

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const payload = {
      name: document.getElementById("task-name").value.trim(),
      deadline: document.getElementById("task-deadline").value || null,
      priority: document.getElementById("task-priority").value,
      duration: document.getElementById("task-duration").value || null,
    };

    try {
      if (editingId) {
        const res = await fetch(`/tasks/api/${editingId}`, {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        });
        const data = await res.json();
        if (!data.success) throw new Error(data.error || "update failed");
      } else {
        const res = await fetch(`/tasks/api`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        });
        const data = await res.json();
        if (!data.success) throw new Error(data.error || "create failed");
      }
      resetForm();
      loadTasks();
    } catch (err) {
      alert(err.message);
      console.error(err);
    }
  });

  cancelBtn.addEventListener("click", (e) => {
    resetForm();
  });

  async function loadTasks() {
    tasksList.innerHTML = "<li>Loading...</li>";
    try {
      const res = await fetch("/tasks/api");
      const data = await res.json();
      if (!data.success) throw new Error(data.error || "could not load tasks");
      renderTasks(data.tasks || []);
    } catch (err) {
      tasksList.innerHTML = "<li>Error loading tasks</li>";
      console.error(err);
    }
  }

  function renderTasks(tasks) {
    tasksList.innerHTML = "";
    if (!tasks || tasks.length === 0) {
      tasksList.innerHTML = "<li class='no-tasks'>No tasks yet</li>";
      return;
    }

    tasks.forEach((task) => {
      const li = document.createElement("li");
      li.className = "task-item";

      // completed checkbox
      const checkbox = document.createElement("input");
      checkbox.type = "checkbox";
      checkbox.checked = !!task.completed;
      checkbox.addEventListener("change", () => toggleComplete(task._id, checkbox.checked));
      li.appendChild(checkbox);

      // title
      const title = document.createElement("span");
      title.className = "task-title";
      title.textContent = task.name;
      if (task.completed) title.style.textDecoration = "line-through";
      li.appendChild(title);

      // meta (deadline, priority, duration)
      const meta = document.createElement("div");
      meta.className = "task-meta";
      const parts = [];
      if (task.deadline) {
        const d = new Date(task.deadline);
        parts.push(d.toLocaleString());
      }
      if (task.priority) parts.push(task.priority);
      if (task.duration !== undefined && task.duration !== null) parts.push(`${task.duration}h`);
      meta.textContent = parts.join(" • ");
      li.appendChild(meta);

      // buttons
      const btns = document.createElement("div");
      btns.className = "task-buttons";

      const editBtn = document.createElement("button");
      editBtn.type = "button";
      editBtn.textContent = "Edit";
      editBtn.addEventListener("click", () => startEdit(task));
      btns.appendChild(editBtn);

      const delBtn = document.createElement("button");
      delBtn.type = "button";
      delBtn.textContent = "Delete";
      delBtn.addEventListener("click", () => deleteTask(task._id));
      btns.appendChild(delBtn);

      li.appendChild(btns);
      tasksList.appendChild(li);
    });
  }

  function startEdit(task) {
    editingId = task._id;
    document.getElementById("task-name").value = task.name || "";
    document.getElementById("task-deadline").value = task.deadline ? toDatetimeLocal(task.deadline) : "";
    document.getElementById("task-priority").value = task.priority || "Medium";
    document.getElementById("task-duration").value = task.duration || "";
    createBtn.textContent = "Save changes";
    cancelBtn.style.display = "inline-block";
  }

  function resetForm() {
    editingId = null;
    form.reset();
    createBtn.textContent = "Create task";
    cancelBtn.style.display = "none";
  }

  async function deleteTask(id) {
    if (!confirm("Are you sure you want to delete this task?")) return;
    try {
      const res = await fetch(`/tasks/api/${id}`, { method: "DELETE" });
      const data = await res.json();
      if (!data.success) throw new Error(data.error || "delete failed");
      loadTasks();
    } catch (err) {
      alert(err.message);
      console.error(err);
    }
  }

  async function toggleComplete(id, completed) {
    try {
      const res = await fetch(`/tasks/api/${id}/toggle`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ completed }),
      });
      const data = await res.json();
      if (!data.success) throw new Error(data.error || "toggle failed");
      loadTasks();
    } catch (err) {
      alert(err.message);
      console.error(err);
    }
  }

  // helper to convert ISO to input[type=datetime-local] compatible string
  function toDatetimeLocal(iso) {
    const dt = new Date(iso);
    const pad = (n) => String(n).padStart(2, "0");
    const YYYY = dt.getFullYear();
    const MM = pad(dt.getMonth() + 1);
    const DD = pad(dt.getDate());
    const hh = pad(dt.getHours());
    const mm = pad(dt.getMinutes());
    return `${YYYY}-${MM}-${DD}T${hh}:${mm}`;
  }

  // initial load
  loadTasks();
});


