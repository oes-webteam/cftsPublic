/* process.js */
/* validate and process the transfer request form */

xferForm = document.querySelector( "#transfer-request-form" );
xferForm.addEventListener( 'submit', process, false );

function validateForm( form ) {
  let thisNet = 'SIPR';
  let isValid = true;
  let errors = [];

  // name
  if( !(form.elements.firstName.value.length || form.elements.lastName.value.length) ) {
    errors.push( form.elements.firstName, form.elements.lastName );
    isValid = false;
  }
  
  // source email
  if( !(form.elements.userEmail.value.length || checkEmail( form.elements.userEmail.value, thisNet ) ) ) {
    errors.push( form.elements.userEmail );
    isValid = false;
  }

  // file queue
  if( !fileQueue.length ) {
    errors.push( form.elements[ "files[]" ], document.querySelector( "#drop-zone" ) );
    isValid = false;
  }

  // target network
  if( !form.elements.network.value.length ) {
    errors.push( form.elements.network );
    isValid = false;
  }

  // target email
  if(  ) {
    isValid = false;
  }

  if( !isValid ) {
    // mark the naughty-naughties
    errors.forEach( function( elem ) {
      elem.setAttribute( "required", "required" );
    });
    form.classList.add( "was-validated" )
  }
  
  return isValid;

}

function preparePost() {}
function successHandler() {}
function failHandler() {}

function process( e ) {
  preventDefaults( e );

  // Give user feedback that the submit action occurred and things are happening
  
  let isValid = validateForm( xferForm );

  if( isValid ) {
    data = preparePost();

    $.ajax( data ).then(
      successHandler( resp ),
      failHandler( resp, status )
    );

  } else {
    // rollback and notify the user of errors

  }

}