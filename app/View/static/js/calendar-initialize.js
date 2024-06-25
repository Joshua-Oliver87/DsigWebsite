var calendar;

function openEventModal() {
    $('#editEventModal').modal('show');
}

function deleteEvent(eventId) {
    $.ajax({
        url: '/delete-event',
        type: 'POST',
        data: { event_id: eventId },
        success: function(response) {
            if (response.status === 'success') {
                // Ensure the event is removed from the calendar
                let event = calendar.getEventById(eventId);
                if (event) {
                    event.remove();
                }
                $('#eventDetailModal').modal('hide');
                fetchTodaysEvents();  // Refresh today's events
            } else {
                console.error('Failed to delete event:', response.message);
            }
        },
        error: function(xhr, status, error) {
            console.error('Failed to delete event:', error);
        }
    });
}


function displayEventDetails(event, canCreateEvents) {
    if (!event.start || !event.end) {
        console.error('Invalid event object:', event);
        return;
    }

    $('#eventDetailModal .modal-title').text(event.title);
    let eventInfoHtml =
        "<p><strong>Description:</strong> " + event.extendedProps.description + "</p>" +
        "<p><strong>Start:</strong> " + new Date(event.start).toLocaleString() + "</p>" +
        "<p><strong>End:</strong> " + new Date(event.end).toLocaleString() + "</p>" +
        "<p><strong>Creator:</strong> " + event.extendedProps.creator + "</p>" +
        "<p><strong>Type of Event:</strong> " + event.extendedProps.event_type + "</p>";
    $('#eventDetailModal .modal-body').html(eventInfoHtml);
    $('#deleteEventButton').data('eventId', event.id);

    if (canCreateEvents) {
        $('#deleteEventButton').show();
    } else {
        $('#deleteEventButton').hide();
    }

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
            if (info.event.extendedProps.event_color) {
                info.el.style.backgroundColor = info.event.extendedProps.event_color;
            }
        },
        headerToolbar: {
            left: 'prev,next today',
            center: 'title',
            right: canCreateEvents ? 'editCalendarButton' : ''
        },
        customButtons: {},
        contentHeight: 'auto',  // Adjust height to fit content
        aspectRatio: 2,  // Adjust aspect ratio to zoom out
    };

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


// Ensure the function is globally accessible
window.initializeCalendar = initializeCalendar;


function deleteEvent(eventId) {
    $.ajax({
        url: '/delete-event',
        type: 'POST',
        data: { event_id: eventId },
        success: function(response) {
            if (response.status === 'success') {
                calendar.getEventById(eventId).remove();
                $('#eventDetailModal').modal('hide');
                fetchTodaysEvents();  // Refresh today's events
            } else {
                console.error('Failed to delete event:', response.message);
            }
        },
        error: function(xhr, status, error) {
            console.error('Failed to delete event:', error);
        }
    });
}


function fetchTodaysEvents() {
    $.ajax({
        url: '/fetch-todays-events',
        type: 'GET',
        success: function(events) {
            var eventsList = $('.events-list');
            eventsList.empty();
            events.forEach(event => {
                eventsList.append(
                    `<div class="event-item" data-event-id="${event.id}">
                        <span class="event-title">${event.title}</span>
                    </div>`
                );
            });
            if (events.length === 0) {
                eventsList.append('<div class="no-events">No events scheduled for today.</div>');
            }
        },
        error: function() {
            console.error('Error fetching today\'s events');
        }
    });
}


