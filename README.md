# CDG Browse

A fully custom-drawn, aesthetic desktop browser built with PyQt6 and QtWebEngine, in a single Python file.
Every button, tab, slider, switch and panel is custom painted.

## Features

- Custom themes, accent colors, pill buttons, gradient toolbar, floating orbs
- Build mode: rearrange the toolbar, move tabs to the side, density presets, templates
- Spaces (separate workspaces with their own theme)
- Built-in ad blocker
- Start page with bookmark tiles (including CDG Chat)
- CDG coins, achievements and a theme shop
- Accounts: username/email, plus optional Google and GitHub sign-in
- Smooth slide-in / slide-out notifications

## Install

Requires Python 3.9+.

```bash
git clone https://github.com/YOUR-USERNAME/cdg-browse.git
cd cdg-browse
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python3 cdg_browse.py
```

## Optional: Google / GitHub sign-in

Create your own OAuth apps and provide the IDs either as environment variables
(`CDG_GOOGLE_CLIENT_ID`, `CDG_GOOGLE_CLIENT_SECRET`, `CDG_GITHUB_CLIENT_ID`) or in
`~/.cdg_browse/oauth.json`:

```json
{"google_client_id": "...", "google_client_secret": "...", "github_client_id": "..."}
```

Never commit these values.

## CDG Chat (built in, no extra files)

CDG Chat lives inside `cdg_browse.py`. Sign in to a CDG account, then click the **CDG Chat** tile on the start page.

- **Just you / testing:** it starts a private chat server on your computer automatically.
- **Chat with friends:** one person hosts the server, everyone else points their browser at it.

Host a server (needs only Python, no PyQt):

```bash
python3 cdg_browse.py --chat-server --port 8765
```

Everyone else (including the host) opens **Settings > Browsing > Chat server** and enters `http://HOST-IP:8765`, then clicks the CDG Chat tile.
You can also set the `CDG_CHAT_URL` environment variable instead.

Over the internet, put the server behind HTTPS (for example a reverse proxy such as Caddy or nginx) so keys aren't sent in plain text.

How it works: your username plus a secret key derived from your account identify you. The first person to use a name owns it,
and nobody else can post as that name. Messages are saved on the server in `~/.cdg_browse/chat_server.json`.

## Data

Settings and account data are stored locally in `~/.cdg_browse/`.

## License

MIT
