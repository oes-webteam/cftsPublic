let dropArea = document.getElementById( "drop-zone" );
let filesInput = document.getElementById( "standard-upload-files" );
let fileQueue = [];

preventDefaults = ( e ) => {
  e.preventDefault();
  e.stopPropagation();
};

addHighlight = ( e ) => dropArea.classList.add( 'highlight-active' );

removeHighlight = ( e ) => dropArea.classList.remove( 'highlight-active' );

removeFileFromQueue = ( e ) => {
  preventDefaults( e );
  fileQueue.splice( e.target.getAttribute( "index" ), 1 );
  displayFileQueue();
}

addFiles = ( e ) => {
  let fileList = [];
  if( 'dataTransfer' in e ) fileList = e.dataTransfer.files;
  else if ( 'target' in e ) fileList = e.target.files;
  else { 
    console.log( "WTF happened here?!" )
    console.dir( e ); 
  }

  for( let f = 0; f < fileList.length; f++ ) {
    let thisFile = fileList[f];
    let isValid = validateFile( thisFile );
    
    if( isValid )
      fileQueue.push( thisFile );
  } // endfor

  displayFileQueue();
}

displayFileQueue = () => {
  dropArea.innerHTML = "";
  let unorderedList = document.createElement( "ul" );
  for ( let f in fileQueue ) {
    let listItem = document.createElement( "li" );
    
    // add link to remove a file from the queue
    let deleteFile = document.createElement( "a" );
    deleteFile.classList.add( "remove" );
    deleteFile.setAttribute( "index", f );
    deleteFile.setAttribute( "title", "Remove File" );
    deleteFile.addEventListener( "click", removeFileFromQueue, false );
    listItem.appendChild( deleteFile );

    listItem.appendChild( document.createTextNode( fileQueue[f].name ) );
    unorderedList.appendChild( listItem );
  }
  dropArea.appendChild( unorderedList );
  dropArea.classList.remove( "empty" );
};

validateFile = ( thisFile ) => {
  let isvalid = true;
  let msg = thisFile.name;
  
  // kick out the JOPES
  let filename = thisFile.name.toLowerCase();
  if( filename.includes( "prf" ) || filename.includes( "lvy" ) || filename.includes( "levy" ) ) {
    // hard NO!!
    msg += "\nPRF and LVY files cannot be transferred per CFTS use policy. See Resources >> Cross Domain Users Guide for details.";
    notifyUser( msg );
    return false;
  }

  for( let q in fileQueue ) {
    let qFile = fileQueue[q];

    // make sure this file doesn't already exist in the queue
    // (crappy version -- would like to do this with MD5 or SHA-1 hash in the future)
    if( thisFile.name == qFile.name && thisFile.size == qFile.size ) {
      msg += "\nA file of this name and size is already in the queue.";
      notifyUser( msg );
      isvalid = false;
      break;
    }
  }

  return isvalid;
};

notifyUser = ( msg ) => {
  alert( msg );
};

// EVENT LISTENERS
// dropArea
[ 'dragenter', 'dragover', 'dragleave', 'drop' ].forEach( eventName => {
  dropArea.addEventListener( eventName, preventDefaults, false ); 
});

[ 'dragenter', 'dragover' ].forEach( eventName => {
  dropArea.addEventListener( eventName, addHighlight, false );
});

[ 'dragleave', 'drop' ].forEach( eventName => {
  dropArea.addEventListener( eventName, removeHighlight, false );
});

dropArea.addEventListener( 'drop', addFiles, false );
filesInput.addEventListener( 'change', addFiles, false );