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
    let url = '/create-zip/' + netName +'/'+ isCentcom+'/false';
    
    if( $( e.target ).hasClass( 'disabled' ) ) {
      if( $(e.target).hasClass('centcom') ){
      alert( 'There are no pending CENTCOM transfer requests to pull for this network.' )
      }
      else{
      alert( 'There are no pending transfer requests to pull for this network.' )
      }

    } else {
      $('.pull-button').prop('disabled', true);

      $.get( url, {}, 'json').then(
	function(resp, status){
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
	  notifyUserSuccess("Pull Created Successfully")

          $( "#forceReload" ).submit();

        }, 

	function(resp, status){
            console.error( 'Shit broke, yo.' );
	    alert("Failed to create pull, send error message to web team.")
            responseText = resp.responseText
	    errorInfo = responseText.substring(resp.responseText.indexOf("Exception Value"), resp.responseText.indexOf("Python Executable"))

	    notifyUserError("Error Creating Pull, send error message to web team:  " + errorInfo)
        }
      );
    }
  });

  $('.request-reject').click(e => {
    e.preventDefault();

    if($(e.target).hasClass('selected-reject')){
      console.log("selcted reject clicked")

      const $checkedItems = $( "[name='fileSelection']:checked[request_id='"+$( e.target ).attr('request_id')+"'][not-rejected]");
      const $checkedItemsRejected = $( "[name='fileSelection']:checked[request_id='"+$( e.target ).attr('request_id')+"'][rejected]");

      // no files selected to reject or un-reject
      if ($checkedItems.length == 0 && $checkedItemsRejected.length == 0){
        alert( 'Select 1 or more files to change rejection status.' );
      }

      // selected files are a mix of rejected and not rejected files
      else if ($checkedItems.length > 0 && $checkedItemsRejected.length > 0){
        alert( 'Cannot process a mix of rejected and non-rejected files. Rejection and un-rejection are seperate processes. Please select only files to reject or only files to un-reject.' );
      }

      // files to reject
      else if ($checkedItems.length > 0){
        console.log("not rejected yet")
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
      }

      //files to un-reject
      else if ($checkedItemsRejected.length > 0){
        console.log("already rejected")
          let data = [];
          $checkedItemsRejected.each( i => {
            data.push({ 
              'fileID': $checkedItemsRejected[i].id.slice(4), 
              'fileName': $( $checkedItemsRejected[i] ).attr( 'file_name' ),
              'requestID': $( $checkedItemsRejected[i] ).attr( 'request_id' ),
              'requestEmail': $( $checkedItemsRejected[i] ).attr( 'request_email' ),
        'unreject': true
            }) 
          });
        sendUnrejectRequest(data)
        }
        
    }

    else{
      console.log("request reject clicked")
      const checkboxes = Array.from( document.querySelectorAll( 'input[type="checkbox"][request_id="'+$( e.target ).attr('request_id')+'"]' ) );
      checkboxes.forEach( checkbox =>{
        checkbox.removeAttribute("hidden");
      });
  
      $(e.target).text("Reject Selected")
      $(e.target).addClass('selected-reject')
    }

  });

