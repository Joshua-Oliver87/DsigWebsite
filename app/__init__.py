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
from google.cloud import storage
import logging
from .config import Config

db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()
babel = Babel()
scheduler = BackgroundScheduler()

basedir = os.path.abspath(os.path.dirname(__file__))

def get_sheet_data(creds, sheet_id, sheet_range):
    logging.info("Fetching data from Google Sheets...")
    service = build('sheets', 'v4', credentials=creds)
    sheet = service.spreadsheets()
    result = sheet.values().get(spreadsheetId=sheet_id, range=sheet_range).execute()
    values = result.get('values', [])

    if values:
        header = values[0]
        rows = values[1:]
        df = pd.DataFrame(rows, columns=header)
        logging.info(f"Data fetched: {df.head()}")
    else:
        df = pd.DataFrame()
        logging.info("No data found in the specified range.")

    return df

def update_data():
    global data
    SERVICE_ACCOUNT_FILE = 'd-sig-housepoints-674a5d8c6fde.json'
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']
    creds = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    SHEET_ID = '1--V44WfrFGoAnxeA_1FF8Ut7fO3KXGUO-hHHjVgxY4o'
    SHEET_RANGE = 'HSPT Totals!A:Z'

    df = get_sheet_data(creds, SHEET_ID, SHEET_RANGE)

    if data is None:
        data = {}

    for _, row in df.iterrows():
        email = row['Email']
        if pd.notnull(email):
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

def init_scheduler(app):
    with app.app_context():
        scheduler.add_job(func=update_data, trigger="interval", minutes=5)

    scheduler.start()
    update_data()
    return scheduler

def create_app():
    basedir = os.path.abspath(os.path.dirname(__file__))
    template_dir = os.path.abspath(os.path.join(basedir, 'View', 'templates'))
    static_dir = os.path.abspath(os.path.join(basedir, 'View', 'static'))

    app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)
    app.config.from_object(Config)

    app.config['ENV'] = 'development'
    app.config['DEBUG'] = True

    logging.debug(f"CLOUD_STORAGE_BUCKET: {os.getenv('CLOUD_STORAGE_BUCKET')}")
    logging.debug(f"GOOGLE_APPLICATION_CREDENTIALS: {os.getenv('GOOGLE_APPLICATION_CREDENTIALS')}")

    @app.context_processor
    def utility_processor():
        def get_image_url(blob_name):
            storage_client = storage.Client()
            bucket_name = current_app.config['CLOUD_STORAGE_BUCKET']
            bucket = storage_client.bucket(bucket_name)
            if not bucket_name:
                logging.error("CLOUD_STORAGE_BUCKET environment variable is not set.")
            else:
                logging.info(f"CLOUD_STORAGE_BUCKET is set to: {bucket_name}")
            blob = bucket.blob(blob_name)
            return blob.public_url

        return dict(get_image_url=get_image_url)

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
