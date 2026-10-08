import unittest
from unittest.mock import Mock

from hondelatte_years import SpotifyAPI, group_episodes, parse_title, synchronize


def episode(part, year=1978, total=5, date='2026-08-01', uri=None):
    return {'name': f"Hondelatte raconte : L'année {year} [{part}/{total}]",
            'uri': uri or f'spotify:episode:{year}-{part}', 'release_date': date}


class FakeAPI:
    def __init__(self):
        self.playlists = []
        self.contents = {}
        self.writes = []

    def request(self, method, path):
        return {'id': 'me'}

    def pages(self, path, **kwargs):
        return iter(self.playlists)

    def playlist_items(self, playlist_id):
        return [{'item': {'uri': uri}} for uri in self.contents[playlist_id]]

    def create_playlist(self, user_id, name, marker, public):
        playlist = {'id': str(len(self.playlists)), 'name': name,
                    'description': marker, 'owner': {'id': user_id}}
        self.playlists.append(playlist)
        self.contents[playlist['id']] = []
        self.writes.append(('create', public))
        return playlist

    def replace_items(self, playlist_id, uris):
        self.contents[playlist_id] = uris
        self.writes.append(('replace', list(uris)))


class AnnualSeriesTests(unittest.TestCase):
    def test_real_title_formats_and_reject_unrelated_years(self):
        for title in ["Hondelatte raconte : L'année 1978 [3/5]",
                      'HONDELATTE RACONTE – L’ANNÉE 1978 (3/5)',
                      'REDIFFUSION - L’année 1978 [ 3 / 5 ]']:
            self.assertEqual(parse_title(title), (1978, 3, 5))
        for title in ['Un meurtre en 1978 (1/2)', 'L’année 1978',
                      'Bande-annonce : L’année 1978 [1/5]',
                      'Extrait : L’année 1978 [1/5]', 'L’année 1978 [0/5]',
                      'L’année 1978 [6/5]']:
            self.assertIsNone(parse_title(title))

    def test_group_sort_deduplicate_and_unavailable(self):
        old = episode(1, date='2022-01-01', uri='spotify:episode:old')
        latest = episode(1, uri='spotify:episode:new')
        unavailable = dict(episode(2), is_playable=False)
        grouped = group_episodes([episode(3), old, None, latest, latest,
                                  episode(1, 1979), unavailable])
        self.assertEqual(list(grouped), [1978, 1979])
        self.assertEqual([e['part'] for e in grouped[1978]], [1, 3])
        self.assertEqual(grouped[1978][0]['uri'], latest['uri'])

    def test_dry_run_no_writes(self):
        api = FakeAPI()
        self.assertEqual(synchronize(api, 'show', group_episodes([episode(1)])), 1)
        self.assertEqual(api.writes, [])

    def test_repeated_runs_late_part_and_unrelated_playlist(self):
        api = FakeAPI()
        api.playlists.append({'id': 'manual', 'name': 'Hondelatte Raconte — L’année 1978',
                              'owner': {'id': 'me'}, 'description': ''})
        api.contents['manual'] = ['spotify:episode:personal']
        groups = group_episodes([episode(3), episode(1)])
        self.assertEqual(synchronize(api, 'show', groups, dry_run=False), 1)
        count = len(api.writes)
        self.assertEqual(synchronize(api, 'show', groups, dry_run=False), 0)
        self.assertEqual(len(api.writes), count)
        groups = group_episodes([episode(3), episode(2), episode(1)])
        synchronize(api, 'show', groups, dry_run=False)
        self.assertEqual(api.contents['1'], [episode(p)['uri'] for p in [1, 2, 3]])
        self.assertEqual(api.contents['manual'], ['spotify:episode:personal'])
        self.assertEqual(len(api.playlists), 2)

    def test_ambiguous_managed_playlists_stop(self):
        api = FakeAPI()
        for _ in range(2):
            api.create_playlist('me', 'name', 'Géré par Spotify_Playlist / hondelatte-years:show:1978.', False)
        with self.assertRaises(ValueError):
            synchronize(api, 'show', group_episodes([episode(1)]), dry_run=False)

    def test_pagination_and_chunk_limit(self):
        api = SpotifyAPI(None)
        api.request = Mock(side_effect=[{'items': [1], 'next': 'https://api.spotify.com/v1/page2'},
                                       {'items': [2, None], 'next': None}])
        self.assertEqual(list(api.pages('page1', limit=50)), [1, 2, None])
        api.request = Mock()
        uris = [f'spotify:episode:{i}' for i in range(205)]
        api.replace_items('playlist', uris)
        calls = api.request.call_args_list
        self.assertEqual([c.args[0] for c in calls], ['PUT', 'POST', 'POST'])
        self.assertTrue(all(c.args[1] == 'playlists/playlist/items' for c in calls))
        self.assertEqual([len(c.args[2]['uris']) for c in calls], [100, 100, 5])

    def test_catalogue_failure_does_not_write(self):
        api = SpotifyAPI(None)
        api.request = Mock(side_effect=[{'items': [episode(1)], 'next': 'https://api.spotify.com/v1/page2'},
                                       RuntimeError('HTTP 503')])
        with self.assertRaises(RuntimeError):
            list(api.pages('shows/show/episodes'))

    def test_legacy_playlist_response(self):
        api = FakeAPI()
        groups = group_episodes([episode(1)])
        synchronize(api, 'show', groups, dry_run=False)
        api.playlist_items = lambda _: [{'track': {'uri': episode(1)['uri']}}]
        self.assertEqual(synchronize(api, 'show', groups, dry_run=False), 0)


if __name__ == '__main__':
    unittest.main()
