window.document.title = "Drop Zone";
dropForm = document.getElementById("dropForm")
dropArea = document.getElementById("drop-zone")
filesInput = document.getElementById("uploadButton")

if (document.location.search) {
    const search = document.location.search
    const params = new URLSearchParams(search);
    let paramObj = {};
    for (var value of params.keys()) {
        paramObj[value] = params.get(value);
    }

    if (paramObj.eml) {

        let eml = paramObj.eml + "&body=" + paramObj.body
        let $anchor = $("<a class='banEmailLink' target='_blank' href='" + eml.replace(/<br>/g, "%0D%0A%0D%0A") + "''></a>");
        $(document.body).append($anchor);

        $('.banEmailLink').each(function() {
            $(this)[0].click();
        });

        history.pushState(null, "", location.href.split("?")[0])
    }
}

$.ajaxSetup({
    beforeSend: function(xhr, settings) {
        xhr.setRequestHeader("X-CSRFToken", getCookie("csrftoken"));
    }
})

const submitDrop = function(e) {
    var data = new FormData()
    if ('dataTransfer' in e) {
        file = e.dataTransfer.files[0];
        data.append('dropZip', file);
    } else if ('target' in e) {
        file = e.target.files[0];
        data.append('dropZip', file);
    }

    $.ajax({
        url: '/process-drop',
        data: data,
        cache: false,
        contentType: false,
        processData: false,
        method: 'POST',
        type: 'POST',
        success: function(resp) {
            console.log(resp)
            window.location = window.location
        },
        error: function(resp) {
            console.log(resp)
            window.location = window.location
        }
    })
}
addHighlight = (e) => dropArea.classList.add('highlight-active');
removeHighlight = (e) => dropArea.classList.remove('highlight-active');

// prevent default actions for all these events
['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
    dropArea.addEventListener(eventName, preventDefaults, false);
});

// add/remove highlighting to/from drop zone
['dragenter', 'dragover'].forEach(eventName => {
    dropArea.addEventListener(eventName, addHighlight, false);
});
['dragleave', 'drop'].forEach(eventName => {
    dropArea.addEventListener(eventName, removeHighlight, false);
});

// the add files handler for the drop zone and file field
dropArea.addEventListener('click', function() {
    $('#uploadButton').click()
}, false);
dropArea.addEventListener('drop', submitDrop, false);
filesInput.addEventListener('change', submitDrop, false);