# Spotify Podcast Episode Filter

## Hondelatte Raconte : une playlist par année

Le flux `Hondelatte — une playlist par année` crée des playlists telles que
**Hondelatte Raconte — L’année 1978**, avec les parties 1/5, 2/5, etc. dans l'ordre.
Il parcourt **tout le catalogue accessible sur Spotify**, pas seulement les derniers
épisodes. L'année vient du titre du récit, pas de sa date de publication.

- Les nouvelles playlists sont **privées** par défaut.
- Une seule version par numéro de partie : la publication disponible la plus récente.
- Les bandes-annonces, extraits, bonus et épisodes hors série annuelle sont exclus.
- Une série incomplète produit une playlist des parties disponibles et un avertissement.
- Les relances réutilisent les playlists créées par ce flux et les remettent dans l'ordre,
  y compris si une partie arrive tardivement. Une playlist déjà à jour ne reçoit aucune écriture.
- Seules les playlists portant le marqueur `hondelatte-years` créé par le flux sont gérées.
  Leur contenu est synchronisé : ne pas y ajouter manuellement d'autres épisodes et ne pas
  retirer le marqueur de leur description. Les autres playlists ne sont pas modifiées.
- Les épisodes retirés du catalogue Spotify ou indisponibles pour le compte ne peuvent
  pas être récupérés. Une erreur de lecture du catalogue arrête le flux avant toute écriture.

### Activation dans GitHub Actions

1. Configurer ou réutiliser les secrets Actions `SPOTIFY_CLIENT_ID`,
   `SPOTIFY_CLIENT_SECRET` et `SPOTIFY_REFRESH_TOKEN` du compte qui recevra les playlists.
   Le token doit autoriser `playlist-read-private`, `playlist-modify-private` et
   `playlist-modify-public` (les mêmes droits que le filtre existant).
2. Dans **Actions → Hondelatte — une playlist par année → Run workflow**, laisser
   **Créer et mettre à jour les playlists** décoché pour examiner une simulation.
   Le champ année est facultatif (par exemple `1978`).
3. Relancer avec la case cochée pour créer les playlists. Une fois le workflow présent
   sur la branche par défaut, la synchronisation automatique tourne chaque jour à
   **05:30 UTC** (07:30 à Paris en été, 06:30 en hiver).

Le podcast est découvert automatiquement par son nom exact sur Spotify. Si la
recherche est ambiguë, définir la variable Actions **`HONDELATTE_SHOW_ID`** avec le
lien du podcast **Hondelatte Raconte** (pas Côté B). Cette variable permet aussi d'éviter
la recherche à chaque exécution.

