from dotenv import load_dotenv
import os
import requests
import logging
import time
import webbrowser
import urllib.parse
from fpdf import FPDF
from requests_oauthlib import OAuth1

# Load ID and Secret from .env
load_dotenv()


# Grab credentials from .env file
ID = os.getenv('CLIENT_ID')
SECRET = os.getenv('CLIENT_SECRET')
AUTHORIZATION = os.getenv('SPOTIFY_AUTHORIZATION')

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

def create_oauth(): # oauth session for authentication
    return OAuth1(
        client_key = ID,
        client_secret = SECRET
    )

def get_token():
    # Grab the Spotify OAuth2 token
    url = "https://accounts.spotify.com/api/token"
    headers = {
        "Authorization": f"Basic {os.getenv('SPOTIFY_AUTHORIZATION')}",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {
        "grant_type": "client_credentials"
    }

    response = requests.post(url, headers=headers, data=data)
    if response.status_code == 200:
        token_info = response.json()
        return token_info['access_token']
    else:
        raise Exception(f'Failed to get token: {response.status_code} {response.text}')

def get_auth_header(token):
    return {
        "Authorization": f"Bearer {token}"
    }

def main():
    try:
        token = get_token()  # Obtain the token
        logger.info("Successfully obtained token")

        auth_header = get_auth_header(token)  # Create the auth header with the token from previous line

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
    print("Extracting stats to PDF File. Save in root working directory")
    pdf = FPDF()
    pdf.add_page()

    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="Spotify Listening Stats", ln=True, align='C')

    # Add stats to PDF
    for key, value in user_stats.items():
        value_str = ", ".join(value) if isinstance(value, list) else str(value)
        pdf.cell(200, 10, txt=f"{key}: {value_str}", ln=True, align='L')

    pdf.output(file_path)
    print(f"PDF saved as {file_path}")

if __name__ == "__main__":
    main()
