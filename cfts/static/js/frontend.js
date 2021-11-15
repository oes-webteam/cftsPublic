window.document.title = "CFTS -- Transfer Request Form"

let dropArea = document.getElementById( "drop-zone" );
let filesInput = document.getElementById( "standard-upload-files" );
let fileQueue = [];
let fileInfo = {};
let addEmail = document.getElementById( "addEmail" );
let classifications = [''];
let buggedPKIs = ['f7d359ebb99a6a8aac39b297745b741b']

console.log("Cache test")
/* *************************************************** */
/* GET USER CERT INFORMATION FROM VAR IN FRONTEND.HTML */
/* *************************************************** */
  // console.log(cert)
  subject = cert.split("=")
  subject = subject[subject.length-1]
  // console.log(subject)
  user = subject.split(".")
  // console.log(user)

  if (buggedPKIs.includes(userHash) == false){
	$("#firstName").val(user[1])
  	$("#lastName").val(user[0]) 
    }
  
  $("#userID").val(userHash)

/* ************************************* */
/* Get classifications from Django admin */
/* ****************************** ****** */
  //Add the CSRF token to ajax requests
  $.ajaxSetup({
    beforeSend: function (xhr, settings) {
      xhr.setRequestHeader("X-CSRFToken", getCookie("csrftoken"));
        },
    });
      
      
    ajaxSettings = {
    url: "api-getclassifications",
    method: "GET",
    contentType: false,
    processData: false,
    };
    $.ajax(ajaxSettings).done(successHandler);
    
  function successHandler(data){
    for(obj in data){
      classifications.push(data[obj].fields.abbrev)
        }
    }


/* ********************************************************* */
/* ADD FILES TO THE QUEUE WHEN ADDED FROM FIELD OR DROP ZONE */
/* ********************************************************* */
const addFiles = ( e ) => {
  let fileList = [];
  if( 'dataTransfer' in e ) fileList = e.dataTransfer.files;
  else if ( 'target' in e ) fileList = e.target.files;
  else { 
    console.log( "WTF happened here?!" )
    console.dir( e ); 
  }

  for( let f = 0; f < fileList.length; f++ ) {
    let thisFile = fileList[f];
    let validation = validateFile( thisFile );
    
    if ( validation.msg.length ) { 
      notifyUserWarning( validation.msg ); 
    }
    if( !validation.error ) {
      // add file to the queue
      fileObject = { 
        'object': thisFile,
        'name': thisFile.name
      };
      fileQueue.push( fileObject );
    }
  }

  updateFileInfo();
  displayFileQueue();
}


/* ************************************************ */
/* VALIDATE UPLOADED FILES (AS BEST WE CAN FOR NOW) */
/* ************************************************ */
const validateFile = ( thisFile ) => {
  let charWhitelist = new RegExp( /[^a-z0-9\.\s_-]/ );
  let msg = "";
  let errorFlag = false;
  
  let filename = thisFile.name.toLowerCase();

  // kick out the JOPES
  if( filename.includes( "prf" ) || filename.includes( "lvy" ) || filename.includes( "levy" ) ) {
    // hard NO!!
    msg += "<li>RF and LVY files cannot be transferred per CFTS use policy. See Resources &gt;&gt; 'CFTS Policies' for details.</li>";
    errorFlag = true;
  }
  
  // we don't transer emails
  if( filename.includes(".eml") || filename.includes(".msg")){
    msg += "<li>.eml and .msg files must be converted to an accepted file format before submission. Use Outlook to export these files to a PDF, Word Document, or plain text file.</li>";
    errorFlag = true;
  }

  // you seem to have a little ... something ... in your filename there.  You might want to clean that up.
  if( charWhitelist.test( filename ) ) {
    msg += "<li>Special characters in filenames can cause the system to reject the files. Please review the filename and ensure it only contains letters, numbers, periods, dashes, or underscores.</li>";
  }
  
  if( msg.length > 0 ) {
    msg = "<strong>File error -- " + thisFile.name + "</strong>" + msg;
  }

    
  return { 'error': errorFlag, 'msg': msg };
};


/* ************************************************************** */
/* TAKE THE STUFF FROM THE FILE LIST AND ADD IT TO THE FILE QUEUE */
/* ************************************************************** */
const updateFileInfo = () => {
  // loop the file list
  let fileList  = document.querySelectorAll( ".file-list ul li" );
  for ( let i = 0; i < fileList.length; i++ ) {
    let cls = fileList[i].querySelector( "select" );
    let encrypt = fileList[i].querySelector( "input" );
    
    fileQueue[i].cls = cls.value;
    fileQueue[i].encrypt = encrypt.checked;
  }
};


