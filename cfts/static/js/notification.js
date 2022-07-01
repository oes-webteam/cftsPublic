/* ****************************************** */
/* USER NOTIFICATION (NEEDS VAST IMPROVEMENT) */
/* ****************************************** */

notifyUserSuccess = (msg) => {
    console.log("Success message")
    $(".server-error").hide()
    $(".danger-error").hide()
    $(".file-error").hide().text("")
    let alertDiv = $(".notification-success");
    alertDiv.html(msg);
    alertDiv.fadeIn();
};

notifyFileWarning = (msg) => {
    console.log("Warning message")
    $(".notification-success").hide()
    $(".server-error").hide()
    let alertDiv = $(".file-error");
    if (alertDiv.is(':visible')) msg = "<hr />" + msg;
    alertDiv.append("<ul style='text-align: left;'>" + msg + "</ul>");
    alertDiv.fadeIn();
};

notifyUserWarning = (msg) => {
    console.log("Warning message")
    $(".notification-success").hide()
    $(".server-error").hide()
    let alertDiv = $(".danger-error");
    alertDiv.text(msg);
    alertDiv.fadeIn();
};

notifyUserError = (msg) => {
    console.log("Error message")
    $(".notification-success").hide()
    $(".danger-error").hide()
    let alertDiv = $(".server-error");
    alertDiv.text(msg);
    alertDiv.fadeIn();
};