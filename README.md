# Magister2Google
This is a script to sync your Magister Schedule to Google Calendar.

## How to use

 1. Create a Google Calender API key at https://console.cloud.google.com/
 2. Download the created credentials json file and save it as `credentials.json` in the directory of the script.
 3. Add your email address [here](https://console.cloud.google.com/apis/credentials/consent) under *test users*
 4. Put the base url  (school.magister.net) of your school at line 18
 5. Login to your magister account in the browser. Open the developer tools (f12) and look for any api request. Copy the Bearer token from the request header into the script (line 19)
 6. Run the script `python magister2google.py`. A browser window will open. Log in with your google account.

The script will sync the Magister schedule of the next 30 days to Google. 

##  Feature requests
 If you have any feature requests don't hesitate to open a issue :)