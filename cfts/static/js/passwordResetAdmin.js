jQuery( document ).ready( function() {
  
  $.ajaxSetup({ 
    beforeSend: function( xhr, settings ) {
      xhr.setRequestHeader("X-CSRFToken", getCookie('csrftoken'));
    } 
  });

  $('.generateButton').click(e => {
    let csrftoken = getCookie('csrftoken');

    let url = '/password-reset-email/' + $(e.currentTarget).attr('userID') + "/" + $(e.currentTarget).attr('feedbackID')

    const setRejectOnFiles = $.post( url, 'json' ).then(
      // success
      function( resp ) {      
        // create mailto anchor
        let $anchor = $( "<a class='emailLink' target='_blank' href='" + resp + "'></a>" );
        $( document.body ).append( $anchor );

        $( '.emailLink' ).each( function() { $(this)[0].click(); } );  

        // reload the page from server
        $( "#forceReload" ).submit();

      },
    );
  })

});