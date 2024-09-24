from dotenv import load_dotenv
import os
import requests
import logging
import webbrowser
import urllib.parse
from fpdf import FPDF
from requests_oauthlib import OAuth1


# Load ID and Secret from .env
load_dotenv()


# Grab credentials from .env file
ID = os.getenv('CLIENT_ID')
SECRET = os.getenv('CLIENT_SECRET')
#Redirect Url for the Flask Redirect.py
REDIRECT_URL = "http://localhost:8888/callback"
#Constants
AUTH_URL = 'https://accounts.spotify.com/authorize'
TOKEN_URL = 'https://accounts.spotify.com/api/token'
SCOPE = 'user-top-read user-read-playback-state playlist-modify-public'



# Check to make sure all credentials were grabbed
if not all([ID, SECRET]):
    raise ValueError("One or more API credentials are missing. Check env and proceed.")

# Setup logging to track errors and debugging
logging.basicConfig(
    level = logging.INFO,
    format = '%(asctime)s - %(levelname)s - %(message)s',
    datefmt = '%Y-%m-%d %H:%M:%S'
)

logger = logging.getLogger()
def get_auth_url(): #Uses Spotify's auth code flow which allows for user-specific data
    params = {
        'client_id': ID,
        'response_type': 'code',
        'redirect_uri': REDIRECT_URL,
        'scope': SCOPE
        #Adds the parameters that spotify needs to authenticate and details the permissions in SCOPE
    }
    url = f"{AUTH_URL}?{urllib.parse.urlencode(params)}"
    return url

def spotify_login():
    auth_url = get_auth_url() #Run the get_auth_url function and assign the output to auth_url variable
    webbrowser.open(auth_url)#Open the auth_url variable in a web browser
spotify_login()

def get_token_from_redirect(code): #get url from flask and create the token
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
    response = requests.post(url, headers=headers, data=data)

    print(f"Request Data: {data}")
    print(f"Response Status Code: {response.status_code}")
    print(f"Response Text: {response.text}")

    if response.status_code == 200:
        token_info = response.json()
        # Extract the access token
        access_token = token_info['access_token']
        # Save only the access token to the file
        with open('access_token.txt', 'w') as f:
            f.write(access_token)
        return access_token
    else:
        raise Exception(f'Failed to get token: {response.status_code} {response.text}')
def get_auth_header(token):
    return {
        "Authorization": f"Bearer {token}"
    }
def main():# Run the Flask app separately to handle the authorization and get the token
            # The Flask app should save the token in 'access_token.txt'
            # Read the access token obtained by the Flask app and strip it, assign it to the token vairable
            #Run the get_auth_header function and pass the token to it.
    try:
        # Read the access token obtained by the Flask app
        with open('access_token.txt', 'r') as f:
            token = f.read().strip()

        auth_header = get_auth_header(token)  # Create the auth header with the token

        # Fetch the stats
        user_stats = stats(auth_header)  #Assign the user_stats variable the results from the stats(auth_header): function below
        if user_stats:
            logger.info("Successfully fetched user stats")
            print(user_stats)

            # Export to PDF
            file_path = "D:/Programming Projects/Document Extractions/Spotify_Stats.pdf"
            export_to_pdf(user_stats, file_path)

    except Exception as e:
        logger.error(f"Error occurred: {e}")

def stats(auth_header):
    # Create empty lists for genres and artists
    genres = []
    artist = []
    top_tracks_data = []
    top_artists_data = []

    try:
        # Get top artists
        top_artists = requests.get(
            "https://api.spotify.com/v1/me/top/artists?limit=10",
            headers=auth_header
        )
        top_artists = top_artists.json()
        print("Top Artists Response:", top_artists)  # Debug output

        # Check for 'items' in top_artists response
        if 'items' in top_artists:
            for artist in top_artists['items']:
                genres.extend(artist.get('genres', []))
        else:
            logger.error("Top Artists response does not contain 'items'")

        # Get top tracks
        top_tracks = requests.get(
            "https://api.spotify.com/v1/me/top/tracks?limit=10",
            headers=auth_header
        )
        top_tracks = top_tracks.json()
        print("Top Tracks Response:", top_tracks)  # Debug output

        # Check for 'items' in top_tracks response
        if 'items' in top_tracks:
            # Process tracks if needed
            pass
        else:
            logger.error("Top Tracks response does not contain 'items'")

        # Get song recommendations based on the songs in top tracks and top artists
        seed_artists = ",".join([artist['id'] for artist in top_artists.get('items', [])[:2]])
        seed_tracks = ",".join([track['id'] for track in top_tracks.get('items', [])[:2]])
        recommendations_response = requests.get(
            f"https://api.spotify.com/v1/recommendations?seed_artists={seed_artists}&seed_tracks={seed_tracks}&limit=10",
            headers=auth_header
        )
        recommendations = recommendations_response.json()
        print("Recommendations Response:", recommendations)

        # Gather and organize the stats
        stats_data = {
            "Top Artists": [artist['name'] for artist in top_artists.get('items', [])],
            "Top Tracks": [track['name'] for track in top_tracks.get('items', [])],
            "Top Genres": list(set(genres)),  # Remove duplicates by converting to set
            "Song Recommendations": [rec['name'] for rec in recommendations.get('tracks', [])]
        }
        return stats_data
    except Exception as e:
        logger.error(f"Error occurred gathering stats_data: {e}")
        return None

def export_to_pdf(user_stats, file_path):
    pdf = FPDF()
    pdf.set_font("Times", size=12)

    for key, value in user_stats.items(): #Loops to grab a new page for every section (Artist, Tracks, Genres, Recommend)
        pdf.add_page()
        pdf.set_font("Times", "BIU", 16) #Font and size for titles
        pdf.cell(200,10,txt=key, ln=True, align='C') #Alignment

        pdf.set_font("Times", size=12)
        for i, item in enumerate(value, 1): #generates a number list starting with number 1
            pdf.cell(200, 10, txt=f"{i}.{item}", ln=True, align= "C")
            #txt=f"{i}.{item} insert number of item and then the name from the item list

    file_path = "./Spotify_Stats.pdf"
    pdf.output(file_path)
    print(f"PDF saved to {file_path}")

if __name__ == "__main__":
    main()
