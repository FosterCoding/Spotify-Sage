from flask import Flask, request, redirect
import requests
import os
from dotenv import load_dotenv

load_dotenv()

# Grab credentials from .env file
ID = os.getenv('CLIENT_ID')
SECRET = os.getenv('CLIENT_SECRET')
REDIRECT_URL = "http://localhost:8888/callback"

app = Flask(__name__)

def get_auth_url(): # Uses Spotify's auth code flow which allows for user-specific data
    auth_url = (
        "https://accounts.spotify.com/authorize?"
        f"client_id={ID}&"
        "response_type=code&"
        f"redirect_uri={REDIRECT_URL}&"
        "scope=user-top-read"
    )
    return auth_url

def get_token_from_redirect(code): # Get URL from Flask and create the token
    url = "https://accounts.spotify.com/api/token"
    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URL,
        "client_id": ID,
        "client_secret": SECRET
    }

    print("Authorization code: {code}")


    response = requests.post(url, headers=headers, data=data)

    # Logging for better debugging
    print(f"Request Data: {data}")
    print(f"Response Status Code: {response.status_code}")
    print(f"Response Text: {response.text}")

    if response.status_code == 200:
        token_info = response.json()
        return token_info['access_token']
    else:
        raise Exception(f'Failed to get token: {response.status_code} {response.text}')

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
        token = get_token_from_redirect(code) #Grabs the code and adds it to a temporary file named access_token.txt
        # Save the token to a file
        with open('access_token.txt', 'w') as f:
            f.write(token)
        return 'Authorization complete. You can close this window.'
    except Exception as e:
        return f'Error during token exchange: {str(e)}'

if __name__ == '__main__':
    app.run(port=8888)
