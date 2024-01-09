

$(document).ready(function() {


    $('#link-calendar').on('click', function(e) {
        e.preventDefault();
        loadContent('calendar');
    });

    $('#eventType').select2({
        templateResult: function (state) {
            if (!state.id) {
                return state.text; // optgroup
            }
            var color = $(state.element).data('color');
            var $state = $('<span style="background-color:' + color + '; color: white;">' + state.text + '</span>');
            return $state;
        },
        templateSelection: function (state) {
            var color = $(state.element).data('color');
            var $state = $('<span style="background-color:' + color + '; color: white;">' + state.text + '</span>');
            return $state;
        }
    });
    // Handle click on other tabs similarly...
});

$(document).on('click', '#deleteEventButton', function() {
    var eventId = $(this).data('eventId');
    if (eventId && confirm('Are you sure you want to delete this event?')) {
        deleteEvent(eventId);
    }
});


function loadContent(contentName) {
    // Make sure the server route matches this AJAX call
    $.ajax({
        url: '/partials/' + contentName + '.html',
        type: 'GET',
        success: function(response) {
            $('#content-area').html(response);
            if (contentName === 'calendar') {
                if (typeof initializeCalendar === "function") {
                    if ($("#calendar").length) {
                        initializeCalendar(canCreateEvents);
                    }
                    // Reinitialize Select2 here
                    $('#eventType').select2({
                        templateResult: function(state) {
                            if (!state.id) {
                                return state.text;
                            }
                            var color = $(state.element).data('color') || state.element.value; // Use data-color or value
                            var $state = $('<span style="background-color:' + color +
                                           '; color: white; font-weight:bold;">' + state.text + '</span>');
                            return $state;
                        }
                    });
                }
            }
        },
        error: function() {
            $('#content-area').html('<p>Error loading content. Please try again.</p>');
        }
    });
}



