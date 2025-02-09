$(document).ready(function() {
    var calendarInitialized = false;
    var currentPage = 'dashboard';  // Default to 'dashboard'

    console.log("main.js loaded");

    $('.sidebar').removeClass('open');

    $('#editProfilePicture').on('click', function(e) {
        e.preventDefault();
        $('#uploadProfilePicture').click();
    });

    $('.sidebar-toggle-btn').on('click', function() {
        $('.sidebar').toggleClass('open');
    });

    // Close sidebar when a link inside it is clicked
    $('.sidebar .nav-link').on('click', function() {
        $('.sidebar').removeClass('open');
    });

    $('#homepage-content').show().css('margin-top', '0');
    $('#googleFormContainer').hide(); // Ensure the form is hidden initially
    $('#thirdFormContainer').hide();
    $('#importantDocumentsHeader').hide();
    $('#form-header').hide(); // Ensure the form header is hidden initially

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

    function setPage(page)
    {
        // Update the global variable
        currentPage = page;
        console.log('Setting page to:', page); // Debugging line

        // Define the possible classes
        const pageClasses = [
            'housepoint-form-page',
            'calendar-page',
            'dashboard-page',
            'forms-page'
        ];

        // Clear any previously set body classes
        $('body').removeClass(pageClasses.join(' '));

        // Map the page value to the corresponding class and apply it
        switch(page) {
            case 'housepoint-form':
                $('body').addClass('housepoint-form-page');
                break;
            case 'calendar':
                $('body').addClass('calendar-page');
                $('#calendar-header').show(); // Ensure the calendar header is shown
                $('.key-container').show(); // Show the key container when the calendar is shown
                break;
            case 'dashboard':
                $('body').addClass('dashboard-page');
                break;
            case 'forms':
                $('body').addClass('forms-page');
                break;
            default:
                console.warn('Unknown page:', page);
                break;
        }

         console.log('Body classes after setPage:', $('body').attr('class'));
    }


    function toggleVisibility(showCalendar) {
        if (showCalendar) {
            $('#calendar').show();
            $('#calendar-header').show();  // Show calendar header only when showing calendar
            $('.key-container').show();
        } else {
            $('#calendar').hide();
            $('#calendar-header').hide();  // Hide calendar header when not showing calendar
            $('.key-container').hide();
            resetMainContentStyles();
        }
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

    function resetMainContentStyles() {
        const mainContent = document.querySelector('.main-content');
        mainContent.style.marginTop = '0px';
        mainContent.style.paddingTop = '50px'; // Reapply the original padding if needed
        mainContent.style.overflowY = 'auto';
        mainContent.style.overflowX = 'hidden';
        console.log('Main content styles reset:', mainContent.getBoundingClientRect());
    }

    function attachEventHandlers()
    {
        $('#link-forms').on('click', function(e) {
            e.preventDefault();
            hideAllSections();
            $('#formsContainer').show();
            $('#thirdFormContainer').show();
            $('#googleFormContainer').show();
            $('#importantDocumentsHeader').show();
            console.log('Forms container is now visible:', $('#formsContainer').is(':visible'));
            setPage('forms');
        });

        $('#link-calendar').on('click', function(e) {
            e.preventDefault();
            hideAllSections();
            loadAndInitializeCalendar();
            setPage('calendar');
        });

        $('#link-dashboard').on('click', function(e) {
            e.preventDefault();
            hideAllSections();
            $('#homepage-content').show();
            setPage('dashboard');
        });
    }


    function hideAllSections()
    {
        $('#homepage-content').hide();
        $('#googleFormContainer').hide();
        $('#calendar').hide();
        $('#thirdFormContainer').hide();
        $('#importantDocumentsHeader').hide();
        $('#formsContainer').hide();
        $('#calendar-header').hide();
        $('.key-container').hide();
    }


    function showGoogleForm() {
        console.log('Showing Google Form');
        $('#googleFormContainer').show();
        $('#calendar').hide();
        $('#calendar-header').hide();
        $('.key-container').hide();
        $('#homepage-content').hide();
    }

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

    function attachEventDeletionHandler() {
        console.log('Attaching event deletion handler');
        $(document).off('click', '#deleteEventButton'); // Remove any existing handler
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

    function hideHomepageContent() {
        $('#homepage-content').hide();
    }

    attachEventHandlers();
});

