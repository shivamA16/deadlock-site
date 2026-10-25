"""Build the Deadlock site into dist/ as plain HTML, CSS and JavaScript.

    python build.py           build into dist/
    python build.py --serve   build, then preview at http://localhost:8080

Netlify runs `python build.py` on every deploy (see netlify.toml). Settings come from
environment variables set in Netlify: PAYMENT_LINK_URL, SITE_URL, CONTACT_EMAIL, DISCORD_URL,
REGISTRATION_OVERRIDE and LEGAL_DRAFT.
"""

from __future__ import annotations

import hashlib
import shutil
import sys
from datetime import timezone
from pathlib import Path
from urllib.parse import urlencode

from jinja2 import Environment, FileSystemLoader, StrictUndefined, select_autoescape

from app.config import CURRENT_EVENT, SEASON, Settings, load_settings

ROOT = Path(__file__).resolve().parent
TEMPLATES = ROOT / "app" / "templates"
STATIC = ROOT / "app" / "static"

# template -> (output file, public path). Netlify serves /register from register.html.
PAGES = [
    ("index.html", "index.html", "/"),
    ("register.html", "register.html", "/register"),
    ("success.html", "register/success.html", "/register/success"),
    ("rules.html", "rules.html", "/rules"),
    ("privacy.html", "privacy.html", "/privacy"),
    ("conduct.html", "conduct.html", "/conduct"),
    ("404.html", "404.html", "/404"),
]


def calendar_link(settings: Settings) -> str:
    ev = CURRENT_EVENT
    fmt = "%Y%m%dT%H%M%SZ"
    start = ev.starts_at.astimezone(timezone.utc).strftime(fmt)
    end = ev.ends_at.astimezone(timezone.utc).strftime(fmt)
    query = urlencode(
        {
            "action": "TEMPLATE",
            "text": f"Deadlock {ev.full_name}",
            "dates": f"{start}/{end}",
            "details": f"The brief drops at the start. Submissions close at the end. {settings.site_url}",
            "location": "Online",
        }
    )
    return f"https://calendar.google.com/calendar/render?{query}"


def make_static_url():
    cache: dict[str, str] = {}

    def static(path: str, versioned: bool = True) -> str:
        """URL for a file in app/static, with a content hash so browsers pick up changes."""
        if not versioned:
            return f"/static/{path}"
        if path not in cache:
            digest = hashlib.sha256((STATIC / path).read_bytes()).hexdigest()[:10]
            cache[path] = f"/static/{path}?v={digest}"
        return cache[path]

    return static


def build(out: Path, settings: Settings | None = None) -> list[Path]:
    settings = settings or load_settings()
    if not settings.payment_link_url:
        print("warning: PAYMENT_LINK_URL is not set; the register page will say entries aren't available")

    env = Environment(
        loader=FileSystemLoader(TEMPLATES),
        autoescape=select_autoescape(["html"]),
        undefined=StrictUndefined,
    )
    env.globals.update(
        event=CURRENT_EVENT,
        season=SEASON,
        settings=settings,
        static=make_static_url(),
    )

    if out.exists():
        shutil.rmtree(out)
    shutil.copytree(STATIC, out / "static")

    written = []
    for template, filename, path in PAGES:
        html = env.get_template(template).render(
            page_path=path,
            pay_url=settings.payment_link_url,
            calendar_link=calendar_link(settings),
        )
        target = out / filename
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(html, encoding="utf-8")
        written.append(target)
    print(f"Built {len(written)} pages into {out}")
    return written


def serve(out: Path, port: int = 8080) -> None:
    """Preview like Netlify: /register serves register.html, unknown paths get 404.html."""
    from functools import partial
    from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

    class Handler(SimpleHTTPRequestHandler):
        def send_head(self):
            path = self.path.split("?", 1)[0]
            if path != "/" and not Path(path).suffix and (out / f"{path.lstrip('/')}.html").exists():
                self.path = path + ".html"
            elif not (out / path.lstrip("/")).exists() and path != "/":
                self.send_response(404)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                return open(out / "404.html", "rb")
            return super().send_head()

    server = ThreadingHTTPServer(("127.0.0.1", port), partial(Handler, directory=str(out)))
    print(f"Previewing at http://localhost:{port} (Ctrl+C to stop)")
    server.serve_forever()


if __name__ == "__main__":
    dist = ROOT / "dist"
    build(dist)
    if "--serve" in sys.argv:
        serve(dist)
