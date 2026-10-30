# ReelDrop — Instagram Reel Downloader (Vercel)

A responsive static frontend with a Python Flask serverless backend. It uses Instaloader to resolve publicly accessible Instagram video posts without a paid third-party API.

## Important Vercel limitation

This project returns Instagram's direct media URL(s) instead of proxying the video bytes through Vercel. That avoids serverless response-size limits for large videos. Instagram CDN links can expire, and the browser may open the video rather than force-save it; use the browser's video menu or download/save option where available. Private or login-gated posts are not supported.

## Deploy to Vercel

1. Upload the project files to a GitHub repository.
2. In Vercel, choose **Add New → Project** and import that repository.
3. Keep the project root at the repository root.
4. Deploy. The included `vercel.json` maps the static site and `/api/*` requests.
5. Open the deployed URL and test with a public Reel URL.

## Local development

Use Python 3.10+.

```bash
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt
python -c "from api.index import app; app.run(host='127.0.0.1', port=5000, debug=True)"
```

Open `public/index.html` through a local static server and proxy `/api/*` to Flask, or use Vercel CLI (`vercel dev`) for a closer match to deployment.

## Security

- No Telegram bot token, Instagram password, or API key is needed or included.
- Do not add secrets to frontend HTML or commit them to GitHub.
- The backend only accepts Instagram domains and public post URL patterns.
- Automated access may be rate-limited or changed by Instagram. Use only for content you own or have permission to save.