Le nouveau flux utilise les endpoints `/items` et `/me/playlists` documentés en 2026.
Si votre application Spotify fonctionne encore avec les anciens endpoints, définir
la variable Actions **`SPOTIFY_LEGACY_API=true`**. Les filtres existants restent indépendants.
L'accès réel dépend des droits et du mode de l'application Spotify ; le propriétaire
d'une application en mode développement doit avoir Premium.
Voir la [documentation Spotify](https://developer.spotify.com/documentation/web-api/concepts/quota-modes)
et le [guide de migration](https://developer.spotify.com/documentation/web-api/tutorials/february-2026-migration-guide).

### Exécution locale

Après installation des dépendances et configuration de `.env` :

```bash
# Autoriser Spotify si nécessaire (ou définir SPOTIFY_REFRESH_TOKEN dans .env).
python auth_setup.py
# Simulation, aucune modification sur Spotify.
python hondelatte_years.py
# Créer et synchroniser toutes les années.
python hondelatte_years.py --apply
# Une année seulement, avec le lien du podcast si nécessaire.
python hondelatte_years.py --year 1978 --show https://open.spotify.com/show/ID --apply
# Tests sans connexion ni identifiants Spotify.
python -m unittest discover -s tests -v
```

Pour une nouvelle autorisation, utiliser **`http://127.0.0.1:8888/callback`** comme
`SPOTIFY_REDIRECT_URI` dans `.env` et dans les Redirect URIs de l'application Spotify
(les anciens URI `localhost` ne sont plus acceptés pour une nouvelle configuration).
L'option `--public` rend publiques les nouvelles playlists ; `--legacy-api` sélectionne
les anciens endpoints en exécution locale.

Automatically filter and add podcast episodes matching specific name patterns to a Spotify playlist. Perfect for high-volume podcast shows where you only want episodes matching certain keywords or patterns.

## Use Case

If you follow a radio station or podcast that publishes many episodes daily (e.g., 100+ episodes/day) with various shows, chapters, and segments, this tool helps you:
- Monitor specific podcast shows
- Filter episodes by name patterns (regex)
- Automatically add matching episodes to a dedicated playlist
- Avoid duplicates

## Prerequisites

1. **Spotify Account** (Free or Premium)
2. **Spotify Developer App** credentials:
   - Go to [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
   - Create a new app
   - Note your `Client ID` and `Client Secret`
   - Add `http://localhost:8888/callback` to the app's Redirect URIs

## Installation

1. **Clone or download this repository**

2. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**:
   - Copy `.env.example` to `.env`:
     ```bash
     cp .env.example .env
     ```
   - Edit `.env` and add your Spotify credentials:
     ```
     SPOTIFY_CLIENT_ID=your_actual_client_id
     SPOTIFY_CLIENT_SECRET=your_actual_client_secret
     SPOTIFY_REDIRECT_URI=http://localhost:8888/callback
     ```

## Configuration

Edit `config.yaml` to define multiple filter configurations. Each filter can monitor a different show with its own patterns and target playlist.

### Configuration Structure

```yaml
filters:
  # Filter 1: Example configuration
  - name: "Interview Episodes"
    show_id: "6z4NLXyHPga1UmSJsPK7G1"  # Show ID or full URL
    name_patterns:
      - ".*Interview.*"
      - ".*Entretien.*"
    exclude_patterns:  # Optional: exclude even if it matches name_patterns
      - ".*replay.*"
      - ".*rediffusion.*"
    target_playlist_id: "your_playlist_id_1"
    max_episodes: 50

  # Filter 2: Another configuration
  - name: "Special Reports"
    show_id: "https://open.spotify.com/show/7rSVyEKZ7nNJaOCCnGPFHq"
    name_patterns:
      - ".*Special.*"
      - ".*Report.*"
    exclude_patterns:
      - ".*best of.*"
    target_playlist_id: "your_playlist_id_2"
    max_episodes: 100

# Global settings
global:
  continue_on_error: true  # Keep processing other filters if one fails
```

### Configuration Fields

**`name`** (string): Descriptive name for this filter configuration

**`show_id`** (string): Spotify show ID or full URL
- Get it by: Spotify → Podcast → Share → Copy link to show

**`name_patterns`** (list): Regex patterns to match episode names
- Episodes matching ANY pattern will be considered
- Patterns are case-insensitive
- Pattern tips:
  - `.*` = match any characters
  - `^` = start of string
  - `$` = end of string
  - `(A|B)` = match A or B
  - `[0-9]+` = one or more digits

**`exclude_patterns`** (list, optional): Regex patterns to exclude episodes
- Episodes matching ANY exclude pattern will be skipped, even if they match `name_patterns`
- Useful for filtering out replays, best-of compilations, etc.
- Same pattern syntax as `name_patterns`

**`target_playlist_id`** (string): Playlist ID where matching episodes will be added
- Get it by: Spotify → Playlist → Share → Copy link to playlist
- Extract ID from URL: `https://open.spotify.com/playlist/YOUR_PLAYLIST_ID`

**`max_episodes`** (integer): Number of recent episodes to check (no limit, uses pagination)

## Usage

### First Time Setup

Run the authentication helper to authorize the app:
```bash
python auth_setup.py
```

This will:
1. Open your browser for Spotify authorization
2. Cache the authentication token
3. Verify your credentials work

### Running the Filter

Execute the main script:
```bash
python podcast_filter.py
```

The script will:
1. Connect to Spotify
2. Check existing episodes in your playlist (to avoid duplicates)
3. Fetch recent episodes from configured shows
4. Filter by name patterns
5. Add matching episodes to your playlist
6. Display a summary of results

### Example Output

```
✓ Authenticated with Spotify

→ Found 2 filter configuration(s)

============================================================
Processing filter: Interview Episodes
============================================================
→ Show: Example Radio Station
→ Playlist has 15 episodes
→ Checking 50 most recent episodes...
  ✓ Match: Morning Show - Interview with Jane Doe
  ✓ Match: Special Report: Breaking News

→ Added 2 episodes to playlist

============================================================
Processing filter: Special Reports
============================================================
→ Show: News Network Daily
→ Playlist has 8 episodes
→ Checking 100 most recent episodes...
  ✓ Match: Special Edition: Election Night

→ Added 1 episodes to playlist

============================================================
GLOBAL SUMMARY
============================================================
  Filters processed: 2/2
  Total matching episodes found: 3
  Total episodes added: 3
============================================================
```

## Automation

### Option 1: GitHub Actions (Recommended)

Run the filter automatically every day at 6:00 AM Paris time using GitHub Actions.

#### Setup Steps:

1. **Push your repository to GitHub**

2. **Get your Spotify refresh token**:
   ```bash
   python get_refresh_token.py
   ```
   This will display your refresh token.

3. **Add GitHub Secrets**:
   - Go to your repository on GitHub
   - Settings → Secrets and variables → Actions
   - Add these secrets:
     - `SPOTIFY_CLIENT_ID`: Your Spotify Client ID
     - `SPOTIFY_CLIENT_SECRET`: Your Spotify Client Secret
     - `SPOTIFY_REDIRECT_URI`: `http://localhost:8888/callback`
     - `SPOTIFY_REFRESH_TOKEN`: The token from step 2

4. **Enable GitHub Actions**:
   - Go to the "Actions" tab in your repository
   - Enable workflows if prompted

The workflow will run automatically every day at 6:00 AM Paris time. You can also trigger it manually from the Actions tab.

### Option 2: Run on Schedule (Cron - macOS/Linux)

Edit your crontab:
```bash
crontab -e
```

Add a line to run every hour:
```
0 * * * * cd /path/to/Spotify_Playlist && /usr/bin/python3 podcast_filter.py >> /tmp/podcast_filter.log 2>&1
```

### Option 3: Run on Schedule (Task Scheduler - Windows)

1. Open Task Scheduler
2. Create Basic Task
3. Set trigger (e.g., daily at 9 AM)
4. Action: Start a program
   - Program: `python`
   - Arguments: `podcast_filter.py`
   - Start in: `C:\path\to\Spotify_Playlist`

## Troubleshooting

### Authentication Issues

- Ensure `http://localhost:8888/callback` is added to your Spotify app's Redirect URIs
- Delete `.cache` files and re-run `auth_setup.py`
- Check that your Client ID and Secret are correct in `.env`

### No Episodes Found

- Verify show IDs are correct (test by opening in Spotify)
- Check that your regex patterns are valid
- Increase `max_episodes` in your filter configuration if needed

### Permission Errors

- Ensure you have write access to the target playlist
- The playlist must be owned by your Spotify account (or you must be a collaborator)

## Project Structure

```
.
├── .github/
│   └── workflows/
│       └── daily-filter.yml   # GitHub Actions workflow
├── .env.example               # Template for credentials
├── .gitignore                 # Git ignore file
├── README.md                  # This file
├── requirements.txt           # Python dependencies
├── config.yaml                # Multi-filter configuration
├── auth_setup.py              # First-time authentication helper
├── get_refresh_token.py       # Extract token for GitHub Actions
└── podcast_filter.py          # Main filtering script
```

## License

MIT License - Use freely for personal or commercial projects.

## Contributing

Feel free to submit issues or pull requests for improvements!
