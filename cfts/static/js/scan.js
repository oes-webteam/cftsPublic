window.document.title = "CFTS -- Scan Tool";
scanForm = document.querySelector( "#scanForm" );

// Add the CSRF token to ajax requests
$.ajaxSetup({
  beforeSend: function (xhr, settings) {
    xhr.setRequestHeader("X-CSRFToken", getCookie("csrftoken"));
  },
});

const callScan = function ( e ) {
  preventDefaults( e );
  let data = new FormData( scanForm );

  $.ajax({
    url: '/scan',
    data: data,
    cache: false,
    contentType: false,
    processData: false,
    method: 'POST',
    type: 'POST', // For jQuery < 1.9
    success: function( data ){
        processResults( data );
    }
  });
};

const processResults = function( results ) {
  try {
    let section = document.querySelector( '#scan-results' );
    let rootList = document.querySelector( '#rootList' );
    let rootItem = document.querySelector( '.root-item' );
    // loop over results

    for( let r of results ) {
      let cln = rootItem.cloneNode( true );
      cln.innerText = r.file;
      let rootScanned = r.found;
      // convert to an array, if needed
      if( typeof rootScanned == 'object' && !Array.isArray( rootScanned ) ) {
        rootScanned = [ rootScanned ];
      }
      rootItem.appendChild( processScanned( rootScanned ) );
      rootList.appendChild( rootItem );
    }
    
    section.style.display = "block";

  } catch ( err ) {
    console.log( err.message );
  }
};

const processScanned = function( scannedFiles ) {
  // returns list of files actually scanned (i.e. unzipped Office files)
  let scannedList = document.createElement( 'ul' );
  for( let scannedFile of scannedFiles ) {
    
    let scannedItem = document.createElement( 'li' );
    scannedItem.innerHTML = scannedFile.file;
    scannedItem.appendChild( processFindings( scannedFile.findings) );
    
    
    scannedList.appendChild( scannedItem );
  }
  return scannedList;
}

const processFindings = function( findings ) {
  let findingList = document.createElement( 'ul' );
  for( let finding of findings ) {
    let li = document.createElement( 'li' );
    let f = finding;
    li.innerHTML = f;
    findingList.appendChild( li );
  }
  return findingList;
};


scanForm.addEventListener( "submit", callScan, false );
