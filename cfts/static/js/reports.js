// NO DOM DEPENDENCIES
function getCookie(name) {
    let cookie = {};
    document.cookie.split(';').forEach(function (el) {
        let [k, v] = el.split('=');
        cookie[k.trim()] = v;
    });
    return cookie[name];
}

$.ajaxSetup({
    beforeSend: function (xhr, settings) {
        xhr.setRequestHeader("X-CSRFToken", getCookie('csrftoken'));
    }
});

window.document.title = "CFTS -- Analyst Reports";


// HAS DOM DEPENDENCIES
$(document).ready(function () {

    const runNumbers = async (e) => {
        console.log("runNumbers called");
        let start = $("#numbersStartDate").val();
        let end = $("#numbersEndDate").val();
        let staffUser = $("#numbersStaff option:selected").val();

        let isValid = () => {
            if (
                start.length > 0 &&
                end.length > 0 &&
                Date.parse(start) <= Date.parse(end)
            )
                return true;
            else
                return false;
        };

        if (isValid()) {
            let url = "/api-numbers";
            let data = {
                'start_date': start,
                'end_date': end,
                'staffUser': staffUser
            };

            postResult = await Promise.resolve(
                $.post(url, data, 'json').then(
                    // ajax request succeeded
                    (resp) => {

                        // $('#reviewed').text(resp.files_reviewed);
                        // $('#transfered').text((Math.round(resp.files_transfered / resp.files_reviewed * 100)) + "%)");
                        // $('#centcom').text(resp.centcom_files + " (" + (Math.round(resp.centcom_files / resp.files_reviewed * 100)) + "%)");
                        // $('#rejected').text(resp.files_rejected + " (" + (Math.round(resp.files_rejected / resp.files_reviewed * 100)) + "%)");

                        $('#resultsPartial').html(resp);
                        $('.col.results').show();

                    },
                    // ajax request failed
                    (resp, status) => {
                        console.dir(status, resp);
                    }
                )
            );

        }
    };
    $('input.xfer-numbers').datepicker({
        format: 'mm/dd/yyyy'
    });
    $('.datepicker').change(runNumbers);
    $('.staff').change(runNumbers);

});