/* **************************************************************************** */
/* RENDER THE FILES IN THE QUEUE ON THE PAGE, WITH LINKS TO REMOVE OR EDIT INFO */
/* **************************************************************************** */
const displayFileQueue = () => {
  if( fileQueue.length ) {
    let displayArea = $( '.file-list' )[0];

    // CLEAR!!!
    displayArea.innerHTML = "";
    displayArea.classList.remove( 'init' );

    let unorderedList = displayArea.children[0] || document.createElement( "ul" );
    for ( let i in fileQueue ) {
      let listItem = document.createElement( "li" );
      
      // add link to remove a file from the queue
      let deleteFile = document.createElement( "a" );
      deleteFile.classList.add( "remove" );
      deleteFile.setAttribute( "index", i );
      deleteFile.setAttribute( "title", "Remove File" );
      deleteFile.addEventListener( "click", removeFileFromQueue, false );
      listItem.appendChild( deleteFile );

      listItem.appendChild( document.createTextNode( fileQueue[i].name ) );

      let fileInfoDiv = document.createElement( "div" );
      fileInfoDiv.classList.add( "form-row" );
      
      let selectClass = document.createElement( "select" );
      selectClass.classList.add( "file-classification", "form-control", "col" );
      selectClass.setAttribute( "name", "classification" + i );
      selectClass.setAttribute( "id", "classification" + i );
      selectClass.required = true;

    classifications.forEach(  c => {
      let option = document.createElement( "option" );
      option.setAttribute( "value", c );
      if( fileQueue[i] && fileQueue[i].cls == c ) option.selected = true;
      option.appendChild( document.createTextNode( c ) );
      selectClass.appendChild( option );
    });
      
      

      

      fileInfoDiv.appendChild( selectClass );

      let toEncrypt = document.createElement( "input" );
      toEncrypt.setAttribute( "type", "checkbox" );
      toEncrypt.setAttribute( "name", "encrypt" + i )
      toEncrypt.setAttribute( "id", "encrypt" + i )
      toEncrypt.setAttribute( "value", "true" );
      if( fileQueue[i] && fileQueue[i].encrypt ) toEncrypt.checked = true;
      toEncrypt.classList.add( "form-check-input", "col" );

      let checkLabel = document.createElement( "label" );
      checkLabel.setAttribute( "for", "encrypt" + i );
      checkLabel.append( document.createTextNode( "Send Encrypted?" ) );
      checkLabel.classList.add( "form-check-label", "col" );
      fileInfoDiv.appendChild( toEncrypt );
      fileInfoDiv.appendChild( checkLabel );

      listItem.appendChild( fileInfoDiv );

      unorderedList.appendChild( listItem );
    } // endfor
    if( displayArea.children.length == 0 ) displayArea.appendChild( unorderedList );
  }
};


/* ********************************* */
/* REMOVE A FILE FROM THE FILE QUEUE */
/* ********************************* */
const removeFileFromQueue = ( e ) => {
  preventDefaults( e );
  fileQueue.splice( e.target.getAttribute( "index" ), 1 );

  let fileList = document.querySelector( ".file-list ul" );
  fileList.removeChild( e.target.parentElement );

  updateFileInfo();
  displayFileQueue();
};


/* ***************************************** */
/* ADD/REMOVE HIGHLIGHTING TO/FROM DROP ZONE */
/* ***************************************** */
addHighlight = ( e ) => dropArea.classList.add( 'highlight-active' );
removeHighlight = ( e ) => dropArea.classList.remove( 'highlight-active' );


/* ******************* */
/* REMOVE EXTRA EMAILS */
/* ******************* */
const deleteEmailField = ( e ) => {
  preventDefaults( e );
  console.log(e.parentNode)
};

/* ******************************* */
/* ADD NEW DESTINATION EMAIL FIELD */
/* ******************************* */
const createEmailField = ( e ) => {
  
  preventDefaults( e );
  let emailFields = document.getElementsByName('targetEmail');
  let emailFieldEmpty = false;

  emailFields.forEach(field => {
    if(field.value == ""){
      console.log("empty email field")
      field.classList.add('is-invalid');
      emailFieldEmpty = true;
    }
    else{
      if(field.classList.contains('is-invalid')){
        field.classList.remove('is-invalid');
      }
    }
  })

  if(emailFieldEmpty == false){
    let theButton = e.target;
    let count = document.getElementsByName( 'targetEmail' ).length - 1;
    
  //  let spacerSpan = document.createElement( 'span' );
  //  spacerSpan.classList.add( 'w-100' );

    let newField = document.createElement( 'input' );
    newField.setAttribute( 'type', 'email' );
    newField.setAttribute( 'name', 'targetEmail' );
    newField.setAttribute( 'id', 'destination' + count );
    newField.setAttribute( 'placeholder', 'Email Address' );
    newField.classList.add( 'form-control' );

    let appendSpan = document.createElement('span');
    appendSpan.classList.add('input-group-text')
    appendSpan.setAttribute('id', 'removeEmail' + count)
    appendSpan.textContent="X"
    appendSpan.addEventListener( "click", () => {
      appendSpan.parentNode.parentNode.remove();
    }, false );


    let removeField = document.createElement('div');
    removeField.classList.add('input-group-append')
    removeField.appendChild(appendSpan);
    
    let formGroup = document.createElement( 'div' );
    formGroup.classList.add( 'form-group', 'add-email', 'input-group' );
    formGroup.appendChild( newField );
    formGroup.appendChild(removeField);


    // inputGroup.insertBefore( spacerSpan, inputGroup.children[ position ] )
    theButton.parentElement.insertAdjacentElement( "beforeBegin", formGroup );
  }
}

addEmail.addEventListener( 'click', createEmailField, false );



/* *************** */
/* EVENT LISTENERS */
/* *************** */
// prevent default actions for all these events
[ 'dragenter', 'dragover', 'dragleave', 'drop' ].forEach( eventName => {
  dropArea.addEventListener( eventName, preventDefaults, false ); 
});

// add/remove highlighting to/from drop zone
[ 'dragenter', 'dragover' ].forEach( eventName => {
  dropArea.addEventListener( eventName, addHighlight, false );
});
[ 'dragleave', 'drop' ].forEach( eventName => {
  dropArea.addEventListener( eventName, removeHighlight, false );
});

// the add files handler for the drop zone and file field
dropArea.addEventListener( 'drop', addFiles, false );
filesInput.addEventListener( 'change', addFiles, false );