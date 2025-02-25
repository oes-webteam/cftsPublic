// function setProgress(percentage) {
//     let radius = 18;
//     let circumference = 2 * Math.PI * radius; // Full circumference
//     let offset = circumference - (percentage / 100) * circumference;

//     $(".progress-ring__circle")
//         .attr("stroke-dasharray", circumference) // Ensure correct value
//         .attr("stroke-dashoffset", offset); // Update progress
// }

// function updateProgress() {
//     let totalFiles = $(".file-review").length;
//     let completedFiles = $(".file-review:checked").length;
//     let progress = (completedFiles / totalFiles) * 100;

//     setProgress(progress);
// }
$(document).ready(function () {
    $(".file-row").each(function () {
        const firstReviewerCompleted = $(this).data("first-reviewer") === true;
        const secondReviewerCompleted = $(this).data("second-reviewer") === true;

        const checkmarkContainer = $("<span></span>"); 

        if (firstReviewerCompleted) {
            checkmarkContainer.append("✔️");
        }

        if (secondReviewerCompleted) {
            checkmarkContainer.append("✔️");
        }

        $(this).find(".file-left").append(checkmarkContainer); 

        // $(".file-review").on("change", function () {
        //     updateProgress();
        // });

        // updateProgress(); 
    });
});
