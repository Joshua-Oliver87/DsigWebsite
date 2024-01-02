// calendar_initialize.js
function initializeCalendar() {
    var calendarEl = document.getElementById('calendar');
    var calendar = new FullCalendar.Calendar(calendarEl, {
        initialView: 'dayGridMonth',
        // Add other FullCalendar options here
    });
    calendar.render();
}

// Make sure to expose initializeCalendar to the global scope if this file is a module.
window.initializeCalendar = initializeCalendar;
