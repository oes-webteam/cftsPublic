$(document).ready(function () {
    $(".file-row").each(function () {
        updateCheckmarks($(this));
    });

    $(".btn-review").on("click", function () {
        const fileRow = $(this).closest(".file-row");
        if (!fileRow.attr("data-first-reviewer")) {
            fileRow.attr("data-first-reviewer", "true");
        } else if (!fileRow.attr("data-second-reviewer")) {
            fileRow.attr("data-second-reviewer", "true");
        }

        updateCheckmarks(fileRow);
    });

    
    

    $(".toggle-files").on("click", function (e) {
        console.log("Button clicked")
        e.preventDefault();
        const fileList = $(this).closest("ul");
        const allFiles = fileList.find(".file-item");
        const hiddenFiles = fileList.find(".file-item:hidden"); 

        if (hiddenFiles.length > 0) {
            hiddenFiles.show(); 
            $(this).text("Show Less");
        } else{
            console.log("Class added")
            allFiles.slice(4).addClass("hidden");
            $(this).text(`Show ${allFiles.length - 4} more files`);
        }
        
    });

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