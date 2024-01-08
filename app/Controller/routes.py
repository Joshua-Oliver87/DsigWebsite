from datetime import datetime
from flask import render_template, redirect, url_for, request, flash, get_flashed_messages, abort, jsonify
from flask_login import current_user, login_user, logout_user, login_required
from jinja2 import TemplateNotFound
from werkzeug.security import generate_password_hash
from app import flask_app, db, login_manager
from app.Model.models import User, Event, EventForm
from app.Controller.admin_decorator import admin_required

@flask_app.route('/')
def welcome():
    return render_template('welcome.html')
@login_manager.user_loader
def load_user(user_id):
    user = User.query.get(int(user_id))
    if user and user.is_approved:
        return user
    return None

@property
def creator_name(self):
    return self.creator.username

@flask_app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        username = request.form['username']
        password = request.form['password']

        # Server-side validation to check if email ends in @wsu.edu
        if not email.endswith('@wsu.edu'):
            flash('Please use your WSU email address to register.');
            return redirect(url_for('login'));

        # Check if the username already exists
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Username already taken. Please choose a different one.')
            return redirect(url_for('register'))

        # Hash the password and create a new user
        hashed_password = generate_password_hash(password)
        new_user = User(username=username, email=email, password_hash=hashed_password)
        new_user.is_approved = False
        db.session.add(new_user)
        db.session.commit()
        flash('Registration pending.')
        return redirect(url_for('login'))

    return render_template('register.html')


@flask_app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('user_homepage'))

    if request.method == 'POST':
        username = request.form['username']  # Changed from 'email' to 'username'
        password = request.form['password']

        # Attempt to retrieve the user by their username
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

@flask_app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))
@flask_app.route('/user_homepage')
@login_required
def user_homepage():
    return render_template('user_homepage.html')

@flask_app.route('/admin/dashboard')
@login_required
@admin_required
def admin_dashboard():
    #Admin dashboard code
    return render_template('admin_dashboard.html')

@flask_app.route('/make_admin/<int:user_id>', methods=['POST'])
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

@flask_app.route('/calendar')
@login_required
def calendar_view():
    events = Event.query.all()
    canCreateEvents = current_user.canCreateEvents
    return render_template('partials/calendar.html', events=events, can_create_events=canCreateEvents)

@flask_app.route('/add-event', methods=['POST'])
@login_required
def add_event():
    if not current_user.canCreateEvents:
        flash('You do not have permission add events.')
        return jsonify({"message": "Permission denied", "status": "error"}), 403
    #Get data from request
    event_data = request.form
    new_event = Event(
        title=event_data.get('title'),
        description=event_data.get('description'),
        start=datetime.fromisoformat(event_data.get('start')),
        end=datetime.fromisoformat(event_data.get('end')),
        creator_id = current_user.id,
        event_type = event_data.get('event_type'),
        event_color = event_data.get('event_color'),
    )

    #Save event to the database
    db.session.add(new_event)
    db.session.commit()

    #Respond to client that request is good
    return jsonify({"message": "Event added successfully", "status": "success"})

@flask_app.route('/delete-event', methods=['POST'])
@login_required
#@admin calendar thing
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


# Assume you have a folder named 'partials' within the 'templates' directory
@flask_app.route('/partials/<content_name>.html')
@login_required
def partials(content_name):
    try:
        # Render the partial HTML for the requested content
        return render_template('partials/' + content_name + '.html')
    except TemplateNotFound:
        abort(404)  # Return a 404 if the template is not found


@flask_app.route('/calendar-content')
@login_required
def calendar_content():
    # This would return a partial HTML snippet containing the calendar.
    return render_template('partials/calendar.html')


@flask_app.route('/create-event', methods=['GET', 'POST'])
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
            # Format depending on your form's datetime format
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

@flask_app.route('/fetch-events')
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