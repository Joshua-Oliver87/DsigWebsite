function deleteEvent(eventId) {
    $.ajax({
        url: '/delete-event',
        type: 'POST',
        data: { event_id: eventId },
        success: function(response) {
            if (response.status === 'success') {
                calendar.refetchEvents();
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

function initializeCalendar(canCreateEvents) {
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
        contentHeight: 'auto',
        aspectRatio: 2,
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
