from __future__ import print_function
# pypeteer
import asyncio
from pyppeteer import launch

import os, time, argparse
import datetime, requests
from datetime import date
from bs4 import BeautifulSoup

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Magister settings
base_url = "YOURSCHOOL.magister.net"
username = "YOUR_USERNAME"
password = "YOUR_PASSWORD"

# Set arguments
parser = argparse.ArgumentParser(description='Magister2Google. Script to sync your magister schedule to Google')
parser.add_argument('-c', action='store', help='Specify a calendar. Default is primary')
parser.add_argument('-d', action='store', help='Specify days to sync. Default is 30')

args = parser.parse_args()

if args.c:
    Calendarid = args.c
else:
    Calendarid = 'primary'
if args.d:
    days = int(args.d)
else:
    days = 30

# Set the scope for Google Calendar API
SCOPES = ['https://www.googleapis.com/auth/calendar.events']

# Magister login Pyppeteer
async def interceptResponse(request):
    if request.url == f"https://{base_url}/api/m6/applicatietoegang":
        global headers
        headers = request.headers
async def main():
    browser = await launch({"headless": True, "args": ["--start-maximized"]})
    page = await browser.newPage()
    #await page.setRequestInterception(True)

    await page.goto(f"https://{base_url}")
    # locate the search box
    entry_box = await page.waitForXPath("""//*[@id="username"]""")

    await entry_box.type(username)
    await asyncio.sleep(1)
    await page.click('button')
    entry_box = await page.waitForXPath("""//*[@id="password"]""")
    await entry_box.type(password)
    await asyncio.sleep(1)

    await page.click('#password_submit')
    page.on('request',
            lambda request: asyncio.ensure_future(interceptResponse(request)))
    await asyncio.sleep(1)
    await browser.close()
print("Logging in to Magister...")
asyncio.get_event_loop().run_until_complete(main())





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
    service = build('calendar', 'v3', credentials=creds)
    # Get Magister schedule 4 weeks?
    s = requests.Session()
    try:
        r = s.get(f"https://{base_url}/api/account", headers=headers).json()
        print(f"Hi {r['Persoon']['Roepnaam']} ")

    except requests.exceptions.ConnectionError:
        print("Please enter a valid magister base url")
        exit(1)
    if r == "Invalid Operation":
        print("Magister Bearer token expiered")
        exit(1)
    # Set the dates
    today = datetime.date.today()
    date_today = today.strftime("%Y-%m-%d")
    date_1_month = today + datetime.timedelta(days=days)
    date_1_month = date_1_month.strftime("%Y-%m-%d")

    # Get schedule from Magister
    data = s.get(f"https://{base_url}/api/personen/{r['Persoon']['Id']}/afspraken?status=1&van={date_today}&tot={date_1_month}", headers=headers).json()
    print(f"Found {len(data['Items'])} events")
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


        try:
            # Send data to google if not already exists
            create_event(event, creds, item['Start'], item['Omschrijving'],service)
            print(f"Syncing {item['Omschrijving']}")
            time.sleep(1)
        except HttpError:
            # update event with new info
            patch_event(event, creds, item['Start'], item['Omschrijving'], hash,service)
            print(f"Updating {item['Omschrijving']}")
            time.sleep(0.6)

    print("Done.")
def create_event(event, creds, event_start, description,service):
    event = service.events().insert(calendarId=Calendarid, body=event).execute()
    print
    'Event created: %s' % (event.get('htmlLink'))

def patch_event(event, creds, event_start, description, id,service):
    # Check for existing events

    event = service.events().patch(calendarId=Calendarid, body=event, eventId=id).execute()
    print
    'Event created: %s' % (event.get('htmlLink'))
        
if __name__ == '__main__':
    main()


