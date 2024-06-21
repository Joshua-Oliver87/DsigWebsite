$(document).ready(function() {
    var calendarInitialized = false;
    var currentPage = 'dashboard';  // Default to 'dashboard'

    $('#editProfilePicture').on('click', function(e) {
        e.preventDefault();
        $('#uploadProfilePicture').click();
    });

    $('#uploadProfilePicture').on('change', function() {
        var formData = new FormData();
        formData.append('profile_picture', $('#uploadProfilePicture')[0].files[0]);

        $.ajax({
            url: '/upload_profile_picture',
            type: 'POST',
            data: formData,
            processData: false,
            contentType: false,
            success: function(response) {
                if (response.success) {
                    $('#profilePicture').attr('src', response.image_url);
                } else {
                    alert(response.message);
                }
            },
            error: function() {
                alert('An error occurred while uploading the profile picture.');
            }
        });
    });

    function setPage(page) {
        currentPage = page;
        $('body').attr('class', page === 'housepoint-form' ? 'housepoint-form-page' : '');
    }

    function loadAndInitializeCalendar() {
        if (!calendarInitialized) {
            console.log('Loading and initializing calendar');
            $.ajax({
                url: '/partials/calendar.html',
                type: 'GET',
                success: function(response) {
                    $('#calendar').html(response);
                    fetchUserPermissions();
                    reinitializeSelect2();
                    attachEventDeletionHandler();
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

    function toggleVisibility(showCalendar) {
        console.log('Toggling visibility, showCalendar:', showCalendar);
        if (showCalendar) {
            $('#googleFormContainer').hide();
            $('#calendar').show();
            $('#homepage-content').hide();
            $('#calendar-header').show();
            $('.key-container').show();
        } else {
            $('#calendar').hide();
            $('#calendar-header').hide();
            $('.key-container').hide();
            $('#homepage-content').show().css('margin-top', '0');  // Reset margin-top
            $('#googleFormContainer').hide();

             resetMainContentStyles();
        }
    }

    function resetMainContentStyles() {
        const mainContent = document.querySelector('.main-content');
        mainContent.style.marginTop = '0px';
        mainContent.style.paddingTop = '50px'; // Reapply the original padding if needed
        mainContent.style.overflowY = 'auto';
        mainContent.style.overflowX = 'hidden';
        console.log('Main content styles reset:', mainContent.getBoundingClientRect());
    }

    function attachEventHandlers() {
        $('#link-Housepoint').on('click', function(e) {
            e.preventDefault();
            console.log('Housepoint Form button clicked');
            setPage('housepoint-form');
            showGoogleForm();
        });

        $('#link-calendar').on('click', function(e) {
            e.preventDefault();
            console.log('Calendar button clicked');
            setPage('calendar');
            toggleVisibility(true);
            loadAndInitializeCalendar();
        });

        $('#link-dashboard').on('click', function(e) {
            e.preventDefault();
            console.log('Dashboard button clicked');
            setPage('dashboard');
            toggleVisibility(false);
        });
    }

    function showGoogleForm() {
        console.log('Showing Google Form');
        $('#googleFormContainer').show();
        $('#calendar').hide();
        $('#calendar-header').hide();
        $('.key-container').hide();
        $('#homepage-content').hide();
    }

    function fetchUserPermissions() {
        console.log('Fetching user permissions');
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

    function reinitializeSelect2() {
        console.log('Reinitializing Select2');
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

    function attachEventDeletionHandler() {
        console.log('Attaching event deletion handler');
        $(document).on('click', '#deleteEventButton', function() {
            var eventId = $(this).data('eventId');
            if (eventId && confirm('Are you sure you want to delete this event?')) {
                deleteEvent(eventId);
            }
        });
    }

    function showEventDetails(eventId) {
        const modalBody = document.querySelector('#eventDetailModal .modal-body');
        console.log('showEventDetails called');

        fetch(`/fetch-event-details/${eventId}`)
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    console.error('Error fetching event details:', data.error);
                    return;
                }
                const startTime = new Date(data.start).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
                const endTime = new Date(data.end).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
                document.getElementById('eventTitle').textContent = data.title;
                document.getElementById('eventStart').textContent = startTime;
                document.getElementById('eventEnd').textContent = endTime;
                document.getElementById('eventDetailsDescription').textContent = data.description;
                $('#deleteEventButton').data('eventId', data.id);  // Correct usage of jQuery data method
                const modal = new bootstrap.Modal(document.getElementById('eventModal'));
                modal.show();
            })
            .catch(error => {
                console.error('Error fetching event details:', error);
            });
    }

    $('.events-list').on('click', '.event-item', function() {
        var eventId = $(this).data('eventId');
        showEventDetails(eventId);
    });

    function loadGoogleFormLink() {
        console.log('Loading Google Form link');
        $.ajax({
            url: '/settings/google-form-link',
            type: 'GET',
            success: function(response) {
                var googleFormLink = response.google_form_link;
                $('#googleFormIframe').attr('src', googleFormLink);
            },
            error: function() {
                console.error('Error loading Google Form link');
            }
        });
    }

    $('#homepage-content').show().css('margin-top', '0');
    $('#googleFormContainer').hide(); // Ensure the form is hidden initially
    $('#form-header').hide(); // Ensure the form header is hidden initially

    attachEventHandlers();
});
