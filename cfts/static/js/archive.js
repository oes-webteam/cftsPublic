jQuery( document ).ready( function() {

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