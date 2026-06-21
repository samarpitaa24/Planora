document.addEventListener("DOMContentLoaded", async () => {

    const subjectEl = document.getElementById("priority-subject");
    const reasonEl = document.getElementById("priority-reason");

    try {

        const res = await fetch("/cards/priority-focus");
        const data = await res.json();

        if (!res.ok) {
            throw new Error(data.error || "Failed to fetch");
        }


        subjectEl.textContent = data.subject;
        reasonEl.textContent = data.reason;

    } catch (err) {

        console.error(err);

        subjectEl.textContent = "Error";
        reasonEl.textContent = "Could not load recommendation";
    }
});