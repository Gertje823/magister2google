from __future__ import print_function

import os, time
import datetime, requests
from datetime import date
from bs4 import BeautifulSoup

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/calendar.events']

# Magister settings
base_url = "BASE_URL"
bearer_token = "TOKEN_HERE"


def main():

    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    # Get Magister schedule 4 weeks?
    s = requests.Session()
    headers = {'Authorization':f'Bearer {bearer_token}'}
    r = s.get(f"https://{base_url}/api/account", headers=headers).json()
    # Set the dates
    today = datetime.date.today()
    date_today = today.strftime("%Y-%m-%d")
    date_1_month = today + datetime.timedelta(days=30)
    date_1_month = date_1_month.strftime("%Y-%m-%d")

    # Get schedule from Magister
    data = s.get(f"https://{base_url}/api/personen/{r['Persoon']['Id']}/afspraken?status=1&van={date_today}&tot={date_1_month}", headers=headers).json()

    # Get all appointments and create an event
    for item in data['Items']:
        if item['Inhoud']:
            soup = BeautifulSoup(item['Inhoud'], 'lxml')
            description = soup.get_text()
        else:
            description = item['Omschrijving']
        hash = f"{item['Omschrijving']}{item['Start']}".encode("utf-8").hex()
        hash = f"{item['Start']}{item['Einde']}".encode("utf-8").hex()
        event = {
            'summary': item['Omschrijving'],
            'location': item['Lokatie'],
            'description': description,
            'id': hash,
            'status': 'confirmed',
            'start': {
                'dateTime': item['Start'],
                'timeZone': 'Europe/Amsterdam',
            },
            'end': {
                'dateTime': item['Einde'],
                'timeZone': 'Europe/Amsterdam',
            },

        }

        # Send data to google if not already exists
        try:
            create_event(event, creds, item['Start'], item['Omschrijving'])
            print(f"Syncing {item['Omschrijving']}")
        except HttpError:
            patch_event(event, creds, item['Start'], item['Omschrijving'], hash)
            print(f"Syncing {item['Omschrijving']}")
            time.sleep(1)

    print("Done.")
def create_event(event, creds, event_start, description):
    # Check for existing events
    service = build('calendar', 'v3', credentials=creds)

    event = service.events().insert(calendarId='primary', body=event).execute()
    print
    'Event created: %s' % (event.get('htmlLink'))

def patch_event(event, creds, event_start, description, id):
    # Check for existing events
    service = build('calendar', 'v3', credentials=creds)

    event = service.events().patch(calendarId='primary', body=event, eventId=id).execute()
    print
    'Event created: %s' % (event.get('htmlLink'))
        
if __name__ == '__main__':
    main()


