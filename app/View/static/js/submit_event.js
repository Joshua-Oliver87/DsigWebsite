// Ensure that 'calendar' is initialized in the global scope or imported from 'calendar-initialize.js'
$(document).ready(function() {
    $('#eventForm').on('submit', function(e) {
        e.preventDefault();

        var eventData = {
            title: $('#eventName').val(),
            description: $('#eventDescription').val(),
            start: $('#eventStartDate').val(),
            end: $('#eventEndDate').val(),
            event_type: $('#eventType').val(), // Assuming you have an input with ID 'eventType'
            event_color: $('#eventType option:selected').attr('data-color'),
        };

        $.ajax({
            url: '/add-event', // This should match the Flask route in your Controller directory
            type: 'POST',
            data: eventData,
            success: function(response) {
                // Assuming 'calendar' is the FullCalendar instance you've initialized
                calendar.addEvent({
                    ...eventData,
                    backgroundColor: eventData.event_color, // Set the color of the event
                    borderColor: eventData.event_color // Optionally, you can set the border color as well
                });

                // Hide the modal
                $('#eventModal').modal('hide');

                calendar.refetchEvents();

                // Here you can add a message to the user, like:
                alert('Event added successfully!');
            },
            error: function(xhr, status, error) {
                // Use Bootstrap's alert component for error display
                var errorAlert = '<div class="alert alert-danger" role="alert">' +
                     'Error adding event: ' + error + '</div>';

                // Append or show the error message in the modal or somewhere on the page
                $('#errorContainer').html(errorAlert); // Assuming you have a div with id 'errorContainer'
            }
        });
    });
});

