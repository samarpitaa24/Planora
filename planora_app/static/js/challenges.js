

document.addEventListener("DOMContentLoaded", async () => {
    const weeklyContainer = document.getElementById("weekly-challenges");
    const badgesContainer = document.getElementById("badges-grid");

    // Badge mapping: challenge_id -> badge file name and badge name
    const BADGE_CONFIG = {
        "ch1": {
            file: "img1.png",
            name: "Pomodoro Pro "
        },
        "ch2": {
            file: "img2.png",
            name: "Focus Finder"
        },
        "ch3": {
            file: "img3.png",
            name: "Streak Keeper"
        }
    };

    async function renderChallenges(challenges) {
        weeklyContainer.innerHTML = "";
        badgesContainer.innerHTML = "";

        challenges.forEach(ch => {
            // Weekly challenges section
            const chDiv = document.createElement("div");
            chDiv.className = "challenge-item";
            chDiv.style.cursor = "pointer";
            chDiv.title = "Click to recalculate this week's progress";

            chDiv.innerHTML = `
                <h3>${ch.challenge_name}${ch.expected_subject ? `: ${ch.expected_subject}` : ""}</h3>
                <div class="progress-bar">
                  <div class="progress" style="width:${ch.progress}%"></div>
                </div>
                <p>Status: <span class="status-text">${ch.status}</span></p>
            `;

            // Click handler to update challenge
            chDiv.addEventListener("click", async (e) => {
                try {
                    chDiv.style.opacity = "0.6";
                    chDiv.style.pointerEvents = "none";

                    const res = await fetch("/challenges/update", {
                        method: "POST",
                        headers: {
                            "Content-Type": "application/json"
                        },
                        body: JSON.stringify({ challenge_id: ch.challenge_id })
                    });

                    if (!res.ok) {
                        console.error("Update failed", await res.text());
                    }

                    await refreshChallenges();

                } catch (err) {
                    console.error(err);
                } finally {
                    chDiv.style.opacity = "";
                    chDiv.style.pointerEvents = "";
                }
            });

            weeklyContainer.appendChild(chDiv);

            // Badge section with SVG images
            const badgeConfig = BADGE_CONFIG[ch.challenge_id];
            if (badgeConfig) {
                const badgeDiv = document.createElement("div");
                const isCompleted = ch.status === "completed";
                
                badgeDiv.className = `badge-item ${isCompleted ? 'completed' : 'locked'}`;
                
                badgeDiv.innerHTML = `
                    <img src="/static/images/${badgeConfig.file}" 
                         alt="${badgeConfig.name}" 
                         class="badge-icon"
                         title="${isCompleted ? 'Completed!' : 'Complete the challenge to unlock'}">
                    <p>${badgeConfig.name}</p>
                `;
                
                badgesContainer.appendChild(badgeDiv);
            }
        });
    }

    async function refreshChallenges() {
        try {
            const res = await fetch("/challenges/api");
            if (!res.ok) throw new Error("Failed to fetch /challenges/api");
            const challenges = await res.json();
            await renderChallenges(challenges);
        } catch (err) {
            console.error(err);
            weeklyContainer.textContent = "Failed to load challenges";
            badgesContainer.textContent = "Failed to load badges";
        }
    }

    // Initial load
    await refreshChallenges();
});