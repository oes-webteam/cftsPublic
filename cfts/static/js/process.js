/* *****************************************
  process.js -- 
  Validate the form inputs, 
  POST them to the server for processing, 
  and handle the response 
  ****************************************** */

xferForm = document.querySelector("#transfer-request-form");
xferForm.addEventListener("submit", process, false);

/* **************** */
/* EMAIL VALIDATION */
/* **************** */
function checkEmail(email, net, direction) {
    // look -- if it's not even a real email address, just kick it the eff out
    var emailRegex = /^\w+([\.-]?\w+)*@\w+([\.-]?\w+)*(\.\w{2,3})+$/;
    if (!email.match(emailRegex)) return false;

    let domain = email.split("@").pop();
    let domainArray = domain.split(".");
    let check = "";
    switch (net) {
        case "NIPR":
            check = domainArray.pop();
            check = check.toLocaleLowerCase()
            return domain.indexOf("smil") == -1 && domain.indexOf("cmil") == -1 && (check == "mil" || check == "gov") ? true : false;
        case "SIPR":
            return domainArray.slice(-2).join(".") == "smil.mil" ? true : false;
            //case "BICES":
            //switch (direction) {
            //case "from":
            //return domainArray.slice(-2).join(".") == "bices.org" ? true : false;
            //case "to":
            //return domainArray.slice(-3).join(".") == "us.bices.org" ? true : false;
            //default:
            //notifyUserWarning(
            //"ERROR: A system error has occurred. The 'checkEmail' function is being called in an impropper manner ('direction' == " +
            //direction +
            //"). Please notify the CFTS administrators of this error by emailing {{ SETTINGS.CFTS_ADMIN_EMAIL }}."
            //);
            //break;
            //}
        default:
            //if (net.length)
            //notifyUserWarning(
            //"ERROR: A system error has occurred. The network " +
            //net +
            //" is not recognized by the 'checkEmail' function. Please notify the CFTS administrators of this error by emailing {{ SETTINGS.CFTS_ADMIN_EMAIL }}."
            //);
            //break;
            check = domainArray.pop();
            return (check == "mil" || check == "gov" || check == "edu" || check == "org") ? true : false;
    }
    // fail by default
    return false;
}

/* *************** */
/* FORM VALIDATION */
/* *************** */
function validateForm(form) {
    let thisNet = "SIPR";
    let isValid = true;
    let errors = [];

    // CLEAR!!  ...any previous submissions
    [...form.elements].forEach((elem) => {
        elem.classList.remove("is-valid");
        elem.classList.remove("is-invalid");
    });

    // name
    if (!(form.elements.firstName.value.length && form.elements.lastName.value.length)) {
        console.log("missing names")
        errors.push(form.elements.firstName, form.elements.lastName);
        isValid = false;
    }

    // source email
    if (!(form.elements.userEmail.value.length && checkEmail(form.elements.userEmail.value, thisNet, "from"))) {
        errors.push(form.elements.userEmail);
        isValid = false;
    }

    // file queue
    if (!fileQueue.length) {
        errors.push(form.elements["files[]"], document.querySelector("#drop-zone"));
        isValid = false;
    }

    // classifications
    for (let check of document.querySelectorAll(".file-classification")) {
        if (check.value == "") {
            errors.push(check);
            isValid = false;
        }
    }

    // target network
    // user has multiple destination network options
    if (!form.elements.network.value.length) {
        form.elements.network.forEach((elem) => errors.push(elem));
        isValid = false;
    }
    // user only has one destination network option
    else if (form.elements.network.length == undefined && form.elements.network.checked == false) {
        errors.push(form.elements.network);
        isValid = false;
    }

    // is centcom
    if (!form.elements.organization.value != "") {
        errors.push(form.elements.organization);
        isValid = false;
    }

    // target email(s)
    /* form has multiple emails */
    if (typeof form.elements.targetEmail.length != 'undefined' && form.elements.targetEmail.length > 1) {
        /* check all for validity */
        form.elements.targetEmail.forEach((elem) => {
            if (!checkEmail(elem.value, form.elements.network.value, "to")) {
                errors.push(elem);
                isValid = false;
            }
        });
    }
    /* form has one email */
    else if (typeof form.elements.targetEmail != 'undefined') {
        if (!(form.elements.targetEmail.value.length && checkEmail(form.elements.targetEmail.value, form.elements.network.value, "to"))) {
            errors.push(form.elements.targetEmail);
            isValid = false;
        }
    }
    /* uhh... the field doesn't even exist, I guess??? */
    else {
        console.dir(form.elements.targetEmail);
        console.log(form.elements.targetEmail.length);
        console.log("WTF happened here?!");
        return false;
    }


    // process errors
    if (!isValid) {
        // it's just a bunch of screwing around and explosions until you write it down (aka: log it)
        //errors.forEach( ( elem ) => console.dir( elem ) );

        // mark everything good
        [...form.elements].forEach((elem) => elem.classList.add("is-valid"));

        // mark the naughty-naughties
        errors.forEach((elem) => {
            elem.classList.remove("is-valid");
            elem.classList.add("is-invalid");
        });
    }

    return isValid;
}

