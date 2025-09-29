#!/usr/bin/env python3
"""
Spotify Authentication Setup Helper
Run this script once to authorize the application and cache the token.
"""

import os
import sys
from dotenv import load_dotenv
import spotipy
from spotipy.oauth2 import SpotifyOAuth


def main():
    print("=" * 60)
    print("Spotify Podcast Filter - Authentication Setup")
    print("=" * 60)

    # Load environment variables
    load_dotenv()

    client_id = os.getenv('SPOTIFY_CLIENT_ID')
    client_secret = os.getenv('SPOTIFY_CLIENT_SECRET')
    redirect_uri = os.getenv('SPOTIFY_REDIRECT_URI', 'http://localhost:8888/callback')

    if not client_id or not client_secret:
        print("\n✗ Error: Missing credentials!")
        print("\nPlease create a .env file with:")
        print("  SPOTIFY_CLIENT_ID=your_client_id")
        print("  SPOTIFY_CLIENT_SECRET=your_client_secret")
        print("  SPOTIFY_REDIRECT_URI=http://localhost:8888/callback")
        print("\nGet credentials from: https://developer.spotify.com/dashboard")
        sys.exit(1)

    print("\n✓ Credentials loaded from .env")
    print(f"  Client ID: {client_id[:10]}...")
    print(f"  Redirect URI: {redirect_uri}")

    # Set up OAuth with required scopes
    scope = "playlist-modify-public playlist-modify-private playlist-read-private"

    print("\n→ Initiating Spotify authentication...")
    print("\nA browser window will open for you to authorize the application.")
    print("After authorization, you'll be redirected to a localhost URL.")
    print("Copy the entire URL from your browser and paste it back here.")

    try:
        sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=redirect_uri,
            scope=scope,
            open_browser=True
        ))

        # Test the authentication by getting user info
        user = sp.current_user()
        print("\n" + "=" * 60)
        print("✓ Authentication successful!")
        print("=" * 60)
        print(f"\nLogged in as: {user.get('display_name', 'Unknown')} ({user['id']})")
        if 'product' in user:
            print(f"Account type: {user['product']}")
        print("\nToken cached successfully. You can now run podcast_filter.py")
        print("=" * 60)

    except Exception as e:
        print(f"\n✗ Authentication failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()