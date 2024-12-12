document.addEventListener("DOMContentLoaded", () => {
    console.log("Page loaded. Setting up feedback popup.");
    setTimeout(showFeedbackPopup, 3000);
});

async function showFeedbackPopup() {
    console.log("Attempting to fetch feedback question...");

    try {
        const response = await fetch('/api/feedback/check-for-popup');

        console.log("Response from server:", response);

        if (!response.ok) {
            console.error("Error fetching feedback question. Status:", response.status);
            return;
        }

        const data = await response.json();
        console.log("Data received:", data);

        if (data.message === 'Popup triggered') {
            console.log("Popup triggered with data:", data);

            const popup = document.getElementById("feedback-popup");
            const questionText = document.getElementById("popup-question-text");
            const optionsContainer = document.getElementById("popup-options");

            questionText.textContent = data.question_text;
            optionsContainer.innerHTML = "";

            if (data.question_type === "yes_no") {
                console.log("Setting up Yes/No question.");
                optionsContainer.innerHTML = `
                    <button class="yes-no" data-value="true">Yes</button>
                    <button class="yes-no" data-value="false">No</button>
                `;
            } else if (data.question_type === "rating") {
                console.log("Setting up Rating question.");
                for (let i = 1; i <= 5; i++) {
                    optionsContainer.innerHTML += `<button class="rating" data-value="${i}">${i}</button>`;
                }
            } else if (data.question_type === "short_answer") {
                console.log("Setting up Short Answer question.");
                optionsContainer.innerHTML = `
                    <textarea id="short-answer" placeholder="Your answer..."></textarea>
                `;
            }

            popup.style.display = "flex";

            document.getElementById("submit-feedback").onclick = async () => {


                const userId = 1;


                let content = null;

                if (data.question_type === "yes_no") {
                    const selectedButton = document.querySelector(".yes-no.selected");
                    if (selectedButton) {
                        content = selectedButton.getAttribute("data-value");
                    }
                } else if (data.question_type === "rating") {
                    const selectedButton = document.querySelector(".rating.selected");
                    if (selectedButton) {
                        content = selectedButton.getAttribute("data-value");
                    }
                } else if (data.question_type === "short_answer") {
                    content = document.getElementById("short-answer").value;
                }

                if (content) {
                    console.log("Submitting feedback with content:", content);
                    const submitResponse = await fetch('/api/feedback/submit-feedback', {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({
                            question_id: data.question_id,
                            question_type: data.question_type,
                            user_id: userId,
                            is_yes: content === "true",
                            rating: parseInt(content),
                            answer_text: content
                        })
                    });


                    if (submitResponse.ok) {
                        console.log("Feedback submitted successfully.");
                        alert("Feedback submitted successfully!");
                        popup.style.display = "none";
                    } else {
                        console.error("Failed to submit feedback. Response:", await submitResponse.text());
                        alert("Failed to submit feedback.");
                    }
                } else {
                    alert("Please provide an answer.");
                }
            };

            optionsContainer.addEventListener("click", (e) => {
                if (e.target.tagName === "BUTTON") {
                    optionsContainer.querySelectorAll("button").forEach((btn) => btn.classList.remove("selected"));
                    e.target.classList.add("selected");
                }
            });
        } else {
            console.log("No popup triggered. Message:", data.message);
        }
    } catch (error) {
        console.error("Error showing feedback popup:", error);
    }
}
