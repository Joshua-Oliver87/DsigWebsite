// calendar_initialize.js

var calendar;


function displayEventDetails(event, canCreateEvents) {
    // Update the modal with the event details
    $('#eventDetailModal .modal-title').text(event.title);
    let eventInfoHtml =
        "Description: " + event.extendedProps.description + "<br>" +
        "Start: " + event.start.toLocaleString() + "<br>" +
        "End: " + event.end.toLocaleString() + "<br>" +
        "Creator: " + event.extendedProps.creator + "<br>" +
        "Type of Event: " + event.extendedProps.event_type
    ;

    $('#eventDetailModal .modal-body').html(eventInfoHtml);

    // Store event ID for deletion
    $('#deleteEventButton').data('eventId', event.id);

    console.log("Can create events in initializor:", canCreateEvents);
    if (canCreateEvents) {
        $('#deleteEventButton').show();
    } else {
        $('#deleteEventButton').hide();
    }

    // Show the modal
    $('#eventDetailModal').modal('show');
}

function initializeCalendar(canCreateEvents) {
    console.log("canCreateEvents in calendar-initialize.js:", canCreateEvents);
    var calendarEl = document.getElementById('calendar');
    var calendarOptions = {
        initialView: 'dayGridMonth',
        events: '/fetch-events',
        eventClick: function(info) {
            displayEventDetails(info.event, canCreateEvents);
        },
        eventDidMount: function(info) {
            // Use this to set the background color for each event based on its properties
            if (info.event.extendedProps.event_color) {
                info.el.style.backgroundColor = info.event.extendedProps.event_color;
            }
        },
        headerToolbar: {
            left: 'prev,next today',
            center: 'title',
            right: canCreateEvents ? 'editCalendarButton' : ''
        },
        customButtons: {}
    };

    // Only add the custom button if canCreateEvents is true
    if (canCreateEvents) {
        calendarOptions.customButtons.editCalendarButton = {
            text: 'Edit Calendar',
            click: function() {
                openEventModal();
            }
        };
    }

    window.calendar = new FullCalendar.Calendar(calendarEl, calendarOptions);
    calendar.render();
}

function deleteEvent(eventId) {
    // Logic to delete the event, perhaps with an AJAX call to the server
    // After deletion, close the modal and refresh the calendar
    $.ajax({
        url: '/delete-event',
        type: 'POST',
        data: { event_id: eventId },
        success: function(response) {
            calendar.getEventById(eventId).remove();
            $('#eventDetailModal').modal('hide');
        },
        error: function(xhr, status, error) {
            // Handle errors here
            console.error('Failed to delete event:', error);
        }
    });
}

//window.initializeCalendar = initializeCalendar;

function openEventModal(){
    $('#eventModal').modal('show');
}


