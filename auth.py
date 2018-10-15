# -*- coding: utf-8 -*-

import os
import flask
import requests
from flask import request,jsonify
from send_response import SendResponse
import json
from receipt_detector import is_receipt


import google.oauth2.credentials
import google_auth_oauthlib.flow
from gmail_connector import get_receipts
import googleapiclient.discovery
from httplib2 import Http

# This variable specifies the name of a file that contains the OAuth 2.0
# information for this application, including its client_id and client_secret.
CLIENT_SECRETS_FILE = "client_secret.json"

# This OAuth 2.0 access scope allows for full read/write access to the
# authenticated user's account and requires requests to use an SSL connection.
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
API_SERVICE_NAME = 'email'
API_VERSION = 'v1'

app = flask.Flask(__name__)
# Note: A secret key is included in the sample so that it works.
# If you use this code in your application, replace this with a truly secret
# key. See http://flask.pocoo.org/docs/0.12/quickstart/#sessions.
app.secret_key = 'myreallysecrectsecret'

def has_args(iterable, args):
    """Verify that all args are in the iterable."""

    try:
        return all(x in iterable for x in args)

    except TypeError:
        return False

@app.route('/')
def index():
  return print_index_table()

@app.errorhandler(SendResponse)
def handle_invalid_usage(error):
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response

@app.route('/get_outlook_receipts', methods=['POST'])
def get_outlook_receipts():

    if not has_args(request.args, ['start_date','end_date']):
        raise SendResponse("Please provide start_date and end_date as request paramaters (i.e. 'get_outlook_receipts?start_date=2015-04-01&end_date=2017-01-01' ")

    auth_err = "You must provide an Authorization header in the form of 'Bearer {YOUR MS GRAPH ACCESS TOKEN}"
    if "authorization" not in request.headers:
        raise SendResponse(auth_err)

    authorization = request.headers['Authorization']

    if authorization.split(' ')[0] and authorization.split(' ')[0] == 'Bearer' and authorization.split(' ')[1]:
        access_token = authorization.split(' ')[1]
    else:
        raise SendResponse(auth_err)

    date_range = "?$filter=ReceivedDateTime ge " + request.args['start_date'] + " and receivedDateTime lt " + request.args['end_date']
    endpoint = "https://graph.microsoft.com/v1.0/me/messages"  + date_range

    headers = {
        'authorization': "Bearer " + access_token,
        'cache-control': "no-cache",
    }

    graphdata = json.loads(requests.request("GET", endpoint, headers=headers).text)
    if 'error' in graphdata:
        raise SendResponse(json.dumps(graphdata))

    receipts=[]
    while True:
        if '@odata.nextLink' in graphdata:
            endpoint = graphdata['@odata.nextLink']
            graphdata = json.loads(requests.request("GET", endpoint, headers=headers).text)
            for mail in graphdata['value']:
                if 'subject' in mail:
                    if is_receipt(mail['subject'].lower()):
                        receipts.append({ 'subject' : mail['subject'], 'body' : mail['body']})
        else:
            break


    return json.dumps(receipts)


@app.route('/get_gmail_receipts', methods=['POST'])
def get_gmail_receipts():

  if "date_range" not in request.args:
    raise SendResponse('Please provide the date_range query parameters (example: date_range=after:2018/09/03+before:2018/10/3')

  if not has_args(request.json, ['scopes','token_uri','token','client_id','client_secret','refresh_token']):
    raise SendResponse("Please provide gmail scopes,token_uri,token,client_id,client_secret,refresh_token within the body of your post request. For example: {'scopes': ['https://www.googleapis.com/auth/gmail.readonly'], 'token_uri': 'https://www.googleapis.com/oauth2/v3/token', 'token': 'ya29.GlsrBvAlmmclOSbNuOe9QmrxLaEWe3t-W7uvaaDsM8oR4G3E2dOp-h70QX84X8mn96rKsJNwnpZQIbl78qGlKEQSBBumPHWlT5ifeUxpecuqJ0iXoYh7RuROBMMA', 'client_id': u'969545104751-3cc95edgshu2bstroubelbu789vd9f68.apps.googleusercontent.com', u'client_secret': 'INqCxZox_qa7o40Ja1TBRpRp', 'refresh_token': u'1/ngq9AA0Jssnc4O_FG64c9CIDULF3SdkwrJ-U2UolS28' ")

  creds = request.json
  date_range = request.args['date_range']
  # Load credentials from the session.

  try:

    credentials = google.oauth2.credentials.Credentials(**creds)

    response = get_receipts(creds,date_range)

   # flask.session[credentials.token] = credentials_to_dict(credentials)
  except Exception as e:
    print(e)
    raise SendResponse(str(e), 500)

  return flask.jsonify(response)  #{ 'token' :credentials.token })


