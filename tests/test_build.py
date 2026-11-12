import importlib.util
import re
from html.parser import HTMLParser
import tomllib
from dataclasses import replace
from pathlib import Path

import pytest

import build
from app.config import CURRENT_EVENT, load_settings
from app.options import PROVINCES, YEARS

ROOT = Path(__file__).resolve().parent.parent
LINK = "https://buy.stripe.com/test_abc123"


def settings(**changes):
    base = replace(
        load_settings(),
        payment_link_url=LINK,
        site_url="https://headlock-hq.ca",
        contact_email="hello@headlock-hq.ca",
        legal_draft=True,
        legal_entity="",
        mailing_address="",
        governing_province="",
        retention_period="",
    )
    return replace(base, **changes)


@pytest.fixture
def site(tmp_path):
    def make(**changes):
        out = tmp_path / "dist"
        build.build(out, settings(**changes))
        return lambda name: (out / name).read_text(encoding="utf-8")

    return make


def test_all_pages_are_built(site, tmp_path):
    site()
    for _, filename, _ in build.PAGES:
        assert (tmp_path / "dist" / filename).exists()
    assert (tmp_path / "dist" / "static" / "js" / "interest.js").exists()
    assert not (tmp_path / "dist" / "static" / "js" / "state.js").exists()


def test_homepage(site):
    page = site()("index.html")
    assert "Get noticed." in page
    assert "interview round" not in page
    assert re.search(r'/static/css/site\.css\?v=[0-9a-f]{10}', page)
    assert '<meta property="og:url" content="https://headlock-hq.ca/">' in page


def test_every_button_says_register_your_interest(site):
    get = site()
    for name in ("index.html", "404.html", "register.html"):
        page = get(name)
        assert "Enter for" not in page
        assert "Enter the " not in page
        assert "Continue to payment" not in page
    home = get("index.html")
    assert home.count('href="/register"') == 4  # header, hero, example briefs, season
    assert "buy.stripe.com" not in home + get("register.html")


def test_requested_content_changes(site):
    page = site()("index.html")
    assert "Example briefs" in page
    assert "Pick the" not in page
    assert "never less than" not in page
    assert "Ship It" not in page
    assert "Winner merch" in page
    assert "Engraved keycaps for every top-10 finish" in page
    assert "senior engineers from top companies in different industries" in page
    assert "on LinkedIn" in page
    assert "Voting opens" not in page
    assert page.count("<tr><td>") >= 8


def test_prize_floor_is_gone_everywhere(site):
    get = site()
    for name in ("index.html", "register.html", "rules.html"):
        assert "guaranteed" not in get(name)
        assert "$500" not in get(name)


def test_interest_page_gates_the_form_behind_age_and_email_consent(site):
    page = site()("register.html")
    assert page.count("data-consent") == 2
    assert "checked" not in page  # nothing is pre-ticked
    assert "18 or older" in page
    assert "Deadlock can email me" in page
    assert "unsubscribe" in page
    assert f'data-href="{CURRENT_EVENT.interest_url}"' in page
    assert not re.search(rf'(?<!data-)href="{re.escape(CURRENT_EVENT.interest_url)}"', page)  # not followable until ticked
    assert "disabled" in page and "interest.js" in page
    assert "hello@headlock-hq.ca" in page


def test_age_is_stated_where_people_sign_up(site):
    get = site()
    assert "18 or older" in get("index.html")
    assert "at least 18" in get("rules.html")
    assert "under 18" in get("privacy.html")
    assert "parent" not in get("rules.html").lower()


def test_no_third_party_requests(site, tmp_path):
    """Self-hosted fonts and code only: no Google Fonts, analytics, or session-replay scripts."""
    site()
    out = tmp_path / "dist"

    class Refs(HTMLParser):
        def __init__(self):
            super().__init__()
            self.external = []

        def handle_starttag(self, tag, attrs):
            attrs = dict(attrs)
            if tag in ("script", "img", "iframe", "source", "video", "audio"):
                url = attrs.get("src", "")
            elif tag == "link":
                url = attrs.get("href", "")
            else:
                return
            if url.startswith(("http://", "https://", "//")):
                self.external.append(url)

    for page in out.rglob("*.html"):
        parser = Refs()
        parser.feed(page.read_text(encoding="utf-8"))
        assert not parser.external, (page.name, parser.external)
    css = (out / "static" / "css" / "site.css").read_text()
    assert not re.search(r"@import|url\(\s*[\"']?(https?:)?//", css)
    for js in (out / "static" / "js").glob("*.js"):
        assert not re.search(r"fullstory|hotjar|clarity|logrocket|mouseflow|gtag|analytics|sessionreplay", js.read_text(), re.I)
    config = tomllib.loads((ROOT / "netlify.toml").read_text())
    csp = config["headers"][0]["values"]["Content-Security-Policy"]
    assert "default-src 'self'" in csp and "script-src 'self'" in csp and "font-src 'self'" in csp
    assert "google" not in csp


