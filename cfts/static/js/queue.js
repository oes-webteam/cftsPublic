window.document.title = "CFTS -- Transfer Queue";

// ADD SHIFT-CLICK SELECTION
function enableGroupSelection( selector ) {
  let lastChecked = null;
  const checkboxes = Array.from( document.querySelectorAll( selector ) );

  checkboxes.forEach( checkbox => checkbox.addEventListener( 'click', event => {
    if ( !lastChecked ) {
      lastChecked = checkbox;
      checkbox.nextElementSibling.style.display = 'inline-block';
      return;
    }

    if ( event.shiftKey ) {
      const start = checkboxes.indexOf( checkbox );
      const end   = checkboxes.indexOf( lastChecked );
      checkboxes
        .slice( Math.min( start, end ), Math.max( start, end ) + 1 )
        .forEach( checkbox => checkbox.checked = lastChecked.checked );
    }

    // match reject buttons to checkboxes on each click
    checkboxes.forEach( checkbox => checkbox.nextElementSibling.style.display = ( checkbox.checked ) ? 'inline-block' : 'none' );

    lastChecked = checkbox;
  }));
}

/*************************/
/* THE REAL FUN BEGINS!! */
/*************************/
jQuery( document ).ready( function() {
  
  $.ajaxSetup({ 
    beforeSend: function( xhr, settings ) {
      xhr.setRequestHeader("X-CSRFToken", getCookie('csrftoken'));
    } 
   });

  // PULL BUTTON CLICK HANDLER
  $( '.pull-button' ).click( e => {
    e.preventDefault();
    pullBtn = $( e.target );
    buttonID = pullBtn.attr( 'id' );
    netName = buttonID.substr( 4 );
    if(pullBtn.hasClass('centcom')){
      isCentcom = "True"
    }
    else{
      isCentcom = "False"
    }
    let url = '/create-zip/' + netName +'/'+ isCentcom;
    
    if( $( e.target ).hasClass( 'disabled' ) ) {
      alert( 'There are no pending transfer requests to pull for this network.' )
    } else {
      $.get( url, {}, ( resp, status ) => {
        if( status == 'success' ) { 
          // TODO: AJAX success != pull success
          // display success to the user
          alert( 'Pull complete. New ZIP file created for ' + netName + '.  Click the download button to retrieve it.' );
          
          // prevent a second pull
          //pullBtn.addClass( 'disabled' );
          $('.pull-button').addClass('disabled');

          // update link on page to avoid unnecessary refresh 
          downloadBtn = $( '#dl' + netName );
          downloadBtn.attr( 'href', '/static/files/' + netName + '_' + resp.pullNumber + '.zip' );
          downloadBtn.text('Download Current '+ netName + ' Zip')
          downloadBtn.attr('hidden', false);
          downloadBtn.focus();

          // update last pulled info
          $( '.last-pull-info .date-pulled' ).text( resp.datePulled );
          $( '.last-pull-info .user-pulled' ).text( resp.userPulled );

          $( "#forceReload" ).submit();

        } else {
            console.error( 'Shit broke, yo.' );
        }
      });
    }
  });
  
  // REJECT BUTTON CLICK HANDLER
  $( '.btn-reject' ).click( e => {
    e.preventDefault();
    const data = [{ 
      'fileID': e.target.id.slice(4), 
      'fileName': $( e.target ).attr( 'file_name' ),
      'requestID': $( e.target ).attr( 'request_id' ),
      'requestEmail': $( e.target ).attr( 'request_email' )
    }];
    rejectDialog.data( 'data', data ).dialog( 'open' );
  });

  // MULTI-REJECT CLICK HANDLER
  $( '.btn-reject-selected' ).click( e => {
    e.preventDefault();
    const $checkedItems = $( "[name='fileSelection']:checked" );
    let data = [];
    $checkedItems.each( i => {
      data.push({ 
        'fileID': $checkedItems[i].id.slice(4), 
        'fileName': $( $checkedItems[i] ).attr( 'file_name' ),
        'requestID': $( $checkedItems[i] ).attr( 'request_id' ),
        'requestEmail': $( $checkedItems[i] ).attr( 'request_email' )
      }) 
    });
    rejectDialog.data( 'data', data ).dialog( 'open' );
  });

  // REJECTION MODAL DEFINITIONS (POPUP)
  const checkSelection = ( selector ) => {
    let $ele = $( selector );
    if( $ele.val().length == 0 ) {
      $ele.addClass( 'ui-state-error' );
      alert( $ele.attr( 'name') + ' cannot be blank.' );
      return false;
    } else {
      return true;
    }
  };

  // REJECTION MODAL INPUT VALIDATION AND ACTION
  const rejectFormCallback = ( theDialog ) => {
    // user input validation
    let isValid = true;
    isValid = isValid && checkSelection( "[name='reason']" );
    
    /* THE REAL WORK GOES HERE */
    if ( isValid ) {
      let data = $( theDialog ).data().data;
      
      let $this = $( "[name='reason'] option:selected" );
      let requests = {};
      
      let csrftoken = getCookie('csrftoken');

      let id_list = [];
      data.forEach( ( f ) => {
        id_list.push( f.fileID ) 
       });

      const postData = {
        'reject_id': $this.val(),
        'request_id': data[0]['requestID'],  // doesn't matter which request we grab
        'id_list': id_list
      };

      const setRejectOnFiles = $.post( '/api-setreject', postData, 'json' ).then( 
        // success
        function( resp ) {
          // console.log( 'SUCCESS' );
          // console.log( 'Server response: ' + resp );
        },
        // fail 
        function( resp, status ) {
          // console.log( 'FAIL' );
          // console.log( 'Server response: ' + resp );
          // console.log( 'Response status: ' + status );
        }
      );

      // sort files back into their own requests
      data.forEach( ( selectedFile ) => {
        if ( !( selectedFile.requestID in requests ) )
          requests[ selectedFile.requestID ] = { 
            'email': selectedFile.requestEmail,
            'files': [{ 'id': selectedFile.fileID, 'name': selectedFile.fileName }]
          };
        else
          requests[ selectedFile.requestID ].files.push( { 'id': selectedFile.fileID, 'name': selectedFile.fileName } );
      });

      let reject = 0
      // for each request ...
      for( r in requests ) {
        const email = requests[r].email;
        let subject = $this.attr( 'data-subject' );
        let body = $this.attr( 'data-text' );

        // replace template variables in the body of the email
        let filesList = "";
        requests[r].files.forEach( ( i ) => {
          filesList += "  - " + i.name + "<br>";
        });
        body = body.replace( '^files^', filesList );
        body = body.replace( /<br>/g, '%0A' );

        // ... create an email with that user's files
        let $anchor = $( "<a class='emailLink" + reject + "' target='_blank' href='mailto:" + email + "?subject=" + subject + "&body=" + body + "'></a>" );
        $( document.body ).append( $anchor );
        window.open($('.emailLink'+reject).attr('href'),"reject"+reject)
        reject++;
      }

      //$( '.emailLink' ).each( function() { $(this)[0].click(); } );  
     
      // close the dialog
      $( theDialog ).dialog( 'close' );
      
      // reload the page from server
      $( "#forceReload" ).submit();

    } else {
      /* bad user, no cookie */
      console.log( "What did you do, Ray?" );
    }
  };

  const rejectDialog = $( '#reject-form' ).dialog({
    autoOpen: false,
    height: 200,
    width: 350,
    modal: true,
    buttons: {
      "Reject Files": function() { 
        let theDialog = this;
        rejectFormCallback( theDialog );
      },
      Cancel: () => rejectDialog.dialog( 'close' )
    },
    close: () => { 
      rejectForm[0].reset();
      $( "[name='reason']" ).removeClass( 'ui-state-error' );
    }
  });

  const rejectForm = rejectDialog.find( 'form' ).submit( e => {
    e.preventDefault();
    rejectFormCallback( rejectDialog );
  })

  const showComments = ( e ) => {
    e.preventDefault();
    $this = $( e.target );
    $this.parents( "tr" ).next().find( ".comments-text div" ).slideToggle( "fast" );
  };
  $( ".btn.comments" ).click( showComments );


  // RUN THIS STUFF NOW THAT THE PAGE IS LOADED
  enableGroupSelection( 'input[type="checkbox"]' )

});