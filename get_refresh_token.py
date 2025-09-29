#!/usr/bin/env python3
"""
Extract Spotify refresh token for use in GitHub Actions.
Run this locally after successful authentication to get your refresh token.
"""

import os
import json
from pathlib import Path


def main():
    print("=" * 60)
    print("Spotify Refresh Token Extractor")
    print("=" * 60)

    # Look for the .cache file created by spotipy
    cache_files = list(Path('.').glob('.cache*'))

    if not cache_files:
        print("\n✗ No cache file found!")
        print("\nPlease run 'python auth_setup.py' first to authenticate.")
        return

    cache_file = cache_files[0]
    print(f"\n→ Found cache file: {cache_file}")

    try:
        with open(cache_file, 'r') as f:
            token_info = json.load(f)

        refresh_token = token_info.get('refresh_token')

        if refresh_token:
            print("\n" + "=" * 60)
            print("✓ Refresh Token found!")
            print("=" * 60)
            print("\nAdd this as a GitHub Secret named SPOTIFY_REFRESH_TOKEN:")
            print(f"\n{refresh_token}")
            print("\n" + "=" * 60)
            print("\nTo add this secret to GitHub:")
            print("1. Go to your repository on GitHub")
            print("2. Settings → Secrets and variables → Actions")
            print("3. Click 'New repository secret'")
            print("4. Name: SPOTIFY_REFRESH_TOKEN")
            print("5. Value: (paste the token above)")
            print("=" * 60)
        else:
            print("\n✗ No refresh token found in cache file")

    except Exception as e:
        print(f"\n✗ Error reading cache file: {e}")


if __name__ == "__main__":
    main()