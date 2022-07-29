/* transfer-request.js */
window.document.title = "Request Info";

jQuery(document).ready(function () {

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

            let fileLink = document.getElementById(paramObj.file);
            console.log(fileLink);
            history.pushState(null, "", location.href.split("?")[0]);

            fileLink.click();
        }
    }


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


    $('#rejectionSubmit').click(e => {
        console.log("rejection submit clicked");

        const checkedItems = $(".file-check.not-rejected:checked");
        const checkedItemsRejected = $(".file-check.rejected:checked");
        const checkedReasons = $(".reason-check:checked");

        // no files selected to reject or un-reject
        if (checkedItems.length == 0 && checkedItemsRejected.length == 0) {
            alert('Select 1 or more files to change rejection status.');
        }

        // selected files are a mix of rejected and not rejected files
        else if (checkedItems.length > 0 && checkedItemsRejected.length > 0) {
            alert('Cannot process a mix of rejected and non-rejected files. Rejection and un-rejection are seperate processes. Please select only files to reject or only files to un-reject.');

        }

        // files to reject
        else if (checkedItems.length > 0) {

            let file_ids = [];
            let rejectionReasons = [];

            console.log(checkedItems);

            checkedItems.each(i => {
                file_ids.push(checkedItems[i].id);
            });

            console.log(checkedReasons);

            checkedReasons.each(i => {
                rejectionReasons.push(checkedReasons[i].id);
            });

            rejectFormCallback(file_ids, rejectionReasons, rqst_id);
        }

        //files to un-reject
        else if (checkedItemsRejected.length > 0) {
            let file_ids = [];

            console.log(checkedItemsRejected);

            checkedItemsRejected.each(i => {
                file_ids.push(checkedItemsRejected[i].id);
            });
            sendUnrejectRequest(file_ids, rqst_id);
        }
    });


    const sendUnrejectRequest = (file_ids, request_id) => {
        console.log(file_ids);

        let csrftoken = getCookie('csrftoken');

        const postData = {
            'request_id': request_id, // doesn't matter which request we grab
            'id_list': file_ids
        };

        const setUnrejectOnFiles = $.post('/api-unreject', postData, 'json').then(
            // success
            function (resp, status) {
                console.log('SUCCESS');
                // notifyUserSuccess("File Unreject Successful")
                $("#forceReload").submit();
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

    };


    /****************************/
    /* Encrypt files in request */
    /****************************/

    $('.request-encrypt').click(e => {
        e.preventDefault();

        if ($(e.target).hasClass('selected-encrypt')) {
            console.log("selcted encrypt clicked");

            const checkedItems = $("[name='fileSelection']:checked");

            if (checkedItems.length == 0) {
                alert(' Select 1 or more files to encrypt.');
            } else {
                let file_ids = [];
                checkedItems.each(i => {
                    file_ids.push(checkedItems[i].id);
                });
                sendEncryptRequest(file_ids, rqst_id);
            }

        } else {
            console.log("request encrypt clicked");
            const checkboxes = Array.from(document.querySelectorAll('input[type="checkbox"]'));
            checkboxes.forEach(checkbox => {
                checkbox.removeAttribute("hidden");
            });

            $(e.target).text("Encrypt Selected");
            $(e.target).addClass('selected-encrypt');
        }

    });

    const sendEncryptRequest = (file_ids, request_id) => {
        console.log(file_ids);

        let csrftoken = getCookie('csrftoken');

        const postData = {
            'request_id': request_id, // doesn't matter which request we grab
            'id_list': file_ids
        };

        const setEncryptOnFiles = $.post('/api-setencrypt', postData, 'json').then(
            // success
            function (resp, status) {
                console.log('SUCCESS');
                $("#forceReload").submit();
            },
            // fail 
            function (resp, status) {
                console.log('FAIL');

                alert("Failed to encrypt files, send error message to web team.");
                responseText = resp.responseText;
                errorInfo = responseText.substring(resp.responseText.indexOf("Exception Value"), resp.responseText.indexOf("Python Executable"));

                notifyUserError("Error encrypting file, send error message to web team: " + errorInfo);
            }
        );

    };

    // REJECTION MODAL INPUT VALIDATION AND ACTION
    const rejectFormCallback = (file_ids, reasons, request_id) => {
        let csrftoken = getCookie('csrftoken');

        const postData = {
            'reject_id': reasons,
            'request_id': request_id, // doesn't matter which request we grab
            'id_list': file_ids
        };

        const setRejectOnFiles = $.post('/api-setreject', postData, 'json').then(
            // success
            function (resp) {
                console.log('SUCCESS');
                console.log('Server response: ' + JSON.stringify(resp, null, 4));

                if (resp.debug != true) {
                    // create mailto anchor
                    let $anchor = $("<a class='emailLink' target='_blank' href='" + resp.eml + "''></a>");
                    $(document.body).append($anchor);

                    $('.emailLink').each(function () {
                        $(this)[0].click();
                    });
                }
                // reload the page from server
                if (resp.flash == false) {
                    window.location = window.location + '?flash=false';
                } else {
                    window.location = window.location;
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


    // supersuer button to remove users from file review
    $('.request-remove').click(e => {
        e.preventDefault();

        if ($(e.target).hasClass('selected-remove')) {
            console.log("selcted Remove clicked");

            const checkedItems = $("[name='fileSelection']:checked");

            if (checkedItems.length == 0) {
                alert(' Select 1 or more files to remove reviewer from.');
            } else {
                let data = [];

                if ($(e.target).hasClass('one-eye')) {
                    stage = 1;
                } else if ($(e.target).hasClass('two-eye')) {
                    stage = 2;
                }

                checkedItems.each(i => {
                    data.push(checkedItems[i].id);
                });

                rqst_id = $(e.target).attr('rqst_id');

                sendRemoveRequest(data, stage, rqst_id);
            }

        } else {
            console.log("request remove clicked");
            const checkboxes = Array.from(document.querySelectorAll('input[type="checkbox"]'));
            checkboxes.forEach(checkbox => {
                checkbox.removeAttribute("hidden");
            });
            const reviewers = Array.from(document.querySelectorAll('.reviewers'));
            reviewers.forEach(elem => {
                elem.classList.remove('d-none');
            });
            $(e.target).text("Remove Selected");
            $(e.target).addClass('selected-remove');
        }

    });

    const sendRemoveRequest = (data, stage, rqst_id) => {
        console.log(stage);
        let csrftoken = getCookie('csrftoken');

        let id_list = [];
        data.forEach((f) => {
            id_list.push(f.fileID);
        });

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