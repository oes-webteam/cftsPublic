document.addEventListener("DOMContentLoaded", function () {
    // Add checkmarks based on review status
    document.querySelectorAll(".file-row").forEach(row => {
        let fileId = row.id.split("_")[1];  // Extract file_id from row ID
        let firstReviewerCompleted = row.getAttribute("data-first-reviewer") === "true";
        let secondReviewerCompleted = row.getAttribute("data-second-reviewer") === "true";
        
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

    if (showMoreBtn) {
        showMoreBtn.addEventListener("click", function () {
            let extraFiles = document.querySelectorAll(".extra-files");

            extraFiles.forEach(file => file.classList.toggle("d-none"));

            if (showMoreBtn.innerText.includes("Show")) {
                showMoreBtn.innerText = "Show Less";
            } else {
                showMoreBtn.innerText = `Show ${extraFiles.length} more files...`;
            }
        });
    }
});