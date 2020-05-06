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
  $( ".datepicker" ).datepicker();

  // filtering
  function applyFilters() {
    $( ".data-row" ).show();    
   
    $( '.filter' ).each( function() {
      $thisFilter = $( this );      

      if( $thisFilter.val() ) {

        switch( $thisFilter.attr( 'name' ) ) {
          case "filterUser":
            $( ".xfer-user" ).each( function() {
              $thisCell = $( this );
              if( !$thisCell.text().toUpperCase().includes( $thisFilter.val().toUpperCase() ) ) 
                 $thisCell.parent( ".data-row" ).hide();
            });
            break;
          
          case "filterDate":
            $( ".xfer-date" ).each( function() {
              $thisCell = $( this );
              if( !$thisCell.text().includes( $thisFilter.val() ) ) 
                 $thisCell.parent( ".data-row" ).hide();
            });
            break;

          case "filterNet":
            $( ".xfer-net" ).each( function() {
              $thisCell = $( this );
              if( $thisCell.text().toUpperCase() != $thisFilter.val().toUpperCase() )
                $thisCell.parent( ".data-row" ).hide();
            });
            break;

          case "filterFiles":
            $( ".xfer-files" ).each( function() {
              $thisCell = $( this );
              if( !$thisCell.html().toUpperCase().includes( $thisFilter.val().toUpperCase() ) ) 
                 $thisCell.parent( ".data-row" ).hide();
            });
            break;

          case "filterEmail":
            $( ".xfer-email" ).each( function() {
              $thisCell = $( this );
              if( !$thisCell.html().toUpperCase().includes( $thisFilter.val().toUpperCase() ) ) 
                 $thisCell.parent( ".data-row" ).hide();
            });
            break;

          case "filterPull":
            $( ".xfer-pull" ).each( function() {
              $thisCell = $( this );
              if( !$thisCell.html().toUpperCase().includes( $thisFilter.val().toUpperCase() ) ) 
                 $thisCell.parent( ".data-row" ).hide();
            });
            break;

          default:
            $.noop();
        } // end switch
      } // end if( $thisFilter has value )
    }); // end .each()
  } // end applyFilters


  // apply filtering 
  $( "input.filter" ).debounce( function( e ) {
    if( $( e.target ).val() != "" )
      $( e.target ).addClass( 'filter-active' );
    else 
      $( e.target ).removeClass( 'filter-active' );

    applyFilters();
  });

  $( '.datepicker' ).change( function( e ) {
    if( $( e.target ).val() != "" )
      $( e.target ).addClass( 'filter-active' );
    else 
      $( e.target ).removeClass( 'filter-active' );

    applyFilters();
  });

  $( 'select.filter' ).change( function( e ) {
    if( $( e.target ).val() != "" )
      $( e.target ).addClass( 'filter-active' );
    else 
      $( e.target ).removeClass( 'filter-active' );

    applyFilters();
  });




  // create the dialog (modal) object
  userDialog = $( '#user-modal' ).dialog({
    autoOpen: false,
    height: 400,
    width: 350,
    modal: true,
    buttons: {
      "View Requests": function() { 
        filterArchive( $(this).data( 'user_id' ) );
      },
      "Email User": function() {

      },
      Close: () => userDialog.dialog( 'close' )
    },
    close: () => {}
  });

  // You clicked a user link.  Huzzah!  Now here's what were gonna do ...
  $( 'a.user' ).click( e => {
    e.preventDefault();
    const data = {};
    const url = '/api-getuser/' + e.target.id;
    $.get( url, ( resp ) => {
      $( '#name' ).text( resp.first_name + ' ' + resp.last_name );
      $( '#email' ).text( resp.email );
    });
    userDialog.dialog( 'open' );

  });

});