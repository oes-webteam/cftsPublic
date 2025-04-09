/* transfer-request.js */
window.document.title = "Request Info";

jQuery(document).ready(function () {
    // instantiate the rejection popovers
    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    var popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });

    if (document.location.search) {
        const search = document.location.search;
        const params = new URLSearchParams(search);
        let paramObj = {};
        for (var value of params.keys()) {
            paramObj[value] = params.get(value);
        }

        //console.log(paramObj)

        if (paramObj.eml) {

            let eml = paramObj.eml + "&body=" + paramObj.body;
            let $anchor = $("<a class='banEmailLink' target='_blank' href='" + eml.replace(/<br>/g, "%0D%0A%0D%0A") + "''></a>");
            $(document.body).append($anchor);

            $('.banEmailLink').each(function () {
                $(this)[0].click();
            });

            history.pushState(null, "", location.href.split("?")[0]);
        }

        if (paramObj.warning) {
            $('#userWarning').attr('href', $('#userWarning').attr('href') + "/true");
            history.pushState(null, "", location.href.split("?")[0]);
        }

        if (paramObj.flash == "false") {
            $('.btn-back').attr('href', '/queue');
            history.pushState(null, "", location.href.split("?")[0]);
        }

        if (paramObj.file) {
            let row = document.getElementById("row_" + paramObj.file);

            row.scrollIntoView({
                behavior: "smooth",
                block: "center"
            });
            setTimeout(function () {
                $('#row_' + paramObj.file).fadeOut(400).fadeIn(400).fadeOut(400).fadeIn(400);
            }, 500);

            let fileLink = document.getElementById("get_" + paramObj.file);
            console.log(fileLink);
            history.pushState(null, "", location.href.split("?")[0]);

            fileLink.click();
        }
    }

    let reloadLocaiton = window.location;


    $.ajaxSetup({
        beforeSend: function (xhr, settings) {
            xhr.setRequestHeader("X-CSRFToken", getCookie('csrftoken'));
        }
    });

    $('#noteBtn').click(e => {
        e.preventDefault();
        data = {
            'notes': $('#notesField').val()
        };


        $.post("/api-requestnotes/" + rqst_id, data, 'json').then(
            function (resp) {
                window.location.replace(window.location);
            },
        );

    });


    $('.reject-dupes').click(e => {
        e.preventDefault();
        requestIDs = [];

        keeperID = $(e.target).attr('current_id');
        requestHash = $(e.target).attr('request_hash');

        requests = document.querySelectorAll('a.card[request_hash="' + requestHash + '"]');
        requests.forEach(request => {
            requestIDs.push(request.id);
        });

        data = {
            'requestIDs': requestIDs,
            'keeperRequest': keeperID
        };

        $.post("/api-setrejectdupes", data, 'json').then(
            function (resp) {
                window.location.replace(window.location);
            },
        );

    });

    $(document).on('click', '#select-all-files', function () {
        let isChecked = $(this).prop('checked');
        $(".all-files[original]").prop('checked', isChecked); 
    });
    
    $(document).on('click', '#select-all-files', function () {
        let isChecked = $(this).prop('checked');
        $(".all-files[original]").prop('checked', isChecked); 
    });
    

    $(document).on('click', '#modifyRejectionSubmit', function (e) {
        console.log("rejection modify submit clicked");
        $('#modifyRejectionSubmit').attr('disabled', 'true');

        const checkedItemsRejected = $(".file-check.rejected:checked[modify]");
        const checkedReasons = $(".reason-check:checked[modify]");

        let file_ids = [];
        let rejectionReasons = [];
        let reject_text = $("#mod-reject-comments[modify]").val();

        console.log(checkedItemsRejected);

        checkedItemsRejected.each(i => {
            console.log(checkedItemsRejected[i].id.split("_")[1]);
            file_ids.push(checkedItemsRejected[i].id.split("_")[1]);
        });

        console.log(checkedReasons);

        checkedReasons.each(i => {
            rejectionReasons.push(checkedReasons[i].id.split("_")[1]);
        });

        rejectFormCallback(file_ids, rejectionReasons, rqst_id, reject_text);

    });


    $(document).on('click', '#rejectionSubmit', function (e) {
        console.log("rejection submit clicked");
        $('#rejectionSubmit').attr('disabled', 'true');

        const checkedItems = $(".file-check.not-rejected:checked[original]");
        const checkedReasons = $(".reason-check:checked[original]");
        let file_ids = [];
        let rejectionReasons = [];
        let reject_text = $("#reject-comments").val();

        if (checkedReasons.length === 0) {
            alert('Select 1 or more rejection reasons.');
            $('#rejectionSubmit').removeAttr('disabled');
            return;
        }

        if (checkedItems.length == 0) {
            alert(' Select 1 or more files to reject.');
            $('#rejectionSubmit').removeAttr('disabled', 'false');
        } else {
            console.log(checkedItems);

            checkedItems.each(i => {
                file_ids.push(checkedItems[i].id);
            });

            console.log(checkedReasons);

            checkedReasons.each(i => {
                rejectionReasons.push(checkedReasons[i].id);
            });

            rejectFormCallback(file_ids, rejectionReasons, rqst_id, reject_text);
        }
    });

    $(document).on('click', '#unrejectionSubmit', function (e) {
        console.log("unreject submit clicked");
        $('#unrejectionSubmit').attr('disabled', 'true');
        const checkedItemsRejected = $(".file-check.rejected:checked[modify]");

        let file_ids = [];

        console.log(checkedItemsRejected);

        checkedItemsRejected.each(i => {
            file_ids.push(checkedItemsRejected[i].id.split("_")[1]);
        });

        console.log(file_ids);

        let csrftoken = getCookie('csrftoken');

        const postData = {
            'request_id': rqst_id, // doesn't matter which request we grab
            'id_list': file_ids
        };

        $.post('/api-unreject', postData, 'json').then(
            // success
            function (resp, status) {
                console.log('SUCCESS');
                //$("#forceReload").submit();
                console.log(window.location);
                window.location = reloadLocaiton;
            },
            // fail 
            function (resp, status) {
                console.log('FAIL');

                alert("Failed to unreject files, send error message to web team.");
                responseText = resp.responseText;
                errorInfo = responseText.substring(resp.responseText.indexOf("Exception Value"), resp.responseText.indexOf("Python Executable"));

                notifyUserError("Error unrejecting file, send error message to web team: " + errorInfo);
            }
        );
    });


    /****************************/
    /* Encrypt files in request */
    /****************************/

   // Select All functionality for encryption
