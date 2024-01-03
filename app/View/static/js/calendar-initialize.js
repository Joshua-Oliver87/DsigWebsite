// calendar_initialize.js
var calendar;

function initializeCalendar() {
    var calendarEl = document.getElementById('calendar');
    calendar = new FullCalendar.Calendar(calendarEl, {
        headerToolbar: {
            left: 'prev,next today',
            center: 'title',
            right: 'editCalendarButton'
        },
        customButtons:{
            editCalendarButton: {
                text: 'Edit Calendar',
                click: function(){
                    //open model
                    openEventModal();
                }
            }
        },
        initialView: 'dayGridMonth',
        events: '/fetch-events',
        eventClick: function(info) {
            displayEventDetails(info.event);
        }
    });
    calendar.render();
}

function openEventModal(){
    $('#eventModal').modal('show');
}

function displayEventDetails(event){
    $('#eventDetailModal .modal-title').text(event.title);
    $('#eventDetailModal .modal-body').html(
        "Description: " + event.extendedProps.description + "<br>" +
        "Start: " + event.start.toLocaleString() + "<br>" +
        "End: " + event.end.toLocaleString() + "<br>" +
        "Creator: " + event.extendedProps.creator
    );
    // Show the modal
    $('#eventDetailModal').modal('show');
}

window.initializeCalendar = initializeCalendar;