def test_privacy_policy_covers_the_legal_points(site):
    page = site()("privacy.html")
    for phrase in ("no cookies", "session recording", "Tally", "Stripe", "Netlify", "outside Canada", "unsubscribe",
                   "mailing address", "withdraw", "Privacy Commissioner", "only with your permission"):
        assert phrase in page, phrase
    assert "Google Cloud" not in page


def test_emails_must_identify_the_sender(site):
    page = site(legal_entity="Deadlock Inc.", mailing_address="1 Main St, Toronto, ON M5V 1A1")("register.html")
    assert "Deadlock Inc., 1 Main St, Toronto, ON M5V 1A1" in page


def test_no_subscription_or_auto_renewal(site):
    get = site()
    assert "Nothing renews automatically" in get("index.html")
    assert "not a subscription" in get("rules.html").lower()
    script = importlib.util.spec_from_file_location("p", ROOT / "scripts" / "create_payment_link.py")
    mod = importlib.util.module_from_spec(script)
    script.loader.exec_module(mod)
    params = mod.link_params("price_123", "https://headlock-hq.ca")
    assert "not a subscription" in params["custom_text"]["submit"]["message"]
    assert "18 or older" in params["custom_text"]["terms_of_service_acceptance"]["message"]
    assert all("recurring" not in item for item in params["line_items"])


def test_no_user_uploads_and_copyright_contact(site):
    page = site()("rules.html")
    assert "we don't host them" in page
    assert "Copyright and other complaints" in page
    for name in ("index.html", "register.html"):
        assert 'type="file"' not in site()(name)


def test_featured_builders_need_permission(site):
    get = site()
    assert "Nothing is published about you without your permission" in get("index.html")
    assert "separate written permission" in get("rules.html")


def test_build_refuses_placeholders_once_legal_review_is_done(tmp_path):
    with pytest.raises(SystemExit, match="placeholders"):
        build.build(tmp_path / "dist", settings(legal_draft=False))
    # with every setting filled in, only the lawyer's bracketed notes remain, and those also block the build
    filled = settings(
        legal_draft=False,
        legal_entity="Deadlock Inc.",
        mailing_address="1 Main St, Toronto, ON",
        governing_province="Ontario",
        retention_period="24 months",
    )
    with pytest.raises(SystemExit, match="Counsel"):
        build.build(tmp_path / "dist", filled)


def test_success_and_404(site):
    get = site()
    assert "You're on the list." in get("register/success.html")
    assert "calendar.google.com" in get("register/success.html")
    assert "Dead end." in get("404.html")


def test_legal_draft_banner(site):
    assert "Draft for legal review" in site()("rules.html")
    # LEGAL_DRAFT=false is refused until every placeholder is filled in (see the last test).


def test_netlify_config():
    config = tomllib.loads((ROOT / "netlify.toml").read_text())
    assert config["build"]["command"] == "python build.py"
    assert config["build"]["publish"] == "dist"
    assert config["build"]["environment"]["PYTHON_VERSION"] == "3.12"
    headers = config["headers"][0]["values"]
    assert "frame-ancestors 'none'" in headers["Content-Security-Policy"]


def test_payment_link_settings():
    path = ROOT / "scripts" / "create_payment_link.py"
    spec = importlib.util.spec_from_file_location("create_payment_link", path)
    script = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(script)

    params = script.link_params("price_123", "https://headlock-hq.ca")
    fields = params["custom_fields"]
    assert len(fields) <= 3  # Stripe's limit
    for field in fields:
        options = field.get("dropdown", {}).get("options", [])
        assert len(options) <= 200
        for opt in options:
            assert re.fullmatch(r"[A-Za-z0-9]+", opt["value"])  # Stripe needs alphanumeric values
            assert len(opt["label"]) <= 100
    assert len(PROVINCES) == 13 and len(YEARS) == 6
    assert params["after_completion"]["redirect"]["url"].startswith("https://headlock-hq.ca/register/success")
    assert params["consent_collection"]["terms_of_service"] == "required"
    assert all(len(v["message"]) <= 1200 for v in params["custom_text"].values())
