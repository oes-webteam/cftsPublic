/* analysts.js */

// utility function
function str2bytes (str) {
    var bytes = new Uint8Array(str.length);
    for (var i=0; i<str.length; i++) {
       bytes[i] = str.charCodeAt(i);
     }
     return bytes;
 }


jQuery( document ).ready( function() {
    $( '.pull-button' ).click( e => {
        e.preventDefault();
        pullBtn = $( e.target );
        buttonID = pullBtn.attr( 'id' );
        netName = buttonID.substr( 4 );
        let url = '/create-zip/' + netName;
        
        if( $( e.target ).hasClass( 'disabled' ) ) {
          alert( 'There are no pending transfer requests to pull for this network.' )
        } else {
          $.get( url, {}, ( resp, status ) => {
              if( status == 'success' ) { 
                // TODO: AJAX success != pull success
                // display success to the user
                alert( 'Pull complete. New ZIP file created for ' + netName + '.  Click the download button to retrieve it.' );
                
                // prevent a second pull
                pullBtn.addClass( 'disabled' );

                // update link on page to avoid unnecessary refresh 
                downloadBtn = $( '#dl' + netName );
                downloadBtn.attr( 'href', '/static/files/' + netName + '_' + resp.pullNumber + '.zip' );
                downloadBtn.focus().blur().focus().blur().focus();

                // update last pulled info
                $( '.last-pull-info .date-pulled' ).text( resp.datePulled );
                $( '.last-pull-info .user-pulled' ).text( resp.userPulled );

              } else {
                  console.error( 'Shit broke, yo.' );
              }
          });
        }

    });

});