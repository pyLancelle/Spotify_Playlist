# Spotify Podcast Episode Filter

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

Edit `config.yaml` to customize your filtering:

### 1. Shows to Query

Add Spotify show IDs or URLs to monitor:
```yaml
shows_to_query:
  - "6z4NLXyHPga1UmSJsPK7G1"  # Can use show ID
  - "https://open.spotify.com/show/7rSVyEKZ7nNJaOCCnGPFHq"  # Or full URL
```

**How to get a show ID:**
- Open Spotify and navigate to the podcast show
- Click "Share" → "Copy link to show"
- Paste the URL in config.yaml (or extract the ID after `/show/`)

### 2. Name Patterns

Define regex patterns to match episode names:
```yaml
name_patterns:
  - ".*Interview.*"           # Matches any episode with "Interview"
  - "^Morning Show.*"          # Matches episodes starting with "Morning Show"
  - ".*(Special|Guest).*"      # Matches episodes containing "Special" OR "Guest"
  - "Episode [0-9]+"           # Matches "Episode" followed by numbers
```

**Pattern Tips:**
- `.*` = match any characters
- `^` = start of string
- `$` = end of string
- `(A|B)` = match A or B
- `[0-9]+` = one or more digits
- Patterns are case-insensitive

### 3. Target Playlist

Specify where matching episodes should be added:
```yaml
target_playlist_id: "your_playlist_id_here"
```

**How to get a playlist ID:**
- Open Spotify and navigate to your playlist
- Click "Share" → "Copy link to playlist"
- Extract the ID from the URL: `https://open.spotify.com/playlist/YOUR_PLAYLIST_ID`

### 4. Max Episodes Per Show

Control how many recent episodes to check:
```yaml
max_episodes_per_show: 50  # Default: 50
```

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

→ Checking existing episodes in playlist...
  Found 15 episodes already in playlist

→ Processing show: Example Radio Station
  Checking 50 recent episodes...
  ✓ Match: Morning Show - Interview with Jane Doe
  ✓ Match: Special Report: Breaking News
  → Added 2 episodes to playlist

==================================================
Summary:
  Total matching episodes found: 2
  Episodes added to playlist: 2
==================================================
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
- Increase `max_episodes_per_show` if needed

### Permission Errors

- Ensure you have write access to the target playlist
- The playlist must be owned by your Spotify account (or you must be a collaborator)

## Project Structure

```
.
├── .env.example           # Template for credentials
├── .gitignore            # Git ignore file
├── README.md             # This file
├── requirements.txt      # Python dependencies
├── config.yaml           # User configuration
├── auth_setup.py         # First-time authentication helper
└── podcast_filter.py     # Main filtering script
```

## License

MIT License - Use freely for personal or commercial projects.

## Contributing

Feel free to submit issues or pull requests for improvements!