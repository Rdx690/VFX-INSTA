import re
from urllib.parse import urlparse

import instaloader
from flask import Flask, jsonify, request

app = Flask(__name__)

# Instaloader uses Instagram's publicly available web endpoints.
# No Instagram API key or Telegram bot token is needed.
LOADER = instaloader.Instaloader(
    save_metadata=False,
    download_comments=False,
    quiet=True,
)

SHORTCODE_RE = re.compile(r"/(?:reel|reels|p|tv)/([A-Za-z0-9_-]+)")


def get_shortcode(raw_url):
    """Accept only Instagram post/reel URLs and return the shortcode."""
    try:
        parsed = urlparse(raw_url.strip())
    except Exception:
        return None

    host = (parsed.hostname or "").lower()
    allowed_hosts = {"instagram.com", "www.instagram.com", "m.instagram.com"}
    if parsed.scheme not in {"http", "https"} or host not in allowed_hosts:
        return None

    match = SHORTCODE_RE.search(parsed.path)
    return match.group(1) if match else None


@app.get("/api/health")
def health():
    return jsonify({"ok": True, "service": "Instagram Reel Resolver"})


@app.post("/api/resolve")
def resolve_reel():
    payload = request.get_json(silent=True) or {}
    raw_url = payload.get("url", "")

    if not isinstance(raw_url, str) or not raw_url.strip():
        return jsonify({"error": "Paste an Instagram Reel or post URL first."}), 400

    shortcode = get_shortcode(raw_url)
    if not shortcode:
        return jsonify({
            "error": "That URL doesn't look like a supported Instagram Reel, post, or TV URL."
        }), 400

    try:
        post = instaloader.Post.from_shortcode(LOADER.context, shortcode)

        videos = []
        if post.typename == "GraphSidecar":
            for node in post.get_sidecar_nodes():
                if node.is_video and node.video_url:
                    videos.append(node.video_url)
        elif post.is_video and post.video_url:
            videos.append(post.video_url)

        if not videos:
            return jsonify({
                "error": "No public video was found. The post may be private, unavailable, or an image-only post."
            }), 404

        # Return the available video URL(s), not the video bytes. This avoids
        # Vercel's serverless response-size limits for large video files.
        # Instagram CDN URLs can expire, so resolve again if a link stops working.
        return jsonify({
            "ok": True,
            "shortcode": shortcode,
            "title": (post.caption or "").strip()[:180],
            "video_urls": videos,
            "video_count": len(videos),
            "note": "Direct media links can expire. Resolve the Instagram link again if needed."
        })

    except instaloader.exceptions.PrivateProfileNotFollowedException:
        return jsonify({"error": "This account is private or requires an authorized login."}), 403
    except instaloader.exceptions.LoginRequiredException:
        return jsonify({"error": "Instagram requires login for this post. This demo only supports publicly accessible posts."}), 403
    except instaloader.exceptions.TooManyRequestsException:
        return jsonify({"error": "Instagram is rate-limiting requests. Wait a while and try again."}), 429
    except instaloader.exceptions.QueryReturnedNotFoundException:
        return jsonify({"error": "Instagram couldn't find that post. Check the link or try again later."}), 404
    except Exception:
        app.logger.exception("Instagram resolve failed")
        return jsonify({
            "error": "Instagram couldn't provide the video right now. The post may be unavailable, or Instagram may have changed its website."
        }), 502


# Vercel's Python runtime can serve this Flask WSGI app.
