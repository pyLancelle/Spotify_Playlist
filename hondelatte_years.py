#!/usr/bin/env python3
"""Synchronise les séries « L'année YYYY » vers une playlist par année."""

import argparse
from collections import defaultdict
import json
import os
import re
import sys
import time
import unicodedata
from urllib.error import HTTPError
from urllib.parse import urlencode, urlparse
from urllib.request import Request, urlopen

SCOPE = 'playlist-modify-public playlist-modify-private playlist-read-private'


def normalize(text):
    return ''.join(c for c in unicodedata.normalize('NFKD', text.casefold())
                   if not unicodedata.combining(c))


def parse_title(title):
    """Année du récit, jamais date de publication ou année d'un fait divers."""
    text = normalize(title)
    if re.search(r'\b(bande[ -]annonce|extrait|teaser|bonus)\b', text):
        return None
    year = re.search(r'\bannee\s*[:–—-]?\s*((?:19|20)\d{2})\b', text)
    part = re.search(r'[\[(]\s*(\d+)\s*/\s*(\d+)\s*[\])]', text)
    if not year or not part:
        return None
    number, total = map(int, part.groups())
    if not 1 <= number <= total <= 100:
        return None
    return int(year[1]), number, total


def group_episodes(episodes):
    """Une version par partie ; préfère la dernière publication disponible."""
    groups = defaultdict(dict)
    for episode in episodes:
        if not episode or not episode.get('uri') or episode.get('is_playable') is False:
            continue
        parsed = parse_title(episode.get('name', ''))
        if parsed is None:
            continue
        year, part, total = parsed
        candidate = dict(episode, part=part, total=total)
        previous = groups[year].get(part)
        rank = lambda e: (e.get('release_date', ''), e['uri'])
        if previous is None or rank(candidate) > rank(previous):
            groups[year][part] = candidate
    return {year: [parts[p] for p in sorted(parts)]
            for year, parts in sorted(groups.items())}


class SpotifyAPI:
    """OAuth Spotipy, transport compatible avec les endpoints Spotify de 2026."""

    def __init__(self, auth, legacy=False):
        self.auth = auth
        self.items_resource = 'tracks' if legacy else 'items'
        self.legacy = legacy

    def request(self, method, path, data=None, **params):
        url = path if path.startswith('https://') else 'https://api.spotify.com/v1/' + path
        if urlparse(url).netloc != 'api.spotify.com':
            raise ValueError('URL de pagination Spotify inattendue')
        if params:
            url += '?' + urlencode(params)
        for attempt in range(4):
            token = self.auth.get_access_token(as_dict=False)
            request = Request(url, method=method, headers={
                'Authorization': 'Bearer ' + token, 'Content-Type': 'application/json'},
                data=None if data is None else json.dumps(data).encode())
            try:
                with urlopen(request, timeout=30) as response:
                    body = response.read()
                    return json.loads(body) if body else {}
            except HTTPError as error:
                if error.code == 429 and attempt < 3:
                    delay = int(error.headers.get('Retry-After', '5'))
                    if delay <= 60:
                        time.sleep(max(0, delay))
                        continue
                # Ne pas afficher les réponses d'authentification ni réessayer
                # une écriture au résultat incertain (création/ajout).
                raise RuntimeError(f'Spotify HTTP {error.code} ({method} {urlparse(url).path})') from None

    def pages(self, path, **params):
        page = self.request('GET', path, **params)
        while True:
            yield from page['items']
            if not page.get('next'):
                return
            page = self.request('GET', page['next'])

    def resolve_show(self, show_input=None):
        if show_input:
            show_id = show_input.split('show/')[-1].split('?')[0].removeprefix('spotify:show:')
            if not re.fullmatch(r'[A-Za-z0-9]{22}', show_id):
                raise ValueError('Identifiant ou lien Spotify du podcast invalide')
            show = self.request('GET', f'shows/{show_id}', market='FR')
        else:
            result = self.request('GET', 'search', q='Hondelatte Raconte', type='show', limit=10, market='FR')
            shows = [s for s in result['shows']['items']
                     if normalize(s['name']) == 'hondelatte raconte']
            if len(shows) != 1:
                raise ValueError('Podcast introuvable ou ambigu : préciser --show avec son lien Spotify')
            show = shows[0]
        if normalize(show['name']) != 'hondelatte raconte':
            raise ValueError('Le podcast sélectionné ne se nomme pas Hondelatte Raconte')
        print(f"Podcast : {show['name']} — https://open.spotify.com/show/{show['id']}")
        return show['id']

    def playlist_items(self, playlist_id):
        return list(self.pages(f'playlists/{playlist_id}/{self.items_resource}',
                               limit=50, additional_types='episode', market='FR'))

    def create_playlist(self, user_id, name, marker, public):
        path = f'users/{user_id}/playlists' if self.legacy else 'me/playlists'
        return self.request('POST', path, {'name': name, 'public': public, 'description': marker})

    def replace_items(self, playlist_id, uris):
        path = f'playlists/{playlist_id}/{self.items_resource}'
        self.request('PUT', path, {'uris': uris[:100]})
        for start in range(100, len(uris), 100):
            self.request('POST', path, {'uris': uris[start:start + 100]})


