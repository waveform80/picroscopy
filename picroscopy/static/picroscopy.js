$('.confirmation').on('click', function() {
  if ($(this).attr('data-confirm'))
    return confirm($(this).attr('data-confirm'));
  else
    return confirm('Are you sure?');
});

