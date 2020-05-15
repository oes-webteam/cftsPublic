window.document.title = "CFTS -- Analyst Reports"

$( '.datepicker.start' ).datepicker({
  format: 'mm/dd/yyyy',
  startDate: '-7d'
});

$( '.datepicker.end' ).datepicker({
  format: 'mm/dd/yyyy',
});