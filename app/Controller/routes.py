from datetime import datetime
from flask import render_template, redirect, url_for, request, flash, jsonify, current_app, abort, send_from_directory, g
from flask_login import current_user, login_user, logout_user, login_required
from jinja2 import TemplateNotFound
from werkzeug.security import generate_password_hash
from app import db, login_manager
from app.Model.models import User, Event, EventForm, Settings
from app.Controller.admin_decorator import admin_required
from app.shared import data
from sqlalchemy.exc import InvalidRequestError
import os
from werkzeug.utils import secure_filename
import logging
from google.cloud import storage

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
UPLOAD_FOLDER = os.path.join(os.path.abspath(os.path.dirname(__file__)), '../../UploadedProfilePictures')

logging.basicConfig(level=logging.DEBUG)



def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

#def get_image_url(filename):
    #bucket_name = os.getenv('delta-sigma-phi-website.appspot.com')
    #return f"https://storage.googleapis.com/{bucket_name}/{filename}"
def register_routes(application):
    application.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

    @application.route('/upload_profile_picture', methods=['POST'])
    @login_required
    def upload_profile_picture():
        if 'profile_picture' not in request.files:
            logging.debug('No file part in request')
            return jsonify({'success': False, 'message': 'No file part'})

        file = request.files['profile_picture']
        if file.filename == '':
            logging.debug('No selected file')
            return jsonify({'success': False, 'message': 'No selected file'})

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)

            # Upload to Google Cloud Storage
            bucket_name = application.config['delta-sigma-phi-website.appspot.com']
            storage_client = storage.Client()
            bucket = storage_client.bucket(bucket_name)
            blob = bucket.blob(filename)
            blob.upload_from_file(file)

            # Update the profile picture field
            current_user.profile_picture = filename
            logging.debug(f'Attempting to update profile picture to {filename} for user {current_user.id}')

            try:
                # Merge current_user into the current session
                db.session.merge(current_user)
                db.session.commit()
                logging.debug(f'Successfully updated profile picture to {filename} for user {current_user.id}')
            except Exception as e:
                logging.error(f'Error committing to database: {e}')
                db.session.rollback()
                return jsonify({'success': False, 'message': 'Database commit failed'})

            # Confirm the profile picture is updated in the database
            user_in_db = User.query.get(current_user.id)
            logging.debug(f'Profile picture in database for user {user_in_db.id}: {user_in_db.profile_picture}')

            image_url = url_for('uploaded_file', filename=filename)
            return jsonify({'success': True, 'image_url': image_url})

        logging.debug('File not allowed')
        return jsonify({'success': False, 'message': 'File not allowed'})

    @application.route('/')
    def welcome():
        return render_template('welcome.html')

    @login_manager.user_loader
    def load_user(user_id):
        user = User.query.get(int(user_id))
        if user and user.is_approved:
            return user
        return None

    @application.route('/register', methods=['GET', 'POST'])
    def register():
        if request.method == 'POST':
            email = request.form['email']
            username = request.form['username']
            password = request.form['password']

            existing_user = User.query.filter_by(username=username).first()
            if existing_user:
                flash('Username already taken. Please choose a different one.')
                return redirect(url_for('register'))

            hashed_password = generate_password_hash(password)
            new_user = User(username=username, email=email, password_hash=hashed_password)
            new_user.is_approved = False
            db.session.add(new_user)
            db.session.commit()
            flash('Registration pending, please wait for approval from admin', 'info')
            return redirect(url_for('login'))

        return render_template('register.html')

    @application.route('/login', methods=['GET', 'POST'])
    def login():
        if current_user.is_authenticated:
            return redirect(url_for('user_homepage'))

        if request.method == 'POST':
            username = request.form['username']
            password = request.form['password']

            user = User.query.filter_by(username=username).first()

            if user and user.check_password(password):
                if not user.is_approved:
                    flash("Your account is not approved yet. Please wait for an admin to approve it.")
                    return redirect(url_for('login'))
                login_user(user)
                return redirect(url_for('user_homepage'))
            else:
                flash("Invalid username or password.")

        return render_template('login.html')

    @application.route('/fetch-todays-events')
    @login_required
    def fetch_todays_events():
        today = datetime.now().date()
        start_of_day = datetime.combine(today, datetime.min.time())
        end_of_day = datetime.combine(today, datetime.max.time())

        events = Event.query.filter(Event.start <= end_of_day, Event.end >= start_of_day).all()
        events_data = []
        for event in events:
            events_data.append({
                'id': event.id,
                'title': event.title,
                'start': event.start.strftime('%H:%M'),
                'end': event.end.strftime('%H:%M'),
                'description': event.description,
                'creator': event.creator.username,
                'event_color': event.event_color,
                'event_type': event.event_type,
            })
        current_app.logger.info(f"Todays events: {events_data}")
        return jsonify(events_data)

    @application.route('/logout')
    def logout():
        logout_user()
        return redirect(url_for('welcome'))

    @application.route('/user_homepage')
    @login_required
    def user_homepage():
        user_email = current_user.email
        user_data = data.get(user_email, {})
        total_points = sum(
            int(user_data.get(category, 0) or 0)
            for category in
            ['Brotherhoods', 'Social Events', 'Philanthropy', 'Recruitment Events', 'Programming', 'Community Service',
             'Other']
        )
        user_data['Total'] = total_points
        todays_events = fetch_todays_events().json
        print("Data being passed to template:", user_data)
        return render_template('user_homepage.html', data=user_data, events=todays_events, page='homepage')

    @application.route('/fetch-event-details/<int:event_id>')
    @login_required
    def fetch_event_details(event_id):
        event = Event.query.get(event_id)
        if event:
            event_data = {
                'id': event.id,
                'title': event.title,
                'start': event.start.isoformat(),
                'end': event.end.isoformat(),
                'description': event.description,
                'creator': event.creator.username,
                'event_color': event.event_color,
                'event_type': event.event_type,
            }
            return jsonify(event_data)
        else:
            return jsonify({'error': 'Event not found'}), 404

    @application.route('/admin/dashboard')
    @login_required
    @admin_required
    def admin_dashboard():
        return render_template('admin_dashboard.html')

    @application.route('/make_admin/<int:user_id>', methods=['POST'])
    @login_required
    @admin_required
    def make_admin(user_id):
        user = User.query.get(user_id)
        if user:
            user.is_admin = True
            db.session.commit()
            flash("User promoted to admin successfully!")
        else:
            flash("User not found.")
        return redirect(url_for('admin_dashboard'))

    @application.route('/calendar')
    @login_required
    def calendar_view():
        events = Event.query.all()
        canCreateEvents = current_user.canCreateEvents
        current_app.logger.info(f"Calendar View Accessed. canCreateEvents: {canCreateEvents}")
        return render_template('partials/calendar.html', can_create_events=canCreateEvents)

    @application.route('/user-permissions')
    @login_required
    def user_permissions():
        can_create_events = current_user.canCreateEvents
        return jsonify({'canCreateEvents': can_create_events})

    @application.route('/add-event', methods=['POST'])
    @login_required
    def add_event():
        event_data = request.form
        new_event = Event(
            title=event_data.get('title'),
            description=event_data.get('description'),
            start=datetime.fromisoformat(event_data.get('start')),
            end=datetime.fromisoformat(event_data.get('end')),
            creator_id=current_user.id,
            event_type=event_data.get('event_type'),
            event_color=event_data.get('event_color'),
        )
        db.session.add(new_event)
        db.session.commit()
        return jsonify({"message": "Event added successfully", "status": "success", "event_id": new_event.id})

    @application.route('/delete-event', methods=['POST'])
    @login_required
    def delete_event():
        if not current_user.canCreateEvents:
            flash('You do not have permission to edit the calendar.')
            return redirect(url_for('calendar_view'))

        event_id = request.form.get('event_id')

        if not event_id:
            return jsonify({"message": "Event ID is required", "status": "error"}), 400

        try:
            # Use a fresh session context to query and delete the event
            event_to_delete = db.session.query(Event).get(event_id)
            if event_to_delete:
                db.session.delete(event_to_delete)
                db.session.commit()
                current_app.logger.info(f"Deleted event with ID: {event_id}")
                return jsonify({"message": "Event deleted successfully", "status": "success"})
            else:
                current_app.logger.error(f"Event with ID: {event_id} not found.")
                return jsonify({"message": "Event not found", "status": "error"}), 404
        except InvalidRequestError as e:
            current_app.logger.error(f"Session error: {str(e)}")
            db.session.rollback()
            db.session.remove()  # Ensure the current session is removed and reset
            return jsonify({"message": "An error occurred: " + str(e), "status": "error"}), 500
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error deleting event with ID: {event_id}. Error: {str(e)}")
            return jsonify({"message": "An error occurred: " + str(e), "status": "error"}), 500

    @application.route('/partials/<content_name>.html')
    @login_required
    def partials(content_name):
        try:
            return render_template('partials/' + content_name + '.html')
        except TemplateNotFound:
            abort(404)

    @application.route('/calendar-content')
    @login_required
    def calendar_content():
        return render_template('partials/calendar.html')

    @application.route('/create-event', methods=['GET', 'POST'])
    @login_required
    def create_event():
        if not current_user.canCreateEvents:
            if request.is_xhr:
                return jsonify({"message": "You do not have permission to create events.", "status": "error"}), 403
            flash('You do not have permission to create events.')
            return redirect(url_for('calendar_view'))

        form = EventForm()
        if form.validate_on_submit():
            event = Event(
                title=form.title.data,
                description=form.description.data,
                start=datetime.strptime(form.start.data, '%Y-%m-%d %H'),
                end=datetime.strptime(form.end.data, '%Y-%m-%d %H'),
                creator_id=current_user.id,
                event_type=form.event_type.data,
                event_color=form.event_color.data
            )
            db.session.add(event)
            try:
                db.session.commit()
                if request.is_xhr:
                    return jsonify({"message": "Event created successfully", "status": "success", "event_id": event.id})
                flash('Event created successfully!')
                return redirect(url_for('calendar_view'))
            except Exception as e:
                db.session.rollback()
                if request.is_xhr:
                    return jsonify({"message": "An error occurred: " + str(e), "status": "error"}), 500
                flash('An error occurred while saving the event: ' + str(e))

        if request.is_xhr:
            return jsonify({"message": "Invalid form data", "status": "error"}), 400
        return render_template('create_event.html', form=form)

    @application.route('/fetch-events', methods=['GET'])
    @login_required
    def fetch_events():
        try:
            events = Event.query.all()
            events_list = []
            for event in events:
                events_list.append({
                    'id': event.id,
                    'title': event.title,
                    'start': event.start.isoformat(),
                    'end': event.end.isoformat(),
                    'description': event.description,
                    'event_type': event.event_type,
                    'event_color': event.event_color,
                    'creator': User.query.get(event.creator_id).username
                })
            return jsonify(events_list)
        except Exception as e:
            current_app.logger.error(f"Error fetching events: {str(e)}")
            return jsonify({"error": str(e)}), 500

    @application.route('/settings/google-form-link')
    def get_google_form_link():
        google_form_link = "https://docs.google.com/forms/d/e/1FAIpQLSeOjs5WVTtI2n2jXxi0duBsEUF10bR-UdW81gRtAvODBGL4Dw/viewform?usp=sf_link"
        return jsonify({'google_form_link': google_form_link})

    @application.route('/update-google-form', methods=['POST'])
    @login_required
    @admin_required
    def update_google_form():
        new_link = request.form.get('googleFormLink')
        settings = Settings.query.first()
        settings.google_form_link = new_link
        db.session.commit()
        flash('Google Form link updated successfully.')
        return redirect(url_for('admin_dashboard'))

    @application.route('/housepoint-form')
    @login_required
    def housepoint_form():
        return render_template('user_homepage.html', page='housepoint-form')