def synchronize(api, show_id, groups, dry_run=True, public=False):
    user_id = api.request('GET', 'me')['id']
    playlists = list(api.pages('me/playlists', limit=50))
    changed = 0
    for year, episodes in groups.items():
        name = f'Hondelatte Raconte — L’année {year}'
        marker = f'Géré par Spotify_Playlist / hondelatte-years:{show_id}:{year}.'
        matches = [p for p in playlists if p and p.get('owner', {}).get('id') == user_id
                   and marker in (p.get('description') or '')]
        if len(matches) > 1:
            raise ValueError(f'{year} : plusieurs playlists gérées portent le même identifiant')
        totals = {e['total'] for e in episodes}
        missing = sorted(set(range(1, max(totals) + 1)) - {e['part'] for e in episodes})
        print(f'{name} : {len(episodes)} parties')
        if missing or len(totals) > 1:
            print(f'  Attention : parties manquantes {missing}, totaux annoncés {sorted(totals)}')
        for e in episodes:
            print(f"  {e['part']}/{e['total']} : {e['name']}")
        desired = [e['uri'] for e in episodes]
        playlist = matches[0] if matches else None
        if playlist:
            current = []
            for entry in api.playlist_items(playlist['id']):
                item = entry.get('item') or entry.get('track') or {}
                current.append(item.get('uri'))
            if current == desired:
                print('  Déjà à jour')
                continue
        changed += 1
        if dry_run:
            print('  Simulation : mise à jour' if playlist else '  Simulation : création')
            continue
        if playlist is None:
            playlist = api.create_playlist(user_id, name, marker, public)
            playlists.append(playlist)
        api.replace_items(playlist['id'], desired)
        print(f"  Playlist : https://open.spotify.com/playlist/{playlist['id']}")
    return changed


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--show', default=os.getenv('HONDELATTE_SHOW_ID'), help='Lien ou ID Spotify ; sinon découverte automatique')
    parser.add_argument('--year', type=int, help='Limiter à une année racontée')
    parser.add_argument('--apply', action='store_true', help='Créer/mettre à jour les playlists (sinon simulation)')
    parser.add_argument('--public', action='store_true', help='Créer les nouvelles playlists publiques (privées par défaut)')
    parser.add_argument('--legacy-api', action='store_true', help='Anciens endpoints pour les applications Spotify non migrées')
    args = parser.parse_args()
    from dotenv import load_dotenv
    from spotipy.cache_handler import MemoryCacheHandler
    from spotipy.oauth2 import SpotifyOAuth
    load_dotenv()
    client_id, secret = os.getenv('SPOTIFY_CLIENT_ID'), os.getenv('SPOTIFY_CLIENT_SECRET')
    if not client_id or not secret:
        raise ValueError('Configurer SPOTIFY_CLIENT_ID et SPOTIFY_CLIENT_SECRET')
    refresh = os.getenv('SPOTIFY_REFRESH_TOKEN')
    options = {}
    if refresh:
        options['cache_handler'] = MemoryCacheHandler(token_info={
            'access_token': '', 'refresh_token': refresh, 'expires_at': 0,
            'token_type': 'Bearer', 'scope': SCOPE})
    elif os.getenv('CI'):
        raise ValueError('Configurer le secret SPOTIFY_REFRESH_TOKEN avant le lancement en CI')
    auth = SpotifyOAuth(client_id=client_id, client_secret=secret,
                        redirect_uri=os.getenv('SPOTIFY_REDIRECT_URI') or 'http://127.0.0.1:8888/callback',
                        scope=SCOPE, open_browser=not bool(refresh), **options)
    api = SpotifyAPI(auth, legacy=args.legacy_api)
    show_id = api.resolve_show(args.show or os.getenv('HONDELATTE_SHOW_ID'))
    # Lecture intégrale réussie avant toute écriture : une erreur sur une page
    # ne doit jamais produire une synchronisation partielle du catalogue.
    episodes = list(api.pages(f'shows/{show_id}/episodes', limit=50, market='FR'))
    groups = group_episodes(episodes)
    if args.year is not None:
        groups = {y: e for y, e in groups.items() if y == args.year}
    if not groups:
        raise ValueError('Aucune série annuelle détectée ; aucune playlist modifiée')
    changes = synchronize(api, show_id, groups, dry_run=not args.apply, public=args.public)
    print(f'{len(groups)} années détectées, {changes} playlists à synchroniser' +
          (' (simulation)' if not args.apply else ''))


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        print(f'Erreur : {error}', file=sys.stderr)
        sys.exit(1)
