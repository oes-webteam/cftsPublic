$(document).ready(function () {
    $(".file-row").each(function () {
        updateCheckmarks($(this));
    });

    $(".btn-review").on("click", function () {
        const fileRow = $(this).closest(".file-row");

        // Simulate completion for a reviewer
        if (!fileRow.attr("data-first-reviewer")) {
            fileRow.attr("data-first-reviewer", "true");
        } else if (!fileRow.attr("data-second-reviewer")) {
            fileRow.attr("data-second-reviewer", "true");
        }

        updateCheckmarks(fileRow);
        updateProgress();
    });

    updateProgress();
});

function updateCheckmarks(fileRow) {
    const firstReviewerCompleted = fileRow.attr("data-first-reviewer") === "true";
    const secondReviewerCompleted = fileRow.attr("data-second-reviewer") === "true";
    const firstReviewerStarted = fileRow.attr("data-first-reviewer-started") === "true";
    const secondReviewerStarted = fileRow.attr("data-second-reviewer-started") === "true";

    let checkmarkContainer = fileRow.find(".file-left span");

    if (checkmarkContainer.length === 0) {
        checkmarkContainer = $("<span></span>").appendTo(fileRow.find(".file-left"));
    } else {
        checkmarkContainer.empty();
    }

    if (firstReviewerCompleted) {
        checkmarkContainer.append("✔️");
    } else if (firstReviewerStarted) {
        checkmarkContainer.append("⏳");
    }

    if (secondReviewerCompleted) {
        checkmarkContainer.append("✔️");
    } else if (secondReviewerStarted) {
        checkmarkContainer.append("⏳");
    }
}

function updateProgress() {
    const totalFilesCount = document.getElementById('file-count').getAttribute('data-count');
    console.log(totalFilesCount); 
    let firstReviewerCompleted = $(".file-row").filter(function () {
        return $(this).attr("data-first-reviewer") === "true";
    }).length;

    let secondReviewerCompleted = $(".file-row").filter(function () {
        return $(this).attr("data-second-reviewer") === "true";
    }).length;

    let firstReviewerProgress = (firstReviewerCompleted / totalFiles) * 100;
    let secondReviewerProgress = (secondReviewerCompleted / totalFiles) * 100;

    updateCircularProgress(".first-reviewer-progress .progress-ring", ".first-reviewer-progress .progress-text", firstReviewerProgress, firstReviewerCompleted, totalFiles);
    updateCircularProgress(".second-reviewer-progress .progress-ring", ".second-reviewer-progress .progress-text", secondReviewerProgress, secondReviewerCompleted, totalFiles);
}

function updateCircularProgress(selector, textSelector, progress, completed, total) {
    let circumference = 2 * Math.PI * 30;
    let offset = circumference - (progress / 100) * circumference;

    $(selector).css("stroke-dashoffset", offset)
               .css("stroke", "green");

    $(textSelector).text(`${completed}/${total}`);
}