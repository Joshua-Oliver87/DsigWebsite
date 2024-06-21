import os
from flask import Flask, current_app
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, current_user
from flask_babel import Babel
from apscheduler.schedulers.background import BackgroundScheduler
import pandas as pd
from google.oauth2 import service_account
from googleapiclient.discovery import build
from .shared import data
from app.Model.models import User
from flask_migrate import Migrate


db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()
babel = Babel()
scheduler = BackgroundScheduler()



basedir = os.path.abspath(os.path.dirname(__file__))


def get_sheet_data(creds, sheet_id, sheet_range):
    service = build('sheets', 'v4', credentials=creds)
    sheet = service.spreadsheets()
    result = sheet.values().get(spreadsheetId=sheet_id, range=sheet_range).execute()
    values = result.get('values', [])

    # Print the fetched values for debugging
    print("Fetched values:", values)

    if values:
        header = values[0]
        rows = values[1:]
        print("Header:", header)
        print("Number of columns in header:", len(header))
        for row in rows:
            print("Row:", row)
            print("Number of columns in row:", len(row))

        df = pd.DataFrame(rows, columns=header)
    else:
        df = pd.DataFrame()

    return df


def update_data():
    global data
    SERVICE_ACCOUNT_FILE = 'd-sig-housepoints-674a5d8c6fde.json'
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']
    creds = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    SHEET_ID = '1--V44WfrFGoAnxeA_1FF8Ut7fO3KXGUO-hHHjVgxY4o'
    SHEET_RANGE = 'HSPT Totals!A:Z'

    # Fetch the data
    df = get_sheet_data(creds, SHEET_ID, SHEET_RANGE)

    # Initialize the data dictionary if it's None
    if data is None:
        data = {}

    # Process the data
    for _, row in df.iterrows():
        email = row['Email']
        if pd.notnull(email):  # Ensure the email is not null
            user_data = {
                'Brotherhoods': row.get('Brotherhoods', 0),
                'Social Events': row.get('Social Events', 0),
                'Philanthropy': row.get('Philanthropy', 0),
                'Recruitment Events': row.get('Recruitment Events', 0),
                'Programming': row.get('Programming', 0),
                'Community Service': row.get('Community Service', 0),
                'Other': row.get('Other', 0)
            }
            data[email] = user_data

    print("Updated data:", data)



def init_scheduler(app):
    with app.app_context():
        all_users = User.query.all()
        # Schedule the job without passing any args
        scheduler.add_job(func=update_data, trigger="interval", minutes=5)

    scheduler.start()
    # Call update_data once immediately to initialize data
    update_data()
    return scheduler

def create_app():
    basedir = os.path.abspath(os.path.dirname(__file__))
    template_dir = os.path.abspath(os.path.join(basedir, 'View', 'templates'))
    static_dir = os.path.abspath(os.path.join(basedir, 'View', 'static'))

    app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)

    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'instance', 'my_database.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['UPLOAD_FOLDER'] = os.path.join(basedir, '..', 'UploadedProfilePictures')
    app.secret_key = os.urandom(24)

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    with app.app_context():
        from app.Controller.routes import register_routes
        register_routes(app)
        from app.Model.models import User, Event, EventForm, Settings
        db.create_all()

    return app

flask_app = create_app()

