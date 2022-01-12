window.document.title = "CFTS -- Pulls";

jQuery( document ).ready( function() {
  $( '.pull-menu-btn' ).click( e => {
    e.preventDefault();
    $( '.pull-menu' ).fadeOut( 'fast' );

    $this = $( e.target );

    $this.siblings( '.pull-menu' ).fadeToggle( 'fast' );
  }).blur( e => { $( '.pull-menu' ).fadeOut( 'fast' ); });

  $( '.pull-card' ).on('contextmenu', e => {
    e.preventDefault();
    $( '.pull-menu' ).fadeOut( 'fast' );
    
    $this = $( e.target )
    if(!$this.attr('pull_id')){
      $this = $( e.target ).parents(".pull-card");
    }

    pullID = $this.attr('pull_id')
    console.log(pullID)

    $('.pull-menu[pull_id="'+pullID+'"]').fadeToggle( 'fast' );
  }).blur( e => { $( '.pull-menu' ).fadeOut( 'fast' ); });

  //$( '.pull-menu' ).mouseleave( e => { $( '.pull-menu' ).fadeOut( 'fast' ); });

  $( '.oneeye' ).click( e => {
    e.preventDefault();
    $this = $( e.target );

    url = '/pulls-oneeye/' + $this.attr( 'href' );
    success = ( resp ) => {
        alert( "Pull id " + resp.id + " marked as 'One Eye Complete'." );
        location.reload();        
    };
    $.get( url, {}, success, 'json' );
  });

  $( '.twoeye' ).click( e => {
    e.preventDefault();
    $this = $( e.target );

    url = '/pulls-twoeye/' + $this.attr( 'href' );
    success = ( resp ) => {
        alert( "Pull id " + resp.id + " marked as 'Two Eye Complete'." );
        location.reload();        
    };
    $.get( url, {}, success, 'json' );
  });

  $( '.done' ).click( e => {
    e.preventDefault();
    $this = $( e.target );

    cd = prompt( 'Enter disc number' );
    if( cd === null || cd == '' ) return;

    url = '/pulls-done/' + $this.attr( 'href' ) + '/' + cd;
    success = ( resp ) => {
        // alert( "Pull id " + resp.id + " marked as 'Transfer Complete'." );
        location.reload();        
    };
    $.get( url, {}, success, 'json' );

  });

});