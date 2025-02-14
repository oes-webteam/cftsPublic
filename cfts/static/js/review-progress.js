document.addEventListener("DOMContentLoaded", function () {
    // Add checkmarks based on review status
    document.querySelectorAll(".file-row").forEach(row => {
        let firstReviewerCompleted = row.getAttribute("data-first-reviewer") === "true";
        let secondReviewerCompleted = row.getAttribute("data-second-reviewer") === "true";
        let reviewerBegin = document.getElementById('btn-review')
        
        let checkmarkContainer = document.createElement("span");

        if (firstReviewerCompleted) {
            checkmarkContainer.innerHTML += "✔️";
        }

        if (secondReviewerCompleted) {
            checkmarkContainer.innerHTML += "✔️";
        }

        row.querySelector(".file-left").appendChild(checkmarkContainer);
    });

    const showMoreBtn = document.getElementById("showMoreBtn");
    const extraFiles = document.querySelectorAll(".extra-files"); // Select all hidden files

    if (showMoreBtn) {
        showMoreBtn.addEventListener("click", function () {
            extraFiles.forEach(file => file.classList.toggle("d-none"));

            // Toggle button text
            if (showMoreBtn.innerText.includes("Show")) {
                showMoreBtn.innerText = "Show Less";
            } else {
                showMoreBtn.innerText = `Show ${extraFiles.length} more files...`;
            }
        });
    }
});