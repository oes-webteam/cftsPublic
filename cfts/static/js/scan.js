window.document.title = "CFTS -- Scan Tool";
scanForm = document.querySelector( "#scanForm" );
loadingIcon = document.querySelector('#loading-icon');
scanResults = document.querySelector('#scan-results')
firstScan = true

// Add the CSRF token to ajax requests
$.ajaxSetup({
  beforeSend: function (xhr, settings) {
    xhr.setRequestHeader("X-CSRFToken", getCookie("csrftoken"));
  },
});

/* sends ajax request to scan contents of a pull or an uploaded zip file
   scan results are rendered into a Django template and then returned to
   client to paste on the page.*/
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
          notifyUserSuccess("Files Scanned Successfully")
          console.log(data)
          $('#rootList').html(data)
          scanResults.hidden = false
          //processResults( data );
      },
      error: function( data ){
          loadingIcon.hidden = true
          responseText = data.responseText
          errorInfo = responseText.substring(data.responseText.indexOf("Exception Value"), data.responseText.indexOf("Python Executable"))
          notifyUserError( "Error in scan, " + data.status + ": " + data.statusText+ " --  Show this to the web team: " + errorInfo);
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
        notifyUserSuccess("Files Scanned Successfully")
        processResults( data );
      },
      error: function( data ){
          loadingIcon.hidden = true
          responseText = data.responseText
          errorInfo = responseText.substring(data.responseText.indexOf("Exception Value"), data.responseText.indexOf("Python Executable"))
          notifyUserError( "Error in scan, " + data.status + ": " + data.statusText+ " --  Show this to the web team: " + errorInfo);
      }
    });

  }


};

if(pullZip!=""){
  scanForm.hidden = true;
  callScan();
}

scanForm.addEventListener( "submit", callScan, false );
