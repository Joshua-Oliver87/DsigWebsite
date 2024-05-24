import os
from flask import Flask, current_app
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_babel import Babel
from apscheduler.schedulers.background import BackgroundScheduler
import pandas as pd
from google.oauth2 import service_account
from googleapiclient.discovery import build
from .shared import data

db = SQLAlchemy()
login_manager = LoginManager()
babel = Babel()
scheduler = BackgroundScheduler()

basedir = os.path.abspath(os.path.dirname(__file__))

def get_sheet_data(creds, sheet_id, sheet_range):
    service = build('sheets', 'v4', credentials=creds)
    sheet = service.spreadsheets()
    result = sheet.values().get(spreadsheetId=sheet_id, range=sheet_range).execute()
    values = result.get('values', [])
    df = pd.DataFrame(values[1:], columns=values[0])
    return df
def update_data():
    global data
    SERVICE_ACCOUNT_FILE = 'd-sig-housepoints-674a5d8c6fde.json'
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']
    creds = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    SHEET_ID = '1--V44WfrFGoAnxeA_1FF8Ut7fO3KXGUO-hHHjVgxY4o'
    SHEET_RANGE = 'Sheet1!A:Z'

    df = get_sheet_data(creds, SHEET_ID, SHEET_RANGE)
    user_id = 1  # Example user ID, you can replace it with dynamic user ID
    user_data = df[df['UserID'] == str(user_id)]
    data.update({
        'Brotherhood Event': user_data['Brotherhood'].values[0] if not user_data.empty else 0,
        'Wet Event': user_data['Wet'].values[0] if not user_data.empty else 0,
        'Exchanges': user_data['Exchanges'].values[0] if not user_data.empty else 0,
        'Philanthropy': user_data['Philanthrophy'].values[0] if not user_data.empty else 0,
        'Programming': user_data['Programming'].values[0] if not user_data.empty else 0,
        'Community Service': user_data['Community Service'].values[0] if not user_data.empty else 0,
    })
    print("Data updated:", data)  #debugging


def init_scheduler(app):
    if not scheduler.running:
        scheduler.add_job(func=update_data, trigger="interval", minutes=5)
        scheduler.start()
        update_data()
    return scheduler

def create_app():
    basedir = os.path.abspath(os.path.dirname(__file__))
    template_dir = os.path.abspath(os.path.join(basedir, 'View', 'templates'))
    static_dir = os.path.abspath(os.path.join(basedir, 'View', 'static'))

    app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)

    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'instance', 'my_database.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.secret_key = os.urandom(24)

    db.init_app(app)
    login_manager.init_app(app)
    babel.init_app(app)

    with app.app_context():
        from app.Controller.routes import register_routes
        register_routes(app)
        from app.Model.models import User, Event, EventForm, Settings
        db.create_all()

    return app

flask_app = create_app()