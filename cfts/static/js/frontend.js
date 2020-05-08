let dropArea = document.getElementById( "drop-zone" );
let filesInput = document.getElementById( "standard-upload-files" );
let fileQueue = [];

preventDefaults = ( e ) => {
  e.preventDefault();
  e.stopPropagation();
};
addHighlight = ( e ) => dropArea.classList.add( 'highlight' );
removeHighlight = ( e ) => dropArea.classList.remove( 'hightlight' );

dropHandler = ( e ) => {
  if ( !e.dataTransfer.files.length ) 
    console.log( "How do you drop 0 files? What did you drag here, a heffalump?" );
  else if ( 'files' in e.dataTransfer ) 
  fileQueue.push.apply( fileQueue, e.dataTransfer.files );
};

fileInputChange = ( e ) => {
  fileQueue.push.apply( fileQueue, e.target.files );
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

dropArea.addEventListener( 'drop', dropHandler, false );

// files[]
filesInput.addEventListener( 'change', fileInputChange, false );