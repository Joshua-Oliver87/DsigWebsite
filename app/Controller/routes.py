from flask import render_template, redirect, url_for, request, flash, get_flashed_messages
from flask_login import current_user, login_user, logout_user, login_required
from werkzeug.security import generate_password_hash
from app import flask_app, db, login_manager
from app.Model.models import User
from app.Controller.admin_decorator import admin_required

@flask_app.route('/')
def welcome():
    return render_template('welcome.html')
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

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
        db.session.add(new_user)
        db.session.commit()
        flash('Registration successful. Please log in.')
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