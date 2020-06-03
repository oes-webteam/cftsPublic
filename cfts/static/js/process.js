/* *****************************************
  process.js -- 
  Validate the form inputs, 
  POST them to the server for processing, 
  and handle the response 
  ****************************************** */

xferForm = document.querySelector( "#transfer-request-form" );
xferForm.addEventListener( 'submit', process, false );

function checkEmail( email, net, direction ) {
  // look -- if it's not even a real email address, just kick it the eff out
  var emailRegex = /^\w+([\.-]?\w+)*@\w+([\.-]?\w+)*(\.\w{2,3})+$/;
  if( ! email.match( emailRegex ) ) return false;

  let domain = email.split( "@" ).pop();
  let domainArray = domain.split( "." );
  let check = "";
  switch( net ) {
    case 'NIPR':
      check = domainArray.pop();
      return domain.indexOf( 'smil' ) == -1 && domain.indexOf( 'cmil' ) == -1 && ( check == 'mil' || check == 'gov' ) ?  true : false;
    case 'SIPR':
      return domainArray.slice(-2).join( "." ) == 'smil.mil' ?  true : false;
    case 'CX-SWA':
      break;
    case 'BICES':
      switch( direction ) {
        case "from":
          return domainArray.slice(-2).join( "." ) == 'bices.org' ?  true : false;
        case "to":
          return domainArray.slice(-3).join( "." ) == 'us.bices.org' ? true : false;
        default:
          notifyUser( "ERROR: A system error has occurred. The 'checkEmail' function is being called in an impropper manner ('direction' == " + direction + "). Please notify the CFTS administrators of this error by emailing {{ SETTINGS.CFTS_ADMIN_EMAIL }}." );
          break;        
      }
    case 'CPN-X':
      break;
    case 'CPN-SAU':
      break;
    case 'CPN-JOR':
      break;
    default:
      if( net.length ) 
        notifyUser( "ERROR: A system error has occurred. The network " + net + " is not recognized by the 'checkEmail' function. Please notify the CFTS administrators of this error by emailing {{ SETTINGS.CFTS_ADMIN_EMAIL }}." );   
      break;
  }
  // fail by default
  return false;
}

function validateForm( form ) {
  let thisNet = 'SIPR';
  let isValid = true;
  let errors = [];

  // CLEAR!!  ...any previous submissions
  [...form.elements].forEach( ( elem ) => {
    elem.classList.remove( 'is-valid' );
    elem.classList.remove( 'is-invalid' );
  });

  // name
  if( !(form.elements.firstName.value.length || form.elements.lastName.value.length) ) {
    errors.push( form.elements.firstName, form.elements.lastName );
    isValid = false;
  }
  
  // source email
  if( !(form.elements.userEmail.value.length && checkEmail( form.elements.userEmail.value, thisNet, "from" ) ) ) {
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
    form.elements.network.forEach( ( elem ) => errors.push( elem ) );
    isValid = false;
  }

  // target email
  if( !( form.elements.targetEmail.value.length && checkEmail( form.elements.targetEmail.value, form.elements.network.value, "to" ) ) ) {
    errors.push( form.elements.targetEmail );
    isValid = false;
  }

  if( !isValid ) {
    // it's just a bunch of screwing around and explosions until you write it down (aka: log it)
    errors.forEach( ( elem ) => console.dir( elem ) );
    // mark everything good
    [...form.elements].forEach( ( elem ) => elem.classList.add( 'is-valid' ) );
    // mark the naughty-naughties
    errors.forEach( ( elem ) => {
      elem.classList.remove( "is-valid" );
      elem.classList.add( "is-invalid" );
    });
  }
  
  return isValid;
}

function prepareFormData( form ) { 
  let data = new FormData( form );
  
  data.delete( "files[]" );
  for( let i in fileQueue ) {
    data.append( 'files', fileQueue[i], fileQueue[i].name );
  }

  return data;
}

function successHandler( r ) { 
  console.dir( r ); 
}

function failHandler( r, s ) { 
  notifyUser( "A system error occurred while trying to submit the files.\n\n" + r.status + ": " + r.statusText + ".  Please notify the CFTS administrators of this error by emailing {{ SETTINGS.CFTS_ADMIN_EMAIL }}.");
}

function process( e ) {
  preventDefaults( e );

  let isValid = validateForm( xferForm );

  if( isValid ) {
    // Give user feedback that the submit action occurred and things are happening
    notifyUser( "Submitting the request now. This could take up to a few minutes depending upon the size of the files being transferred. Please stand by ... " );

    ajaxSettings = {
      url: 'api-processrequest',
      method: 'POST',
      data: prepareFormData( xferForm ),
      contentType: false,
      processData: false,
      beforeSend: function( xhr, settings ) {
        xhr.setRequestHeader("X-CSRFToken", getCookie('csrftoken'));
      }
    };
    $.ajax( ajaxSettings ).done( successHandler ).fail( failHandler );

  } else {
    // notify the user there were validation errors
    notifyUser( "There are errors on the request form.  Please review and address the indicated fields." );
  }
}