$(document).on('click', '#encrypt-all-files', function () {
    let isChecked = $(this).prop('checked');
    $(".file-check.encrypt").prop('checked', isChecked); // Select/deselect all files for encryption
});

// Submission logic for encryption
$(document).on('click', '#encryptSubmit', function (e) {
    $('#encryptSubmit').attr('disabled', 'true');

    const checkedItems = $(".file-check.encrypt:checked"); // Selected files for encryption
    let file_ids = [];

    console.log(checkedItems);

    if (checkedItems.length == 0) {
        alert('Select 1 or more files to encrypt.');
        $('#encryptSubmit').removeAttr('disabled', 'false');
    } else {
        checkedItems.each(function () {
            file_ids.push($(this).attr('id').split("_")[1]);
        });

        console.log("Encrypting files: ", file_ids);

        sendEncryptRequest(file_ids, rqst_id);
    }
});

// Encryption request logic
const sendEncryptRequest = (file_ids, request_id) => {
    console.log(file_ids);

    let csrftoken = getCookie('csrftoken');

    const postData = {
        'request_id': request_id, // Doesn't matter which request we grab
        'id_list': file_ids
    };

    const setEncryptOnFiles = $.post('/api-setencrypt', postData, 'json').then(
        // Success callback
        function (resp, status) {
            console.log('SUCCESS');
            $("#forceReload").submit(); // Reload the page or refresh the state
        },
        // Failure callback
        function (resp, status) {
            console.log('FAIL');

            alert("Failed to encrypt files, send error message to web team.");
            let responseText = resp.responseText;
            let errorInfo = responseText.substring(
                resp.responseText.indexOf("Exception Value"),
                resp.responseText.indexOf("Python Executable")
            );

            notifyUserError("Error encrypting file, send error message to web team: " + errorInfo);
        }
    );
};

    // REJECTION MODAL INPUT VALIDATION AND ACTION
    const rejectFormCallback = (file_ids, reasons, request_id, reject_text) => {
        let csrftoken = getCookie('csrftoken');

        const postData = {
            'reject_id': reasons,
            'request_id': request_id, // doesn't matter which request we grab
            'id_list': file_ids,
            'reject_text': reject_text
        };

        const setRejectOnFiles = $.post('/api-setreject', postData, 'json').then(
            // success
            function (resp) {
                console.log('SUCCESS');
                console.log('Server response: ' + JSON.stringify(resp, null, 4));

                if (resp.debug != true && resp.eml) {
                    // create mailto anchor
                    let $anchor = $("<a class='emailLink' target='_blank' href='" + resp.eml + "''></a>");
                    $(document.body).append($anchor);

                    $('.emailLink').each(function () {
                        $(this)[0].click();
                    });
                }
                console.log(reloadLocaiton);
                // reload the page from server
                if (resp.flash == false) {
                    window.location = reloadLocaiton + '?flash=false';
                } else {
                    window.location = reloadLocaiton;
                }
            },
            // fail 
            function (resp, status) {
                alert("Failed to reject files, send error message to web team.");

                console.log('FAIL');
                responseText = resp.responseText;
                errorInfo = responseText.substring(resp.responseText.indexOf("Exception Value"), resp.responseText.indexOf("Python Executable"));

                notifyUserError("Error rejecting file, send error message to web team: " + errorInfo);
            }
        );
    };

    $(document).on('click', '#modifyReviewSubmit', function (e) {
        $('#modifyReviewSubmit').attr('disabled', 'true');

        const checkedItems = $(".review-check:checked");

        if (checkedItems.length == 0) {
            alert(' Select a reviewer to remove.');
            $('#modifyReviewSubmit').removeAttr('disabled', 'false');
        } else {
            let data = [];
            
            checkedItems.each(i => {
                data.push(checkedItems[i].id.split('_')[1]);
                if (checkedItems[i].classList.contains('one-eye')) {
                    stage = 1;
                } else if (checkedItems[i].classList.contains('two-eye')) {
                    stage = 2;
                }
            });

            sendRemoveRequest(data, stage, rqst_id);
        }
    });

    const sendRemoveRequest = (id_list, stage, rqst_id) => {
        console.log(stage);
        let csrftoken = getCookie('csrftoken');

        // let id_list = [];
        // data.forEach((f) => {
        //     id_list.push(f.fileID);
        // });

        const postData = {
            'id_list': id_list,
            'rqst_id': rqst_id
        };

        const removeReviewers = $.post('/removeFileReviewer/' + stage, postData, 'json').then(
            // success
            function (resp, status) {
                console.log('SUCCESS');
                $("#forceReload").submit();
            },
            // fail 
            function (resp, status) {
                console.log('FAIL');

                alert("Failed to remove reviewer, send error message to web team.");
                responseText = resp.responseText;
                errorInfo = responseText.substring(resp.responseText.indexOf("Exception Value"), resp.responseText.indexOf("Python Executable"));

                notifyUserError("Error removing reviewer, send error message to web team: " + errorInfo);
            }
        );

    };
});