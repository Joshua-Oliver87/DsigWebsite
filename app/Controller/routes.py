from datetime import datetime, timezone, timedelta
import pytz
from flask import (
    render_template, redirect, url_for, request, flash, jsonify, current_app,
    abort, send_from_directory, g, make_response, session
)
from flask_login import current_user, login_user, logout_user, login_required
from jinja2 import TemplateNotFound
from werkzeug.security import generate_password_hash
from app import db, login_manager, update_data, scheduler
from app.Model.models import User, Event, EventForm, Settings
from app.Controller.admin_decorator import admin_required
from app.shared import data
from sqlalchemy.exc import InvalidRequestError
import os
from werkzeug.utils import secure_filename
import logging
from google.cloud import storage
from PIL import Image
from io import BytesIO

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
UPLOAD_FOLDER = os.path.join(os.path.abspath(os.path.dirname(__file__)), '../../uploadedProfilePictures')

logging.basicConfig(level=logging.DEBUG)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def register_routes(application):
    application.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

    @application.before_request
    def detect_app_request():
        user_agent = request.headers.get('User-Agent', '')
        g.is_app = "median" in user_agent  # Flag to identify app requests
        if g.is_app:
            # Set session to be permanent to keep app users logged in
            session.permanent = True
            application.permanent_session_lifetime = timedelta(days=30)
    @application.context_processor
    def utility_processor():
        def get_image_url(blob_name):
            if not blob_name:
                logging.info("No profile picture set, using default profile picture.")
                return url_for('static', filename='images/defaultProfilePicture.jpeg')

            storage_client = storage.Client()
            bucket_name = current_app.config['CLOUD_STORAGE_BUCKET']
            bucket = storage_client.bucket(bucket_name)
            blob = bucket.blob(blob_name)

            if blob.exists():
                logging.info(f"Serving profile picture from URL: {blob.public_url}")
                return blob.public_url
            else:
                logging.warning(f"Blob {blob_name} does not exist. Using default profile picture.")
                return url_for('static', filename='images/defaultProfilePicture.jpeg')

        return dict(get_image_url=get_image_url)

    @application.route('/uploads/<filename>')
    def uploaded_file(filename):
        bucket_name = application.config['CLOUD_STORAGE_BUCKET']
        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(f'images/{filename}')  # Adjusted to point to the 'images' folder if needed

        if blob.exists():
            image_url = blob.public_url
            return redirect(image_url)
        else:
            # If the blob doesn't exist, serve the default profile picture
            default_image_url = url_for('static', filename='images/defaultProfilePicture.jpeg')
            return redirect(default_image_url)

    @application.route('/upload_profile_picture', methods=['POST'])
    @login_required
    def upload_profile_picture():
        if 'profile_picture' not in request.files:
            logging.debug('No file part in request')
            return jsonify({'success': False, 'message': 'No file part'})

        file = request.files['profile_picture']
        if file.filename == '' or not allowed_file(file.filename):
            logging.debug('Invalid file')
            return jsonify({'success': False, 'message': 'Invalid file'})

        filename = secure_filename(f"{current_user.id}_{file.filename}")
        image = Image.open(file).resize((100, 100), Image.LANCZOS)
        image_io = BytesIO()
        image.save(image_io, format=image.format or 'PNG')
        image_io.seek(0)

        bucket = storage.Client().bucket(application.config['CLOUD_STORAGE_BUCKET'])
        blob = bucket.blob(f"images/{filename}")
        blob.upload_from_file(image_io, content_type=file.content_type)

        if not blob.exists():
            logging.error(f"Failed to upload to {bucket.name}/images/{filename}")
            return jsonify({'success': False, 'message': 'Upload failed'})

        current_user.profile_picture = f"https://storage.googleapis.com/{bucket.name}/images/{filename}"
        db.session.merge(current_user)
        db.session.commit()
        return jsonify({'success': True, 'image_url': current_user.profile_picture})

    @application.route('/')
    def welcome():
        return render_template('welcome.html')

    @login_manager.user_loader
    def load_user(user_id):
        user = User.query.get(int(user_id))
        if user and user.is_approved:
            logging.debug(f"Loaded user {user.id} with profile picture URL: {user.profile_picture}")
            return user
        logging.debug(f"User {user_id} not found or not approved.")
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

    @application.route('/fetch-todays-events', methods=['GET'])
    @login_required
    def fetch_todays_events():
        local_tz = pytz.timezone('America/Los_Angeles')  # Set to your local timezone
        today = datetime.now(local_tz).date()

        # Correct way to get start and end of the day in local timezone
        start_of_day = datetime(today.year, today.month, today.day, 0, 0, 0, tzinfo=local_tz)
        end_of_day = datetime(today.year, today.month, today.day, 23, 59, 59, 999999, tzinfo=local_tz)

        current_app.logger.info(f"Fetching events for today: {today}")
        current_app.logger.info(f"Start of day (local time): {start_of_day}")
        current_app.logger.info(f"End of day (local time): {end_of_day}")

        # Adjusted query to include events that overlap with the current day
        events = Event.query.filter(Event.start <= end_of_day, Event.end >= start_of_day).all()
        events_data = []
        for event in events:
            events_data.append({
                'id': event.id,
                'title': event.title,
                'start': event.start.astimezone(local_tz).strftime('%H:%M'),
                'end': event.end.astimezone(local_tz).strftime('%H:%M'),
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
        profile_picture_url = current_user.profile_picture or url_for('static', filename='images/defaultProfilePicture.jpeg')
        user_data['profile_picture_url'] = profile_picture_url
        logging.debug(f"Data being passed to template: {user_data}")
        todays_events = fetch_todays_events().json
        print("Data being passed to template:", user_data)
        return render_template('user_homepage.html', data=user_data, events=todays_events, page='homepage')

    @application.route('/manual-update', methods=['GET'])
    def manual_update():
        update_data()
        return "Data updated manually!"

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

    @application.route('/delete-event', methods=['POST'])
    @login_required
    def delete_event():
        if not current_user.canCreateEvents:
            return jsonify({"message": "You do not have permission to delete events.", "status": "error"}), 403

        event_id = request.form.get('event_id')

        if not event_id:
            return jsonify({"message": "Event ID is required", "status": "error"}), 400

        try:
            with db.session.no_autoflush:
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

    @application.route('/add-event', methods=['POST'])
    @login_required
    def add_event():
        event_data = request.form
        current_app.logger.info(f"Received event data: {event_data}")

        start_time = datetime.fromisoformat(event_data.get('start')).replace(tzinfo=timezone.utc)
        end_time = datetime.fromisoformat(event_data.get('end')).replace(tzinfo=timezone.utc)

        new_event = Event(
            title=event_data.get('title'),
            description=event_data.get('description'),
            start=start_time,
            end=end_time,
            creator_id=current_user.id,
            event_type=event_data.get('event_type'),
            event_color=event_data.get('event_color'),
        )
        db.session.add(new_event)
        db.session.commit()
        current_app.logger.info(f"Added event: {new_event}")
        return jsonify({"message": "Event added successfully", "status": "success", "event_id": new_event.id})

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
                start=datetime.strptime(form.start.data, '%Y-%m-%d %H:%M:%S'),
                end=datetime.strptime(form.end.data, '%Y-%m-%d %H:%M:%S'),
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
            current_app.logger.info(f"Fetched events: {events_list}")  # Log the fetched events
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


    @application.route('/check-scheduler', methods=['GET'])
    def check_scheduler():
        jobs = scheduler.get_jobs()
        job_details = []
        for job in jobs:
            job_details.append({
                'id': job.id,
                'name': job.name,
                'next_run_time': job.next_run_time
            })
        logging.info(f"Scheduled jobs: {job_details}")
        return jsonify({"jobs": job_details})
