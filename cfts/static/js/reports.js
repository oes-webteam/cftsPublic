// NO DOM DEPENDENCIES
function getCookie(name) {
  let cookie = {};
  document.cookie.split(';').forEach(function(el) {
    let [k,v] = el.split('=');
    cookie[k.trim()] = v;
  })
  return cookie[name];
}

$.ajaxSetup({ 
  beforeSend: function( xhr, settings ) {
    xhr.setRequestHeader("X-CSRFToken", getCookie('csrftoken'));
  } 
});

window.document.title = "CFTS -- Analyst Reports";


// HAS DOM DEPENDENCIES
$( document ).ready( function( ) {

  const runNumbers = ( e ) => {
    let start = $( "#numbersStartDate" ).val();
    let end = $( "#numbersEndDate" ).val();
    let isValid = () => {
      if( 
        start.length > 0
        && end.length > 0
        && Date.parse( start ) <= Date.parse( end )
      ) 
        return true;
      else 
        return false;
    };

    if( isValid() ) {
      let url = "/api-numbers";
      let data = { 'start_date': start, 'end_date': end };

      $.post( url, data, 'json' ).then( 
        // ajax request succeeded
        ( resp ) => {
          $( '#reviewed' ).text( resp.files_reviewed );
          $( '#transfered' ).text( resp.files_transfered );
          $( '#centcom' ).text( resp.centcom );
          $( '#rejected' ).text( resp.files_rejected );
          $( '.col.results' ).show();
        }, 
        // ajax request failed
        ( resp, status ) => {
          console.dir( status, resp );
        } 
      );

    }
  };
  $( 'input.xfer-numbers' ).datepicker({ format: 'mm/dd/yyyy' }).change( runNumbers );

});
