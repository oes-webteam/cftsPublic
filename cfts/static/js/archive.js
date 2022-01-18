window.document.title = "CFTS -- Transfer Archive";

/* delayed onchange while typing jquery for text boxes widget
This code was shamelessly harvested from StackOverflow user AntonK and then modified

usage:
    $("#SearchCriteria").debounce(function ( event ) {
        DoMyAjaxSearch();
    });

*/

(function($) {
    $.fn.debounce = function(options) {
        var timer;
        var o;

        if (jQuery.isFunction(options)) {
            o = {
                onChange: options
            };
        } else {
            o = options;
        }

        o = $.extend({}, $.fn.debounce.defaultOptions, o);

        return this.each(function() {
            var element = $(this);
            element.keyup(function(event) {
                clearTimeout(timer);
                timer = setTimeout(function() {
                    var newVal = element.val();
                    newVal = $.trim(newVal);
                    if (element.debounce.oldVal != newVal) {
                        element.debounce.oldVal = newVal;
                        o.onChange.call(this, event);
                    }
                }, o.delay);
            });
        });
    };

    $.fn.debounce.defaultOptions = {
        delay: 300,
        onChange: function(event) {}
    }

    $.fn.debounce.oldVal = "";
})(jQuery);


jQuery(document).ready(function() {
    // activate datepicker fields
    $(".datepicker").datepicker({
        dateFormat: "yy-mm-dd"
    });

    // filtering
    function applyFilters() {
        $(".data-row").show();
        let data = {
            'userFirst': "",
            'userLast': "",
            'date': "",
            'network': "",
            'files': "",
            'email': "",
            'pull': "",
            'org': ""
        }
        $('.filter').each(function() {
            $thisFilter = $(this);

            if ($thisFilter.val()) {

                switch ($thisFilter.attr('name')) {
                    case "filterUserFirst":
                        let userFirst = $thisFilter.val()
                        data.userFirst = userFirst;
                        break;

                    case "filterUserLast":
                        let userLast = $thisFilter.val()
                        data.userLast = userLast;
                        break;

                    case "filterDate":
                        let date = $thisFilter.val()
                        data.date = date
                        break;

                    case "filterNet":
                        let network = $thisFilter.val()
                        data.network = network
                        break;

                    case "filterFiles":
                        let files = $thisFilter.val()
                        data.files = files
                        break;

                    case "filterEmail":
                        let email = $thisFilter.val()
                        data.email = email
                        break;

                    case "filterPull":
                        let pull = $thisFilter.val()
                        data.pull = pull
                        break;

                    case "filterOrg":
                        let org = $thisFilter.val()
                        data.org = org
                        break;

                    default:
                        $.noop();
                } // end switch
            } // end if( $thisFilter has value )


        }); // end .each()
        return data;
    } // end applyFilters


    function getRequests() {
        data = applyFilters()

        console.log(data)

        if ([...new Set(Object.values(data))].length == 1) {
            window.location.href = "/archive"
        } else {
            //Add the CSRF token to ajax requests
            $.ajaxSetup({
                beforeSend: function(xhr, settings) {
                    xhr.setRequestHeader("X-CSRFToken", getCookie("csrftoken"));
                },
            });

            $.ajax({
                type: "POST",
                url: "/filterArchive",
                data: data,
                success: function(response) {
                    $("#templateTable").html(response)
                }
            });
        }
    }

    $("#submit-button").click(function(e) {
        e.preventDefault();
        getRequests();
    });

    $(".filter").keypress(function(e) {
        if (e.which == 13) {
            getRequests();

        }
    });

});