window.document.title = "CFTS -- Scan Tool";
scanForm = document.querySelector( "#scanForm" );
loadingIcon = document.querySelector('#loading-icon');
firstScan = true

// Add the CSRF token to ajax requests
$.ajaxSetup({
  beforeSend: function (xhr, settings) {
    xhr.setRequestHeader("X-CSRFToken", getCookie("csrftoken"));
  },
});

/* callScan( [event] ): returns void           */
/* POSTs the zip to the scan tool API via AJAX */
/* POST callback: processResults()             */
const callScan = function ( e ) {

  if(pullZip!=""){

    loadingIcon.hidden = false
    let data = pullZip;

    $.ajax({
      url: '/scan/'+pullZip,
      data: data,
      cache: false,
      contentType: false,
      processData: false,
      method: 'POST',
      type: 'POST', // For jQuery < 1.9
      success: function( data ){
          loadingIcon.hidden = true
          processResults( data );
      }
    });
  }
  else{
    preventDefaults( e );
    loadingIcon.hidden = false
    let data = new FormData( scanForm );

    $.ajax({
      url: '/scan/none',
      data: data,
      cache: false,
      contentType: false,
      processData: false,
      method: 'POST',
      type: 'POST', // For jQuery < 1.9
      success: function( data ){
        loadingIcon.hidden = true
        processResults( data );
      }
    });

  }


};


/* processResults( [json] ): returns void */
/* Builds HTML display of scan results    */
const processResults = function( results ) {
  try {
    let section = document.querySelector( '#scan-results' );
    let rootList = document.querySelector( '#rootList' );
    let rootItem = document.querySelector( '.root-item' );
    // loop over results

    if(results.length==0){
      console.log("scan returned no hits")
      let cln = rootItem.cloneNode( true );
      cln.innerHTML = "Scan returned no hits.";

      let scannedList = document.createElement( 'ul' );
      scannedList.classList.add( 'scanned-list' );

      cln.appendChild( scannedList );
      rootList.appendChild( cln );
      
    }
    for( let r of results ) {
      let cln = rootItem.cloneNode( true );
      cln.innerHTML = r.file;
      let rootScanned = r.found;
      // convert to an array, if needed
      if( typeof rootScanned == 'object' && !Array.isArray( rootScanned ) ) {
        rootScanned = [ rootScanned ];
      }
      cln.appendChild( processScanned( rootScanned ) );
      rootList.appendChild( cln );
    }
    
    section.style.display = "block";
    if(firstScan == true){
      rootList.removeChild( rootItem );
      firstScan = false;
    };

  } catch ( err ) {
    console.log( err.message );
  }
};

/* processScanned( [findings] ): returns unordered list with list items             */
/* Returns an HTML list of files and processed findings from unzipped Office files  */
  const processScanned = function( scannedFiles ) {
  let scannedList = document.createElement( 'ul' );
  scannedList.classList.add( 'scanned-list' );
  for( let scannedFile of scannedFiles ) {
    
    let scannedItem = document.createElement( 'li' );
    scannedItem.classList.add( 'scanned-item' );
    scannedItem.innerHTML = scannedFile.file;
    scannedItem.appendChild( processFindings( scannedFile.findings) );
    scannedList.appendChild( scannedItem );
  }
  return scannedList;
}

/* processFindings( [findings] ): returns unordered list with list items */
/* Returns HTML list of files and results from an array of findings */
const processFindings = function( findings ) {
  let findingList = document.createElement( 'ul' );
  findingList.classList.add( 'inner-files' );
  for( let finding of findings ) {
    let li = document.createElement( 'li' );
    li.classList.add( 'scanned-file' )
    let f = finding;
    li.innerHTML = f;
    findingList.appendChild( li );
  }
  return findingList;
};



if(pullZip!=""){
  scanForm.hidden = true;
  callScan();
}

scanForm.addEventListener( "submit", callScan, false );
