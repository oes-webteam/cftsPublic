/* transfer-request.js */
jQuery( document ).ready( function() {
  
  $( '.btn-back' ).click( e => {  
    e.preventDefault();
    window.location.href = jQuery( e.target ).attr( 'href' ); 
  });

});