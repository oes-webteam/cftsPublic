/* transfer-request.js */
window.document.title = "Request Info";

jQuery( document ).ready( function() {

  $.ajaxSetup({ 
    beforeSend: function( xhr, settings ) {
      xhr.setRequestHeader("X-CSRFToken", getCookie('csrftoken'));
    } 
   });
  
  $( '.btn-back' ).click( e => {  
    e.preventDefault();
    window.location.href = jQuery( e.target ).attr( 'href' ); 
  });

  $( '#noteBtn' ).click( e => {  
    e.preventDefault();
    data = {
      'notes': $('#notesField').val()
    }


    $.post("/api-requestnotes/"+ rqst_id , data, 'json').then(
      function (resp) {
        alert("Notes saved")
        window.location.replace(window.location)
      },
    ); 
  });

});