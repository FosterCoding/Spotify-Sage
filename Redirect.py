from flask import Flask, request, redirect
import requests
import os
from dotenv import load_dotenv
import json
import urllib.parse


load_dotenv()

# Grab credentials from .env file
ID = os.getenv('CLIENT_ID')
SECRET = os.getenv('CLIENT_SECRET')
REDIRECT_URL = "http://localhost:8888/callback"
AUTH_URL = 'https://accounts.spotify.com/authorize'
TOKEN_URL = 'https://accounts.spotify.com/api/token'

app = Flask(__name__)

@app.route('/')
def home():
    return 'Go to /login to authorize'

@app.route('/login')
def login():
    auth_url = get_auth_url()
    return redirect(auth_url)

@app.route('/callback')
def callback():
    code = request.args.get('code')
    if not code:
        return 'Authorization failed. No code received.'

    try:
        token = exchange_code_for_token(code)
        # Save the token for future use
        with open('access_token.txt', 'w') as f:
            f.write(token['access_token'])
        return 'Authorization complete. You can close this window.'
    except Exception as e:
        return f'Error during token exchange: {str(e)}'

def get_auth_url():
    params = {
        'client_id': ID,
        'response_type': 'code',
        'redirect_uri': REDIRECT_URL,
        'scope': 'user-top-read user-read-playback-state playlist-modify-public'
    }
    url = f"{AUTH_URL}?{urllib.parse.urlencode(params)}"
    return url

def exchange_code_for_token(code):
    data = {
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': REDIRECT_URL,
        'client_id': ID,
        'client_secret': SECRET
    }
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    response = requests.post(TOKEN_URL, data=data, headers=headers)
    response_data = response.json()

    if response.status_code != 200:
        raise Exception(f"Failed to get token: {response_data.get('error')}")

    return response_data

if __name__ == '__main__':
    app.run(port=8888)