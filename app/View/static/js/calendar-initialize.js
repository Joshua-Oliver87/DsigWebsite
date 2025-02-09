function deleteEvent(eventId) {
    console.log('Deleting event with ID:', eventId); // Add console log
    $.ajax({
        url: '/delete-event',
        type: 'POST',
        data: { event_id: eventId },
        success: function(response) {
            console.log('Delete event response:', response); // Add console log
            if (response.status === 'success') {
                refreshCalendar();
                fetchTodaysEvents();
                $('#eventDetailModal').modal('hide');
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
    console.log('Fetching today\'s events'); // Debug log
    $.ajax({
        url: '/fetch-todays-events',
        type: 'GET',
        success: function(events) {
            console.log('Fetched today\'s events:', events); // Debug log
            var eventsList = $('.events-list');
            eventsList.empty();
            events.forEach(event => {
                console.log('Appending event to today\'s events:', event); // Debug log
                eventsList.append(
                    `<div class="event-item" data-event-id="${event.id}">
                        <span class="event-title">${event.title}</span>
                    </div>`
                );
            });
            if (events.length === 0) {
                console.log('No events found for today'); // Debug log
                eventsList.append('<div class="no-events">No events scheduled for today.</div>');
            }
        },
        error: function() {
            console.error('Error fetching today\'s events');
        }
    });
}

function openEventModal() {
    $('#editEventModal').modal('show');
}

function displayEventDetails(event, canCreateEvents) {
    if (!event.start || !event.end) {
        console.error('Invalid event object:', event);
        return;
    }


    let eventInfoHtml =
        "<p><strong>Description:</strong> " + (event.extendedProps.description || '') + "</p>" +
        "<p><strong>Start:</strong> " + new Date(event.start).toLocaleString() + "</p>" +
        "<p><strong>End:</strong> " + new Date(event.end).toLocaleString() + "</p>";

    $('#eventDetailModal .modal-title').text(event.title);
    $('#eventDetailModal .modal-body').html(eventInfoHtml);
    $('#deleteEventButton').data('eventId', event.id);

    if (canCreateEvents) {
        $('#deleteEventButton').show();
    } else {
        $('#deleteEventButton').hide();
    }

    $('#eventDetailModal').modal('show');
}

function refreshCalendar() {
    if (window.calendar) {
        window.calendar.refetchEvents();
        console.log('Calendar events refreshed'); // Debug log
    } else {
        console.error('Calendar instance not found.');
    }
}

function initializeCalendar(canCreateEvents) {
    var calendarEl = document.getElementById('calendar');
    if (!calendarEl) {
        console.error('Calendar element not found!');
        return;
    }// Early exit if the element is not found
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
        customButtons: canCreateEvents ? {
            editCalendarButton: {
                text: 'Edit Calendar',
                click: function() {
                    openEventModal();
                }
            }
        } : {},
        contentHeight: 'auto',
        aspectRatio: 2,
    };

    window.calendar = new FullCalendar.Calendar(calendarEl, calendarOptions);
    calendar.render();
    console.log('Calendar initialized'); // Add console log
}

$(document).ready(function() {
    var calendarInitialized = false;
    var currentPage = 'dashboard';

    function fetchUserPermissions() {
        $.ajax({
            url: '/user-permissions',
            type: 'GET',
            success: function(response) {
                var canCreateEvents = response.canCreateEvents;
                initializeCalendar(canCreateEvents);
            },
            error: function() {
                console.error('Error fetching user permissions');
            }
        });
    }

    function loadAndInitializeCalendar() {
        if (!calendarInitialized) {
            $.ajax({
                url: '/partials/calendar.html',
                type: 'GET',
                success: function(response) {
                    $('#calendar').html(response);
                    fetchUserPermissions();
                    calendarInitialized = true;
                    $('#calendar').show();
                },
                error: function() {
                    console.error('Error loading calendar content');
                }
            });
        } else {
            $('#calendar').show();
        }
    }

    $('#link-calendar').on('click', function(e) {
        e.preventDefault();
        currentPage = 'calendar';
        toggleVisibility(true);
        loadAndInitializeCalendar();
    });

    function toggleVisibility(showCalendar) {
        if (showCalendar) {
            $('#calendar').show();
            $('#homepage-content').hide();
        } else {
            $('#calendar').hide();
            $('#homepage-content').show().css('margin-top', '0');
        }
    }
});
