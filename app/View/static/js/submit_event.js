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

        console.log('Submitting event data:', eventData); // Log the event data being sent

        $.ajax({
            url: '/add-event',
            type: 'POST',
            data: eventData,
            success: function(response) {
                console.log('Create event response:', response); // Log the response
                if (response.status === 'success') {
                    $('#editEventModal').modal('hide');
                    refreshCalendar();
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
