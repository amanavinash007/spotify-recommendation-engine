from flask import Flask, redirect, request, session, url_for
from flask_session import Session
import requests
import os
import base64

app = Flask(__name__)
app.secret_key = os.urandom(24)
app.config['SESSION_COOKIE_NAME'] = 'session'
Session(app)

# Spotify app credentials
CLIENT_ID = 'a157ca37f296409b8ec7c14667a5831b'
CLIENT_SECRET = 'e5ea6488ab5e4e63b83aca706a9c733c'
REDIRECT_URI = 'http://localhost:5000/callback'

AUTH_URL = 'https://accounts.spotify.com/authorize'
TOKEN_URL = 'https://accounts.spotify.com/api/token'

# Step 1: Redirect to Spotify login
@app.route('/login')
def login():
    auth_url = f"{AUTH_URL}?client_id={CLIENT_ID}&response_type=code&redirect_uri={REDIRECT_URI}&scope=user-top-read user-library-read"
    return redirect(auth_url)

# Step 2: Handle callback and exchange code for tokens
@app.route('/callback')
def callback():
    code = request.args.get('code')
    auth_header = base64.b64encode(f"{CLIENT_ID}:{CLIENT_SECRET}".encode()).decode('utf-8')
    data = {
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': REDIRECT_URI
    }
    headers = {
        'Authorization': f'Basic {auth_header}'
    }
    response = requests.post(TOKEN_URL, data=data, headers=headers)
    response_data = response.json()
    session['token'] = response_data['access_token']
    return redirect(url_for('home'))

# Step 3: Use the token to get the user's top tracks or artists
@app.route('/home')
def home():
    token = session.get('token')
    if token:
        headers = {
            'Authorization': f'Bearer {token}'
        }
        top_tracks = requests.get('https://api.spotify.com/v1/me/top/artists', headers=headers).json()
        return render_template('home.html', top_tracks=top_tracks)
    else:
        return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)


@app.route('/recommendations')
def recommendations():
    token = session.get('token')
    if token:
        headers = {
            'Authorization': f'Bearer {token}'
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
