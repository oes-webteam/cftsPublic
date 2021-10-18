// NO DOM DEPENDENCIES
function getCookie(name) {
  let cookie = {};
  document.cookie.split(';').forEach(function(el) {
    let [k,v] = el.split('=');
    cookie[k.trim()] = v;
  })
  return cookie[name];
}

$.ajaxSetup({ 
  beforeSend: function( xhr, settings ) {
    xhr.setRequestHeader("X-CSRFToken", getCookie('csrftoken'));
  } 
});

window.document.title = "CFTS -- Analyst Reports";


// HAS DOM DEPENDENCIES
$( document ).ready( function( ) {

  const runNumbers = ( e ) => {
    let start = $( "#numbersStartDate" ).val();
    let end = $( "#numbersEndDate" ).val();
    let isValid = () => {
      if( 
        start.length > 0
        && end.length > 0
        && Date.parse( start ) <= Date.parse( end )
      ) 
        return true;
      else 
        return false;
    };

    if( isValid() ) {
      let url = "/api-numbers";
      let data = { 'start_date': start, 'end_date': end };

      $.post( url, data, 'json' ).then( 
        // ajax request succeeded
        ( resp ) => {

          $( '#reviewed' ).text( resp.files_reviewed );
          $( '#transfered' ).text( resp.files_transfered );
          $( '#centcom' ).text( resp.centcom_files );
          $( '#rejected' ).text( resp.files_rejected );
          $( '#users' ).text( resp.user_count );
          
          $( '#excel' ).text("Excel files: " + resp.file_types.excel);
          $( '#word' ).text("Word files: " + resp.file_types.word);
          $( '#ppt' ).text("PowerPoint files: " + resp.file_types.ppt);
          $( '#txt' ).text("Text files: " + resp.file_types.text);
          $( '#pdf' ).text("PDF files: " + resp.file_types.pdf);
          $( '#img' ).text("Image files: " + resp.file_types.img);
          $( '#zip' ).text("Zip files: " + resp.file_types.zip);
          $( '#zipContents' ).text("Total files in zips: " + resp.file_types.zipContents);
          $( '#other' ).text("Other files: " + resp.file_types.other);

          $( '#CENTCOM-HQ' ).text("CENTCOM: " + resp.org_counts.HQ);
          $( '#ARCENT' ).text("ARCENT: " + resp.org_counts.ARCENT);
          $( '#AFCENT' ).text("AFCENT: " + resp.org_counts.AFCENT);
          $( '#NAVCENT' ).text("NAVCENT: " + resp.org_counts.NAVCENT);
          $( '#MARCENT' ).text("MARCENT: " + resp.org_counts.MARCENT);
          $( '#SOCCENT' ).text("SOCCENT: " + resp.org_counts.SOCCENT);
          $( '#OTHER' ).text("OTHER: " + resp.org_counts.OTHER);

          $( '#size' ).text(resp.file_sizes);

          $( '.col.results' ).show();

        }, 
        // ajax request failed
        ( resp, status ) => {
          console.dir( status, resp );
        } 
      );

    }
  };
  $( 'input.xfer-numbers' ).datepicker({ format: 'mm/dd/yyyy' }).change( runNumbers );

});
