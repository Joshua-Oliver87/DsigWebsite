$(document).ready(function() {
    // Function to load and initialize the calendar
    var calendarInitialized = false;

    function toggleVisibility(showCalendar) {
        if (showCalendar) {
            $('#googleFormContainer').hide();
            if (!calendarInitialized) {
                loadAndInitializeCalendar();
            } else {
                $('#calendar').show();
            }
        } else {
            $('#calendar').hide();
            loadGoogleFormLink();
            $('#googleFormContainer').show();
        }
    }

    $('#updateGoogleFormLinkButton').on('click', function() {
        var newLink = $('#newGoogleFormLink').val();
        $.ajax({
            url: '/update-google-form', // The Flask route
            type: 'POST',
            data: { googleFormLink: newLink },
            success: function(response) {
                $('#updateStatus').text(response.message).css('color', 'green');
            },
            error: function() {
                $('#updateStatus').text('Error updating the link').css('color', 'red');
            }
        });
    });

    function loadAndInitializeCalendar() {
        if (!calendarInitialized) {
            $.ajax({
                url: '/partials/calendar.html',
                type: 'GET',
                success: function(response) {
                    $('#content-area').html(response);
                    fetchUserPermissions();
                    reinitializeSelect2();
                    attachEventDeletionHandler();
                    calendarInitialized = true;
                    $('#calendar').show(); // Ensure the calendar container is visible
                },
                error: function() {
                    console.error('Error loading calendar content');
                }
            });
        }
    }


     function attachEventHandlers() {
         $('#link-Housepoint').on('click', function(e) {
            e.preventDefault();
            $('#calendar').hide();
            console.log("just called calendar.hide()");
            $('#googleFormContainer').show();
            loadGoogleFormLink();
            // No need to reset calendarInitialized here
        });

        $('#link-calendar').on('click', function(e) {
            e.preventDefault();
            if ($('#calendar').is(':empty') || !$('#calendar').is(':visible')) {
                $('#googleFormContainer').hide();
                console.log("just called googleFormContainer.hide()");
                $('#calendar').show();
                loadAndInitializeCalendar();
                console.log("jsut called laod and initialize calendar)");
            } else {
                // Calendar is already initialized and visible
                $('#googleFormContainer').hide();
                $('#calendar').show();
            }
        });
    }

    // Function to fetch user permissions
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

    // Function to reinitialize Select2 with colored text
    function reinitializeSelect2() {
        $('#eventType').select2({
            templateResult: function(state) {
                if (!state.id) {
                    return state.text;
                }
                var color = $(state.element).data('color');
                var $state = $('<span style="color:' + color + '">' + state.text + '</span>');
                return $state;
            },
            templateSelection: function(state) {
                var color = $(state.element).data('color');
                var $state = $('<span style="color:' + color + '">' + state.text + '</span>');
                return $state;
            }
        });
    }

    // Function to attach event deletion handler
    function attachEventDeletionHandler() {
        $(document).on('click', '#deleteEventButton', function() {
            var eventId = $(this).data('eventId');
            if (eventId && confirm('Are you sure you want to delete this event?')) {
                deleteEvent(eventId);
            }
        });
    }

    // Function to load Google Form link
    function loadGoogleFormLink() {
        $.ajax({
            url: '/settings/google-form-link',  // Update this URL as per your route
            type: 'GET',
            success: function(response) {
                googleFormLoaded = true;
                var googleFormLink = response.google_form_link;
                console.log(response);
                $('#googleFormIframe').attr('src', googleFormLink);
                console.log('Iframe should now load:', googleFormLink);
            },
            error: function() {
                console.error('Error loading Google Form link');
            }
        });
    }
    attachEventHandlers(); //initial attachment
});
