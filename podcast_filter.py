#!/usr/bin/env python3
"""
Spotify Podcast Episode Filter
Automatically adds podcast episodes matching specified patterns to a playlist.
"""

import os
import re
import sys
import yaml
from dotenv import load_dotenv
import spotipy
from spotipy.oauth2 import SpotifyOAuth


def load_config(config_path='config.yaml'):
    """Load configuration from YAML file."""
    try:
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        print(f"Error: Config file '{config_path}' not found.")
        sys.exit(1)
    except yaml.YAMLError as e:
        print(f"Error parsing config file: {e}")
        sys.exit(1)


def extract_show_id(show_input):
    """Extract Spotify show ID from URL or ID string."""
    if 'open.spotify.com/show/' in show_input:
        # Extract ID from URL
        return show_input.split('show/')[-1].split('?')[0]
    return show_input


def extract_playlist_id(playlist_input):
    """Extract Spotify playlist ID from URL or ID string."""
    if 'open.spotify.com/playlist/' in playlist_input:
        return playlist_input.split('playlist/')[-1].split('?')[0]
    return playlist_input


def get_playlist_episode_uris(sp, playlist_id):
    """Get all episode URIs currently in the playlist."""
    episode_uris = set()
    results = sp.playlist_items(playlist_id)

    while results:
        for item in results['items']:
            if item['track'] and item['track']['type'] == 'episode':
                episode_uris.add(item['track']['uri'])

        # Handle pagination
        if results['next']:
            results = sp.next(results)
        else:
            break

    return episode_uris


def get_show_episodes(sp, show_id, limit=50):
    """Fetch recent episodes from a show using pagination."""
    try:
        episodes = []
        offset = 0
        batch_size = 50  # Maximum allowed by Spotify API per request

        while len(episodes) < limit:
            # Calculate how many episodes to fetch in this batch
            remaining = limit - len(episodes)
            current_limit = min(batch_size, remaining)

            # Fetch a batch of episodes
            results = sp.show_episodes(show_id, limit=current_limit, offset=offset)

            if not results or not results.get('items'):
                break

            episodes.extend(results['items'])

            # Check if there are more episodes available
            if not results.get('next') or len(results['items']) < current_limit:
                break

            offset += len(results['items'])

        return episodes[:limit]
    except Exception as e:
        print(f"Error fetching episodes for show {show_id}: {e}")
        return []


def matches_patterns(episode_name, patterns):
    """Check if episode name matches any of the provided regex patterns."""
    for pattern in patterns:
        try:
            if re.search(pattern, episode_name, re.IGNORECASE):
                return True
        except re.error as e:
            print(f"Warning: Invalid regex pattern '{pattern}': {e}")
    return False


def process_filter(sp, filter_config):
    """Process a single filter configuration."""
    filter_name = filter_config.get('name', 'Unnamed filter')
    show_id = extract_show_id(filter_config.get('show_id', ''))
    patterns = filter_config.get('name_patterns', [])
    playlist_id = extract_playlist_id(filter_config.get('target_playlist_id', ''))
    max_episodes = filter_config.get('max_episodes', 50)

    # Validate filter config
    if not show_id or not patterns or not playlist_id:
        print(f"\n✗ Skipping '{filter_name}': Missing show_id, name_patterns, or target_playlist_id")
        return 0, 0

    print(f"\n{'='*60}")
    print(f"Processing filter: {filter_name}")
    print(f"{'='*60}")

    # Get show information
    try:
        show_info = sp.show(show_id)
        show_name = show_info['name']
        print(f"→ Show: {show_name}")
    except Exception as e:
        print(f"✗ Error accessing show {show_id}: {e}")
        return 0, 0

    # Get existing episodes in playlist
    try:
        existing_episodes = get_playlist_episode_uris(sp, playlist_id)
        print(f"→ Playlist has {len(existing_episodes)} episodes")
    except Exception as e:
        print(f"✗ Error accessing playlist: {e}")
        return 0, 0

    # Fetch episodes from show
    print(f"→ Checking {max_episodes} most recent episodes...")
    episodes = get_show_episodes(sp, show_id, max_episodes)

    if not episodes:
        print("  No episodes found")
        return 0, 0

    # Filter episodes by patterns
    matching_episodes = []
    found_count = 0

    for episode in episodes:
        episode_name = episode['name']
        episode_uri = episode['uri']

        # Skip if already in playlist
        if episode_uri in existing_episodes:
            continue

        # Check if matches any pattern
        if matches_patterns(episode_name, patterns):
            matching_episodes.append(episode_uri)
            found_count += 1
            print(f"  ✓ Match: {episode_name}")

    # Add matching episodes to playlist
    added_count = 0
    if matching_episodes:
        try:
            sp.playlist_add_items(playlist_id, matching_episodes)
            added_count = len(matching_episodes)
            print(f"\n→ Added {added_count} episodes to playlist")
        except Exception as e:
            print(f"\n✗ Error adding episodes to playlist: {e}")
    else:
        print("\n→ No new matching episodes found")

    return found_count, added_count


def main():
    # Load environment variables
    load_dotenv()

    # Check for required credentials
    client_id = os.getenv('SPOTIFY_CLIENT_ID')
    client_secret = os.getenv('SPOTIFY_CLIENT_SECRET')
    redirect_uri = os.getenv('SPOTIFY_REDIRECT_URI', 'http://localhost:8888/callback')

    if not client_id or not client_secret:
        print("Error: SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET must be set in .env file")
        sys.exit(1)

    # Load configuration
    config = load_config()

    # Get filters from config
    filters = config.get('filters', [])
    if not filters:
        print("Error: config.yaml must contain at least one filter configuration")
        sys.exit(1)

    # Get global settings
    global_config = config.get('global', {})
    continue_on_error = global_config.get('continue_on_error', True)

    # Authenticate with Spotify
    scope = "playlist-modify-public playlist-modify-private playlist-read-private"
    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri=redirect_uri,
        scope=scope
    ))

    print("✓ Authenticated with Spotify")
    print(f"\n→ Found {len(filters)} filter configuration(s)")

    # Process each filter
    total_found = 0
    total_added = 0
    successful_filters = 0
    failed_filters = 0

    for i, filter_config in enumerate(filters, 1):
        try:
            found, added = process_filter(sp, filter_config)
            total_found += found
            total_added += added
            successful_filters += 1
        except Exception as e:
            filter_name = filter_config.get('name', f'Filter {i}')
            failed_filters += 1
            print(f"\n✗ Error processing filter '{filter_name}': {e}")
            if not continue_on_error:
                print("\nStopping execution (continue_on_error is false)")
                break

    # Global summary
    print(f"\n{'='*60}")
    print(f"GLOBAL SUMMARY")
    print(f"{'='*60}")
    print(f"  Filters processed: {successful_filters}/{len(filters)}")
    if failed_filters > 0:
        print(f"  Failed filters: {failed_filters}")
    print(f"  Total matching episodes found: {total_found}")
    print(f"  Total episodes added: {total_added}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()