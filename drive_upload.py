#!/usr/bin/python

import httplib2
import pprint

from apiclient.discovery import build
from apiclient.http import MediaFileUpload
from oauth2client.client import OAuth2WebServerFlow


def run():
    # Copy your credentials from the console
    CLIENT_ID = '836063683607-uarkc1vslg7rms30e4a5bqi11u384dlk.apps.googleusercontent.com'
    CLIENT_SECRET = '9dAUI6uin5sap-fBrWID0QGB'

    # Check https://developers.google.com/drive/scopes for all available scopes
    OAUTH_SCOPE = 'https://www.googleapis.com/auth/drive'

    # Redirect URI for installed apps
    REDIRECT_URI = 'urn:ietf:wg:oauth:2.0:oob'

    # Path to the file to upload
    FILENAME = 'games.csv'

    # Run through the OAuth flow and retrieve credentials
    flow = OAuth2WebServerFlow(CLIENT_ID, CLIENT_SECRET, OAUTH_SCOPE, REDIRECT_URI)
    authorize_url = flow.step1_get_authorize_url()
    print 'Go to the following link in your browser: ' + authorize_url
    code = raw_input('Enter verification code: ').strip()
    credentials = flow.step2_exchange(code)

    # Create an httplib2.Http object and authorize it with our credentials
    http = httplib2.Http()
    http = credentials.authorize(http)

    drive_service = build('drive', 'v2', http=http)

    # Insert a file
    media_body = MediaFileUpload(FILENAME, mimetype='text/csv', resumable=True)
    body = {
        'title': 'Gameslist',
        'description': "A list of Dan's games.",
        'mimeType': 'text/csv'
    }

    request = drive_service.files().insert(body=body, media_body=media_body)
    request.uri += '&convert=true'
    response = request.execute()

if __name__ == '__main__':
    run()
