import logging
from google.oauth2 import service_account
from apscheduler.schedulers.background import BackgroundScheduler
import pandas as pd

scheduler = BackgroundScheduler()
def update_data():
    global data
    SERVICE_ACCOUNT_FILE = 'delta-sigma-phi-website-e19be0fb9757.json'
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']
    creds = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    SHEET_ID = '1--V44WfrFGoAnxeA_1FF8Ut7fO3KXGUO-hHHjVgxY4o'
    SHEET_RANGE = 'HSPT Totals!A:Z'

    logging.info("Updating data from Google Sheets...")
    df = get_sheet_data(creds, SHEET_ID, SHEET_RANGE)
    logging.info(f"Data fetched from Google Sheets: {df}")

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
    logging.info(f"Updated data: {data}")

def init_scheduler(app):
    logging.info("Initializing scheduler...")
    with app.app_context():
        job = scheduler.add_job(func=update_data, trigger="interval", minutes=10)
        logging.info(f"Scheduler job added: {job}")
    scheduler.start()
    logging.info("Scheduler started with jobs: {}".format(scheduler.get_jobs()))
    update_data()
    return scheduler
