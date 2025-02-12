from flask import current_app
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from flask_wtf import FlaskForm
from wtforms import StringField, DateTimeField, SelectField
from wtforms.validators import DataRequired
from .database import db
from google.cloud import storage


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key = True)
    username = db.Column(db.String(100), unique = True, nullable=False)
    email = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    is_admin = db.Column(db.Boolean, default = False, nullable=False)
    is_approved = db.Column(db.Boolean, default=False, nullable=False)
    canCreateEvents = db.Column(db.Boolean, default=False, nullable=False)
    profile_picture = db.Column(db.String(150), nullable=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


    @property
    def profile_picture_url(self):
        if self.profile_picture:
            bucket_name = current_app.config['delta-sigma-phi-website.appspot.com']
            return f"https://storage.googleapis.com/{bucket_name}/{self.profile_picture}"
        return "https://storage.googleapis.com/delta-sigma-phi-website.appspot.com/images/defaultProfilePicture.jpeg"


class Settings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    google_form_link = db.Column(db.String(255), nullable=False, default='')
    @classmethod
    def get_or_create(cls):
        settings = cls.query.first()
        if not settings:
            settings = cls()
            db.session.add(settings)
            db.session.commit()
        return settings
    @classmethod
    def get_google_form_link(cls):
        settings = cls.query.first()
        return settings.google_form_link if settings else ''

class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    start = db.Column(db.DateTime, nullable=False)
    end = db.Column(db.DateTime, nullable=False)
    creator_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    creator = db.relationship('User', backref='events')
    event_type = db.Column(db.String(50))
    event_color = db.Column(db.String(120))
class EventForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    description = StringField('Description')
    start = DateTimeField('Start Time', validators=[DataRequired()])
    end = DateTimeField('End Time', validators=[DataRequired()])
    event_type = SelectField('Type of Event', choices=[
        ('brotherhood', 'Brotherhood Event'),
        ('wet', 'Wet Event'),
        ('exchange', 'Exchange'),
        ('philanthropy', 'Philanthrophy'),
        ('programming', 'Programming'),
        ('community_service', 'Community Service'),
        ('other', 'Other'),
        # ... other event types ...
    ], validators=[DataRequired()])
    event_color = SelectField('Event Color', choices=[
        ('#0000FF', 'Blue'),
        ('#FFA500', 'Orange'),
        ('#FF0000', 'Red'),
        ('#80004C', 'Purple'), #this one
        ('#008000', 'Green'),
        ('#3498db', 'Light blue'),
        ('#808080', 'Grey'),
        # ... other color choices ...
    ], validators=[DataRequired()])