@app.route('/authorize')
def authorize():
  # Create flow instance to manage the OAuth 2.0 Authorization Grant Flow steps.
  flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
      CLIENT_SECRETS_FILE, scopes=SCOPES)

  flow.redirect_uri = flask.url_for('oauth2callback', _external=True)

  authorization_url, state = flow.authorization_url(
      # Enable offline access so that you can refresh an access token without
      # re-prompting the user for permission. Recommended for web server apps.
      access_type='offline',
      # Enable incremental authorization. Recommended as a best practice.
      include_granted_scopes='true')

  # Store the state so the callback can verify the auth server response.
  flask.session['state'] = state

  return flask.redirect(authorization_url)


@app.route('/oauth2callback')
def oauth2callback():
  # Specify the state when creating the flow in the callback so that it can
  # verified in the authorization server response.
  state = flask.session['state']

  flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
      CLIENT_SECRETS_FILE, scopes=SCOPES, state=state)

  flow.redirect_uri = flask.url_for('oauth2callback', _external=True)

  # Use the authorization server's response to fetch the OAuth 2.0 tokens.
  authorization_response = flask.request.url
  flow.fetch_token(authorization_response=authorization_response)

  # Store credentials in the session.
  # ACTION ITEM: In a production app, you likely want to save these
  #              credentials in a persistent database instead.
  credentials = flow.credentials
  flask.session[credentials.token] = credentials_to_dict(credentials)

  return flask.jsonify({ 'credentials' :credentials })


@app.route('/revoke')
def revoke():
  if 'credentials' not in flask.session:
    return ('You need to <a href="/authorize">authorize</a> before ' +
            'testing the code to revoke credentials.')

  credentials = google.oauth2.credentials.Credentials(
    **flask.session['credentials'])

  revoke = requests.post('https://accounts.google.com/o/oauth2/revoke',
      params={'token': credentials.token},
      headers = {'content-type': 'application/x-www-form-urlencoded'})

  status_code = getattr(revoke, 'status_code')
  if status_code == 200:
    return('Credentials successfully revoked.' + print_index_table())
  else:
    return('An error occurred.' + print_index_table())


@app.route('/clear')
def clear_credentials():
  if 'credentials' in flask.session:
    del flask.session['credentials']
  return ('Credentials have been cleared.<br><br>' +
          print_index_table())


def credentials_to_dict(credentials):
  return {'token': credentials.token,
          'refresh_token': credentials.refresh_token,
          'token_uri': credentials.token_uri,
          'client_id': credentials.client_id,
          'client_secret': credentials.client_secret,
          'scopes': credentials.scopes}

def print_index_table():
  return ('<table>' +
          '<tr><td><a href="/test">Test an API request</a></td>' +
          '<td>Submit an API request and see a formatted JSON response. ' +
          '    Go through the authorization flow if there are no stored ' +
          '    credentials for the user.</td></tr>' +
          '<tr><td><a href="/authorize">Test the auth flow directly</a></td>' +
          '<td>Go directly to the authorization flow. If there are stored ' +
          '    credentials, you still might not be prompted to reauthorize ' +
          '    the application.</td></tr>' +
          '<tr><td><a href="/revoke">Revoke current credentials</a></td>' +
          '<td>Revoke the access token associated with the current user ' +
          '    session. After revoking credentials, if you go to the test ' +
          '    page, you should see an <code>invalid_grant</code> error.' +
          '</td></tr>' +
          '<tr><td><a href="/clear">Clear Flask session credentials</a></td>' +
          '<td>Clear the access token currently stored in the user session. ' +
          '    After clearing the token, if you <a href="/test">test the ' +
          '    API request</a> again, you should go back to the auth flow.' +
          '</td></tr></table>')


if __name__ == '__main__':
  # When running locally, disable OAuthlib's HTTPs verification.
  # ACTION ITEM for developers:
  #     When running in production *do not* leave this option enabled.
  os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

  # Specify a hostname and port that are set as a valid redirect URI
  # for your API project in the Google API Console.
  app.run('localhost', 8080, debug=True)

