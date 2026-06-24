document.addEventListener("DOMContentLoaded", async () => {

    const streakEl = document.getElementById("daily-streak-count");
    const highestEl = document.getElementById("daily-streak-missed");
    const msgEl = document.getElementById("daily-streak-msg");

    try {

        const res = await fetch("/cards/daily-streak");

        let data = {};

        try {
            data = await res.json();
        } catch (e) {}

        if (!res.ok) {
            throw new Error(data.error || "Failed to fetch streak");
        }

        const currentStreak = data.current_streak || 0;
        const highestStreak = data.highest_streak || 0;
        const message = data.message || "";

        streakEl.textContent =
            `${currentStreak} ${currentStreak === 1 ? "day" : "days"}`;

        highestEl.textContent =
            `${highestStreak} ${highestStreak === 1 ? "day" : "days"}`;

        msgEl.textContent = message;

    } catch (err) {

        console.error(err);

        streakEl.textContent = "0 days";
        highestEl.textContent = "0 days";
        msgEl.textContent = "Unable to load streak";

    }

});