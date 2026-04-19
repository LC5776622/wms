
// $.noConflict(); - Seems Not Required.

//SEARCHABLE SCRIPT:-

// $(window).on('load', function() {
//     $('.searchable').select2({
//         minimumResultsForSearch: Infinity,
//         dropdownCssClass: 'searchable-dropdown'
//     });

//     $('#vendor').select2({
//         minimumInputLength: 3,
//         dropdownCssClass: 'searchable-dropdown'
//     });

//     $('#location, #category').change(function() {
//         var location = $('#location').val();
//         var category = $('#category').val();
//         $('#vendor option').each(function() {
//             if ((location == '' || $(this).data('location') == location) && (category == '' || $(this).data('category') == category)) {
//                 $(this).show();
//             } else {
//                 $(this).hide();
//             }
//         });
//         $('#vendor').val('');
//         $('#vendor').trigger('change.select2');
//     });
// });


//Script-2- WORKING:

$(document).ready(function() {
    $('#location, #category').change(function() {
        var location = $('#location').val();
        var category = $('#category').val();
        $('#vendor option').each(function() {
            if ((location == '' || $(this).data('location') == location) && (category == '' || $(this).data('category') == category)) {
                $(this).show();
            } else {
                $(this).hide();
            }
        });
        $('#vendor').val('');
    });
});

// ONE MORE SEARCHABLE-
// $(document).ready(function() {
//     $('.searchable').select2({
//         minimumResultsForSearch: Infinity,
//         dropdownCssClass: 'searchable-dropdown'
//     });

//     $('#vendor').select2({
//         minimumInputLength: 3,
//         dropdownCssClass: 'searchable-dropdown'
//     });

//     $('#location, #category').change(function() {
//         var location = $('#location').val();
//         var category = $('#category').val();
//         $('#vendor option').each(function() {
//             if ((location == '' || $(this).data('location') == location) && (category == '' || $(this).data('category') == category)) {
//                 $(this).show();
//             } else {
//                 $(this).hide();
//             }
//         });
//         $('#vendor').val('');
//         $('#vendor').trigger('change.select2');
//     });
// });


