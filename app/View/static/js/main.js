function loadContent(contentName) {
    // Make sure the server route matches this AJAX call
    $.ajax({
        url: '/partials/' + contentName + '.html',
        type: 'GET',
        success: function(response) {
            $('#content-area').html(response);
            if (contentName === 'calendar') {
                initializeCalendar(); // This function is defined in calendar-initialize.js
            }
        },
        error: function() {
            $('#content-area').html('<p>Error loading content. Please try again.</p>');
        }
    });
}

$(document).ready(function() {
    $('#link-calendar').on('click', function(e) {
        e.preventDefault();
        loadContent('calendar');
    });

    // Handle click on other tabs similarly...
});
