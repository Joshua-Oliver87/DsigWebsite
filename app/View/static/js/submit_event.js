$(document).ready(function() {
    $('#eventForm').on('submit', function(e) {
        e.preventDefault();

        var eventData = {
            title: $('#eventName').val(),
            description: $('#eventDescription').val(),
            start: $('#eventStartDate').val(),
            end: $('#eventEndDate').val(),
            event_type: $('#eventType').val(),
            event_color: $('#eventType option:selected').attr('data-color'),
        };

        $.ajax({
            url: '/create-event',
            type: 'POST',
            data: eventData,
            success: function(response) {
                // Remove this part to prevent manual adding of events
                /*
                if (!window.calendar.getEventById(response.event_id)) {
                    window.calendar.addEvent({
                        id: response.event_id, // Ensure the event ID is set correctly
                        ...eventData,
                        backgroundColor: eventData.event_color,
                        borderColor: eventData.event_color
                    });
                }
                */

                $('#editEventModal').modal('hide');

                // Refetch events to update the calendar and today's events
                calendar.refetchEvents();
                fetchTodaysEvents();

                alert('Event added successfully!');
            },
            error: function(xhr, status, error) {
                var errorAlert = '<div class="alert alert-danger" role="alert">' +
                    'Error adding event: ' + error + '</div>';
                $('#errorContainer').html(errorAlert);
            }
        });
    });
});
