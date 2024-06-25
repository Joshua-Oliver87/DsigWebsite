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
                if (response.status === 'success') {
                    $('#editEventModal').modal('hide');
                    // Refetch events to update the calendar and today's events
                    calendar.refetchEvents();
                    fetchTodaysEvents();
                    alert('Event added successfully!');
                } else {
                    var errorAlert = '<div class="alert alert-danger" role="alert">' +
                        'Error adding event: ' + response.message + '</div>';
                    $('#errorContainer').html(errorAlert);
                }
            },
            error: function(xhr, status, error) {
                var errorAlert = '<div class="alert alert-danger" role="alert">' +
                    'Error adding event: ' + error + '</div>';
                $('#errorContainer').html(errorAlert);
            }
        });
    });
});
