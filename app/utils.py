import logging
import pandas as pd
from google.cloud import storage
from googleapiclient.discovery import build
from flask import Flask, current_app
from apscheduler.schedulers.background import BackgroundScheduler

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

def get_image_url(blob_name):
    storage_client = storage.Client()
    bucket_name = current_app.config['CLOUD_STORAGE_BUCKET']
    bucket = storage_client.bucket(bucket_name)

    if not bucket_name:
        logging.error("CLOUD_STORAGE_BUCKET environment variable is not set.")
        return None

    if not blob_name:
        logging.info("No profile picture set, using default profile picture.")
        blob_name = 'defaultProfilePicture.jpeg'  # Ensure you have this file in your bucket

    blob = bucket.blob(blob_name)
    return blob.public_url
