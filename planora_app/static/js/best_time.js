async function fetchBestTime() {

    try {

        const res = await fetch("/cards/best-time");
        const data = await res.json();

        const bestTimeEl =
            document.getElementById("peak-focus-time");

        const subtitleEl =
            document.getElementById("best-time-subtitle");

        bestTimeEl.textContent = data.best_time;

        if (data.source === "preference") {

            subtitleEl.textContent =
                "Based on your onboarding preference";

        } else {

            subtitleEl.textContent =
                "Based on your recent study sessions";
        }

    } catch (err) {

        console.error(err);

        document.getElementById(
            "peak-focus-time"
        ).textContent = "Error";

        document.getElementById(
            "best-time-subtitle"
        ).textContent = "Could not load data";
    }
}

window.addEventListener(
    "DOMContentLoaded",
    fetchBestTime
);