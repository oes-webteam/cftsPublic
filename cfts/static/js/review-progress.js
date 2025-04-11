$(document).ready(function () {
    $(".toggle-files").off("click").on("click", function (e) {
        e.preventDefault();

        const fileList = $(this).closest("ul");
        const allFiles = fileList.find(".file-item");
        const hiddenFiles = allFiles.slice(4);

        if (hiddenFiles.css("display") === "none") {
            hiddenFiles.css("display", "list-item");
            $(this).text("Show Less"); 
        } else {
            hiddenFiles.css("display", "none"); // Hide files
            $(this).text(`Show ${hiddenFiles.length} more files`); 
        }
    });
});
