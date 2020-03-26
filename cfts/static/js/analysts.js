/* analysts.js */
jQuery( document ).ready( function() {
    $( '.pull-button' ).click( e => {
        e.preventDefault();
        buttonID = $( e.target ).attr( 'id' );
        netName = buttonID.substr( 4 );
        let url = '/create-zip/' + netName;
        $.get( url, {}, ( resp, status ) => {
            if( status == 'success' ) { 
                let file = URL.createObjectURL( resp );
                window.open( file );
            } else {
                console.error( 'Shit broke, yo.' );
            }
        });
    });
});