const sendUnrejectRequest = (data) => {
    console.log(data);

    let csrftoken = getCookie('csrftoken');

    let id_list = [];
      data.forEach( ( f ) => {
        id_list.push( f.fileID ) 
       });

      const postData = {
        'request_id': data[0]['requestID'],  // doesn't matter which request we grab
        'id_list': id_list
      };

      const setUnrejectOnFiles = $.post( '/api-unreject', postData, 'json' ).then( 
        // success
        function( resp, status ) {
           console.log( 'SUCCESS' );        
           notifyUserSuccess("File Unreject Successful")
	   $( "#forceReload" ).submit();
        },
        // fail 
        function( resp, status ) {
           console.log( 'FAIL' );

	   alert("Failed to unreject files, send error message to web team.")
	   responseText = resp.responseText
	   errorInfo = responseText.substring(resp.responseText.indexOf("Exception Value"), resp.responseText.indexOf("Python Executable"))

           notifyUserError("Error unrejecting file, send error message to web team: " + errorInfo)
           //console.log( 'Server response: ' + JSON.stringify(resp,null, 4));
          // console.log( 'Response status: ' + status );
        }
      );
    
  };


  /****************************/
  /* Encrypt files in request */
  /****************************/

  $('.request-encrypt').click(e => {
    e.preventDefault();

    if($(e.target).hasClass('selected-encrypt')){
      console.log("selcted encrypt clicked")

      const $checkedItems = $( "[name='fileSelection']:checked[request_id='"+$( e.target ).attr('request_id')+"']");

      if ($checkedItems.length == 0){
        alert( ' Select 1 or more files to encrypt.' );
      }
      
      else{
        let data = [];
      $checkedItems.each( i => {
        data.push({ 
          'fileID': $checkedItems[i].id.slice(4), 
          'fileName': $( $checkedItems[i] ).attr( 'file_name' ),
          'requestID': $( $checkedItems[i] ).attr( 'request_id' ),
          'requestEmail': $( $checkedItems[i] ).attr( 'request_email' )
        }) 
      });
	sendEncryptRequest(data)
      }
      
    }

    else{
      console.log("request encrypt clicked")
      const checkboxes = Array.from( document.querySelectorAll( 'input[type="checkbox"][request_id="'+$( e.target ).attr('request_id')+'"]' ) );
      checkboxes.forEach( checkbox =>{
        checkbox.removeAttribute("hidden");
      });
  
      $(e.target).text("Encrypt Selected")
      $(e.target).addClass('selected-encrypt')
    }

  });

  const sendEncryptRequest = (data) => {
    console.log(data);

    let csrftoken = getCookie('csrftoken');

    let id_list = [];
      data.forEach( ( f ) => {
        id_list.push( f.fileID ) 
       });

      const postData = {
        'request_id': data[0]['requestID'],  // doesn't matter which request we grab
        'id_list': id_list
      };

      const setEncryptOnFiles = $.post( '/api-setencrypt', postData, 'json' ).then( 
        // success
        function( resp, status ) {
           console.log( 'SUCCESS' );        
           notifyUserSuccess("File Encryption Successful")
	   $( "#forceReload" ).submit();
        },
        // fail 
        function( resp, status ) {
           console.log( 'FAIL' );

	   alert("Failed to encrypt files, send error message to web team.")
	   responseText = resp.responseText
	   errorInfo = responseText.substring(resp.responseText.indexOf("Exception Value"), resp.responseText.indexOf("Python Executable"))

           notifyUserError("Error encrypting file, send error message to web team: " + errorInfo)
           //console.log( 'Server response: ' + JSON.stringify(resp,null, 4));
          // console.log( 'Response status: ' + status );
        }
      );
    
  };




/***************************/
/* Show duplicate requests */
/***************************/

  $('.show-dupe').click(e => {
    e.preventDefault();

    if($(e.target).hasClass('dupes-visable')){
      console.log("hide dupes")

      const dupes = Array.from( document.querySelectorAll( 'tr[request_hash="'+$( e.target ).attr('request_hash')+'"]' ) );
      dupes.forEach( dupe =>{
        dupe.classList.remove("dupe");
      });

      $(e.target).text("Show Duplicates")
      $(e.target).removeClass('dupes-visable')
     
      
    }

    else{
      console.log("show dupes")
      const dupes = Array.from( document.querySelectorAll( 'tr[request_hash="'+$( e.target ).attr('request_hash')+'"]') );
      dupes.forEach( dupe =>{
        dupe.classList.add("dupe");
      });
  
      $(e.target).text("Hide Duplicates")
      $(e.target).addClass('dupes-visable')
    }

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
           console.log( 'SUCCESS' );
           notifyUserSuccess("File rejection Successful")
           console.log( 'Server response: ' + JSON.stringify(resp,null, 4));

      // download eml file
      let $anchor = $( "<a class='emailLink' target='_blank' href='/api-geteml/"+ resp.emlName +"'></a>" );
      $( document.body ).append( $anchor );
      window.open($('.emailLink').attr('href'))

      // close the dialog
      $( theDialog ).dialog( 'close' );
      
      // reload the page from server
      $( "#forceReload" ).submit();

        },
        // fail 
        function( resp, status ) {
	   // close the dialog
           $( theDialog ).dialog( 'close' );
	   alert("Failed to reject files, send error message to web team.")

           console.log( 'FAIL' );
	   responseText = resp.responseText
	   errorInfo = responseText.substring(resp.responseText.indexOf("Exception Value"), resp.responseText.indexOf("Python Executable"))

           notifyUserError("Error rejecting file, send error message to web team: " + errorInfo)
           //console.log( 'Server response: ' + JSON.stringify(resp,null, 4));
          // console.log( 'Response status: ' + status );
        }
      );

      

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