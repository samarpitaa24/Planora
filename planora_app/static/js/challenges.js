document.addEventListener("DOMContentLoaded", async () => {

    const weeklyContainer = document.getElementById("weekly-challenges");
    const badgesContainer = document.getElementById("badges-grid");

    const BADGE_CONFIG = {
        ch1: {
            file: "img1.png",
            name: "Pomodoro Pro"
        },
        ch2: {
            file: "img2.png",
            name: "Focus Finder"
        },
        ch3: {
            file: "img3.png",
            name: "Streak Keeper"
        }
    };

    async function renderChallenges(challenges) {

        weeklyContainer.innerHTML = "";
        badgesContainer.innerHTML = "";

        challenges.forEach((ch) => {

            const progress = Number(ch.progress) || 0;

            const chDiv = document.createElement("div");
            chDiv.className = "challenge-item";

            let statusClass = "status-notstarted";

            if (ch.status === "completed") {
                statusClass = "status-completed";
            }
            else if (
                ch.status === "in progress" ||
                ch.status === "in_progress"
            ) {
                statusClass = "status-progress";
            }

            chDiv.innerHTML = `
                <h3>
                    ${ch.challenge_name}
                    ${ch.expected_subject ? ` : ${ch.expected_subject}` : ""}
                </h3>

                <span class="status-pill ${statusClass}">
                    ${ch.status}
                </span>

                <div class="progress-wrapper">

                    <div class="progress-info">
                        <span>Progress</span>
                        <span>${progress}%</span>
                    </div>

                    <div class="progress-bar">
                        <div
                            class="progress-fill"
                            style="width:${progress}%;">
                        </div>
                    </div>

                </div>
            `;

            weeklyContainer.appendChild(chDiv);

            const badgeConfig = BADGE_CONFIG[ch.challenge_id];

            if (badgeConfig) {

                const badgeDiv = document.createElement("div");

                const isCompleted =
                    ch.status === "completed";

                badgeDiv.className =
                    `badge-item ${isCompleted ? "completed" : "locked"}`;

                badgeDiv.innerHTML = `
                    <img
                        src="/static/images/${badgeConfig.file}"
                        alt="${badgeConfig.name}"
                        class="badge-icon">

                    <p>${badgeConfig.name}</p>
                `;

                badgesContainer.appendChild(badgeDiv);
            }
        });
    }

    async function refreshChallenges() {

        try {

            const res = await fetch("/challenges/api");

            if (!res.ok) {
                throw new Error("Failed to fetch challenges");
            }

            const challenges = await res.json();

            console.log("Challenges:", challenges);

            renderChallenges(challenges);

        }
        catch (err) {

            console.error(err);

            weeklyContainer.innerHTML =
                "<p>Failed to load challenges</p>";

            badgesContainer.innerHTML =
                "<p>Failed to load badges</p>";
        }
    }

    await refreshChallenges();
});