window.document.title = "CFTS -- Transfer Archive";

/* delayed onchange while typing jquery for text boxes widget
This code was shamelessly harvested from StackOverflow user AntonK and then modified

usage:
    $("#SearchCriteria").debounce(function ( event ) {
        DoMyAjaxSearch();
    });

*/

(function ($) {
  $.fn.debounce = function (options) {
    var timer;
    var o;

    if ( jQuery.isFunction( options ) ) { 
      o = { onChange: options }; 
    } else { o = options; }

    o = $.extend({}, $.fn.debounce.defaultOptions, o);

    return this.each( function () {
      var element = $( this );
      element.keyup( function ( event ) {
        clearTimeout( timer );
        timer = setTimeout( function () {
          var newVal = element.val();
          newVal = $.trim( newVal );
          if ( element.debounce.oldVal != newVal ) {
            element.debounce.oldVal = newVal;
            o.onChange.call( this, event );
          }
        }, o.delay);
      });
    });
  };

  $.fn.debounce.defaultOptions = {
      delay: 300,
      onChange: function ( event ) { }
  }

  $.fn.debounce.oldVal = "";
})(jQuery);


jQuery( document ).ready( function() {
  // activate datepicker fields
  $( ".datepicker" ).datepicker({dateFormat: "yy-mm-dd"});

  // filtering
  function applyFilters() {
    $( ".data-row" ).show();
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
    $( '.filter' ).each( function() {
      $thisFilter = $( this );      

      if( $thisFilter.val() ) {

        switch( $thisFilter.attr( 'name' ) ) {
          case "filterUserFirst":
            // $( ".xfer-user" ).each( function() {
            //   $thisCell = $( this );
            //   if( !$thisCell.text().toUpperCase().includes( $thisFilter.val().toUpperCase() ) ) 
            //      $thisCell.parent( ".data-row" ).hide();
            // });
            let userFirst = $thisFilter.val()
            data.userFirst = userFirst;
            break;

          case "filterUserLast":
            // $( ".xfer-user" ).each( function() {
            //   $thisCell = $( this );
            //   if( !$thisCell.text().toUpperCase().includes( $thisFilter.val().toUpperCase() ) ) 
            //      $thisCell.parent( ".data-row" ).hide();
            // });
            let userLast = $thisFilter.val()
            data.userLast = userLast;
            break;
          
          case "filterDate":
            // $( ".xfer-date" ).each( function() {
            //   $thisCell = $( this );
            //   if( !$thisCell.text().includes( $thisFilter.val() ) ) 
            //      $thisCell.parent( ".data-row" ).hide();
            // });
            let date = $thisFilter.val()
            data.date = date
            break;

          case "filterNet":
            // $( ".xfer-net" ).each( function() {
            //   $thisCell = $( this );
            //   if( $thisCell.text().toUpperCase() != $thisFilter.val().toUpperCase() )
            //     $thisCell.parent( ".data-row" ).hide();
            // });
            let network = $thisFilter.val()
            data.network = network
            break;

          case "filterFiles":
            // $( ".xfer-files" ).each( function() {
            //   $thisCell = $( this );
            //   if( !$thisCell.html().toUpperCase().includes( $thisFilter.val().toUpperCase() ) ) 
            //      $thisCell.parent( ".data-row" ).hide();
            // });
            let files = $thisFilter.val()
            data.files = files
            break;

          case "filterEmail":
            // $( ".xfer-email" ).each( function() {
            //   $thisCell = $( this );
            //   if( !$thisCell.html().toUpperCase().includes( $thisFilter.val().toUpperCase() ) ) 
            //      $thisCell.parent( ".data-row" ).hide();
            // });
            let email = $thisFilter.val()
            data.email = email
            break;

          case "filterPull":
            // $( ".xfer-pull" ).each( function() {
            //   $thisCell = $( this );
            //   if( !$thisCell.html().toUpperCase().includes( $thisFilter.val().toUpperCase() ) ) 
            //      $thisCell.parent( ".data-row" ).hide();
            // });
            let pull = $thisFilter.val()
            data.pull = pull
            break;

          case "filterOrg":
            // $( ".xfer-org" ).each( function() {
            //   $thisCell = $( this );
            //   if( !$thisCell.html().toUpperCase().includes( $thisFilter.val().toUpperCase() ) ) 
            //      $thisCell.parent( ".data-row" ).hide();
            // });
            let org = $thisFilter.val()
            data.org = org
            break;

          default:
            $.noop();
        } // end switch
      } // end if( $thisFilter has value )


    }); // end .each()
    return  data;
  } // end applyFilters


  $("#submit-button").click(function (e) { 
    e.preventDefault();
    data = applyFilters()

    console.log(data)
    console.log([...new Set(Object.values(data))].length)

    if([...new Set(Object.values(data))].length == 1){
      window.location.href = "/archive"
    }
    else{
    //Add the CSRF token to ajax requests
      $.ajaxSetup({
        beforeSend: function (xhr, settings) {
          xhr.setRequestHeader("X-CSRFToken", getCookie("csrftoken"));
        },
      });

      $.ajax({
        type: "POST",
        url: "/filterArchive",
        data: data,
        success: function (response) {
          $("#templateTable").html(response)
        }
      });
    }
  });

});