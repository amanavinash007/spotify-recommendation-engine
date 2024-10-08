from flask import Flask, redirect, request, session, url_for, render_template
from flask_session import Session
import requests
import os
import base64
from dotenv import load_dotenv  # Add this import

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
app.config['SESSION_TYPE'] = 'filesystem'  
app.secret_key = os.urandom(24)
app.config['SESSION_COOKIE_NAME'] = 'session'
Session(app)

# Spotify app credentials (now fetched from environment variables)
CLIENT_ID = os.getenv('CLIENT_ID')
CLIENT_SECRET = os.getenv('CLIENT_SECRET')
REDIRECT_URI = os.getenv('REDIRECT_URI')

AUTH_URL = 'https://accounts.spotify.com/authorize'
TOKEN_URL = 'https://accounts.spotify.com/api/token'

@app.route('/login')
def login():
    auth_url = f"{AUTH_URL}?client_id={CLIENT_ID}&response_type=code&redirect_uri={REDIRECT_URI}&scope=user-top-read user-library-read"
    return redirect(auth_url)

# Step 2: Handle callback and exchange code for tokens
@app.route('/callback')
def callback():
    code = request.args.get('code')  # Get authorization code from the callback
    auth_header = base64.b64encode(f"{CLIENT_ID}:{CLIENT_SECRET}".encode()).decode('utf-8')  # Base64 encode client credentials
    data = {
        'grant_type': 'authorization_code',  # We are using the 'authorization_code' grant type
        'code': code,
        'redirect_uri': REDIRECT_URI
    }
    headers = {
        'Authorization': f'Basic {auth_header}'
    }
    response = requests.post(TOKEN_URL, data=data, headers=headers)  # Exchange the code for tokens
    response_data = response.json()  # Get the response as a JSON object
    if response.status_code == 200:
        session['token'] = response_data['access_token']  # Store access token in the session
        return redirect(url_for('user_home'))  # Redirect to home page (user data)
    else:
        return "Error: Unable to authenticate", 400

# Step 3: Use the token to get the user's top tracks or artists
@app.route('/home')
def user_home():
    token = session.get('token')  # Get token from session
    if token:
        headers = {
            'Authorization': f'Bearer {token}'  # Pass the token as a Bearer token in the Authorization header
        }
        top_tracks = requests.get('https://api.spotify.com/v1/me/top/artists', headers=headers).json()  # Fetch top artists
        return render_template('home.html', top_tracks=top_tracks)
    else:
        return redirect(url_for('login'))  # Redirect to login if no token exists

@app.route('/recommendations')
def recommendations():
    token = session.get('token')  # Get token from session
    if token:
        headers = {
            'Authorization': f'Bearer {token}'  # Pass token in Authorization header
        }
        
        # Get the user's top artists
        top_artists = requests.get('https://api.spotify.com/v1/me/top/artists', headers=headers).json()
        seed_artists = [artist['id'] for artist in top_artists['items'][:5]]  # Get top 5 artists
        
        # Generate recommendations
        params = {
            'seed_artists': ','.join(seed_artists),
            'limit': 10,
            'min_energy': 0.5,  # Adjust according to your needs
            'min_valence': 0.5
        }
        recommendations = requests.get('https://api.spotify.com/v1/recommendations', headers=headers, params=params).json()
        
        return render_template('recommendations.html', recommendations=recommendations['tracks'])
    else:
        return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