/* ****************************************** */
/* PREPARE THE FORM DATA FOR THE AJAX REQUEST */
/* ****************************************** */
function prepareFormData(form) {
    let formData = new FormData(form);
    let data = new FormData();

    if (form.elements.targetEmail.length > 1) {
        let emailList = '';
        let first = true;
        for (let email of form.elements.targetEmail) {
            if (first) {
                emailList += email.value;
                first = false;
            } else {
                emailList += ',' + email.value;
            }
        }
        formData.delete('targetEmail');
        formData.append('targetEmail', emailList);
    }

    if (form.elements.organization.value == "OTHER") {
        formData.delete('isCentcom');
        formData.append('isCentcom', "False");
    } else {
        formData.delete('isCentcom');
        formData.append('isCentcom', "True");

    }

    data = prepareFileInfo(data);
    for (const [field, value] of formData.entries()) {
        if (!(field.includes("classification") || field.includes("encrypt") || field.includes("files[]"))) {
            data.append(field, value);
        }
    }

    for (let i in fileQueue) {
        data.append("files", fileQueue[i].object, fileQueue[i].name);
    }

    return data;
}

/* ***************** */
/* PREPARE FILE INFO */
/* ***************** */
function prepareFileInfo(formData) {
    let fileInfo = [];

    for (let i of fileQueue) {
        obj = {
            classification: i.cls,
            encrypt: i.encrypt.toString(),
        };
        fileInfo.push(obj);
    }

    formData.append("fileInfo", JSON.stringify(fileInfo));

    return formData;
}

/* ****************************** */
/* AJAX REQUEST SENT SUCCESSFULLY */
/* ****************************** */
function openRequestLink(id) {
    window.open(window.location.origin + "/request/" + id).focus();
}

function successHandler(r) {
    console.dir(r);
    notifyUserSuccess("THANK YOU! Your files have been submitted. Click <a <a class='alert-link' href='/my-requests'>here</a> to see your requests. ");

    if (debug != "True") {
        let requestlink = $("<div class='requestLink' style='display: none;'></div>");
        $(document.body).append(requestlink);
        requestlink.attr('onClick', "openRequestLink('" + r.request_id + "')")
        $('.requestLink').each(function() {
            $(this)[0].click();
        });
    }

    // CLEAN UP!!

    let destEmail = $("#targetEmail").val()

    document.getElementById("transfer-request-form").reset();
    resetFileQueue();
    resetAdditionalEmails();
    autoFillUserInfo(email, phone, destEmail);


    // re-enable the submit button
    $('#submitButton').prop('disabled', false);
}

function autoFillUserInfo(email, phone, destEmail) {
    $("#firstName").val(firstName)
    $("#lastName").val(lastName)
    $("#userPhone").val(phone)
    $("#userEmail").val(email)
    $("#organization").val(org)
    $("#targetEmail").val(destEmail)
}

function resetFileQueue() {
    fileQueue = []; // obvs
    fileList = document.querySelector('.file-list');
    fileList.removeChild(fileList.firstChild);

    let newSpan = document.createElement('span');
    let spanText = document.createTextNode('No files in queue.');
    newSpan.appendChild(spanText);

    let newSmall = document.createElement('small');
    let smallText = document.createTextNode('Use the button to the left or drag and drop files into the indicated area.');
    newSmall.appendChild(smallText);

    fileList.appendChild(newSpan);
    fileList.appendChild(newSmall);

    fileList.classList.add('init');
}

function resetAdditionalEmails() {
    let toRemove = document.querySelectorAll('.add-email');
    for (let el of toRemove) {
        el.remove();
    }
}


/* ******************* */
/* AJAX REQUEST FAILED */
/* ******************* */
function failHandler(r, s) {
    notifyUserError(
        "A system error occurred while trying to submit the files.\n\n" +
        r.status +
        ": " +
        r.statusText +
        '.  Please notify the CFTS administrators of this error. Contact info can be found by clicking "Contact Us" at the bottom of the page.'
    );

    // re-enable the submit button
    $('#submitButton').prop('disabled', false);
}



/* ***************************************************************** */
/* THE ROOT FORM PROCESSING FUNCTION (EVERYTHING ELSE SUPPORTS THIS) */
/* ***************************************************************** */
function process(e) {
    preventDefaults(e);

    if (userBanned != "True") {
        // disable the submit button once clicked, prevent duplicate submissions from multi clicks
        $('#submitButton').prop('disabled', true);

        let isValid = validateForm(xferForm);

        if (isValid) {
            // Give user feedback that the submit action occurred and things are happening
            notifyUserSuccess(
                "Submitting the request now. This could take up to a few minutes depending upon the size of the files being transferred. Please stand by ... "
            );

            // give it a quick refresh
            updateFileInfo();

            let prepData = prepareFormData(xferForm);


            //Add the CSRF token to ajax requests
            $.ajaxSetup({
                beforeSend: function(xhr, settings) {
                    xhr.setRequestHeader("X-CSRFToken", getCookie("csrftoken"));
                },
            });


            ajaxSettings = {
                url: "api-processrequest",
                method: "POST",
                data: prepData,
                contentType: false,
                processData: false,
            };
            $.ajax(ajaxSettings).done(successHandler).fail(failHandler);
        } else {
            console.log("Request Process Canceled");

            // notify the user there were validation errors
            notifyUserWarning("There are errors on the request form.  Please review and address the indicated fields.");

            // re-enable the submit button
            $('#submitButton').prop('disabled', false);
        }

    }
}