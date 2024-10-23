require('dotenv').config();

const express = require('express');
const request = require('request');
const querystring = require('querystring');
const SpotifyWebApi = require('spotify-web-api-node');

const app = express();
const client_id = process.env.CLIENT_ID;
const client_secret = process.env.CLIENT_SECRET;
const redirect_uri = 'http://localhost:8888/callback';
const scope = 'user-read-private user-read-email';

app.get('/', (req, res) => {
  res.send('<h1>Welcome to the Spotify OAuth App</h1><a href="/login">Login with Spotify</a>');
});

app.get('/login', (req, res) => {
  const state = generateRandomString(16);
  res.redirect(`https://accounts.spotify.com/authorize?` +
    `client_id=${client_id}&` +
    `response_type=code&` +
    `redirect_uri=${redirect_uri}&` +
    `scope=${scope}&` +
    `state=${state}`);
});

app.get('/callback', (req, res) => {
  const code = req.query.code || null;
  const state = req.query.state || null;

  if (state === null) {
    res.redirect('/#' +
      querystring.stringify({
        error: 'state_mismatch'
      }));
  } else {
    const authOptions = {
      url: 'https://accounts.spotify.com/api/token',
      form: {
        code: code,
        redirect_uri: redirect_uri,
        grant_type: 'authorization_code'
      },
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
        Authorization: 'Basic ' + (new Buffer.from(client_id + ':' + client_secret).toString('base64'))
      },
      json: true
    };

    request.post(authOptions, (error, response, body) => {
      if (!error && response.statusCode === 200) {
        const access_token = body.access_token;
        res.redirect('/#' +
          querystring.stringify({
            access_token: access_token
          }));
      } else {
        res.redirect('/#' +
          querystring.stringify({
            error: 'invalid_token'
          }));
      }
    });
  }
});

app.get('/generate', (req, res) => {
  const token_info = req.session.token_info;
  if (!token_info) {
    return res.redirect('/login');
  }

  const sp = new SpotifyWebApi({
    accessToken: token_info.access_token
  });

  // Use the 'sp' object to make API requests
  res.send('Hello World!');
});

app.listen(8888, () => {
  console.log('Server started on port 8888');
});