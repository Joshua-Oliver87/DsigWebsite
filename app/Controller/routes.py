from datetime import datetime
import os
from flask import render_template, redirect, url_for, request, flash, jsonify, current_app, abort
from flask_login import current_user, login_user, logout_user, login_required
from jinja2 import TemplateNotFound
from werkzeug.security import generate_password_hash
from app import db, login_manager
from app.Model.models import User, Event, EventForm, Settings
from app.Controller.admin_decorator import admin_required
from app.shared import data

def register_routes(application):
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

            if not email.endswith('@wsu.edu'):
                flash('Please use your WSU email address to register.')
                return redirect(url_for('login'))

            existing_user = User.query.filter_by(username=username).first()
            if existing_user:
                flash('Username already taken. Please choose a different one.')
                return redirect(url_for('register'))

            hashed_password = generate_password_hash(password)
            new_user = User(username=username, email=email, password_hash=hashed_password)
            new_user.is_approved = False
            db.session.add(new_user)
            db.session.commit()
            flash('Registration pending.')
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
                flash("Logged in successfully.")
                return redirect(url_for('user_homepage'))
            else:
                flash("Invalid username or password.")

        return render_template('login.html')

    @application.route('/logout')
    def logout():
        logout_user()
        return redirect(url_for('welcome'))

    @application.route('/user_homepage')
    @login_required
    def user_homepage():
        print("Data being passed to template:", data)
        return render_template('user_homepage.html', data=data)

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
        return jsonify({"message": "Event added successfully", "status": "success"})

    @application.route('/delete-event', methods=['POST'])
    @login_required
    def delete_event():
        if not current_user.canCreateEvents:
            flash('You do not have permission to edit the calendar.')
            return redirect(url_for('calendar_view'))
        event_id = request.form.get('event_id')
        event_to_delete = Event.query.get(event_id)
        if event_to_delete:
            db.session.delete(event_to_delete)
            db.session.commit()
            return jsonify({"message": "Event deleted successfully", "status": "success"})
        else:
            return jsonify({"message": "Event not found", "status": "error"}), 404

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
        if not current_user.can_create_events:
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
                event_color=form.event_color.data  # Assuming your Event model has an event_color field
            )
            db.session.add(event)
            try:
                db.session.commit()
                flash('Event created successfully!')
            except Exception as e:
                flash('An error occurred while saving the event: ' + str(e))
                db.session.rollback()
            return redirect(url_for('calendar_view'))

        return render_template('create_event.html', form=form)

        @application.route('/fetch-events')
        @login_required
        def fetch_events():
            events = Event.query.all()
            events_data = []
            for event in events:
                events_data.append({
                    'id': event.id,
                    'title': event.title,
                    'start': event.start.isoformat(),
                    'end': event.end.isoformat(),
                    'description': event.description,
                    'creator': event.creator.username,
                    'event_color': event.event_color,
                    'event_type': event.event_type,
                })
            return jsonify(events_data)

        @application.route('/settings/google-form-link')
        def get_google_form_link():
            google_form_link = Settings.get_google_form_link()
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

    def register_routes(app):
        with app.app_context():
            register_routes(app)


