import importlib.util
import re
import tomllib
from dataclasses import replace
from pathlib import Path

import pytest

import build
from app.config import load_settings
from app.options import PROVINCES, YEARS

ROOT = Path(__file__).resolve().parent.parent
LINK = "https://buy.stripe.com/test_abc123"


def settings(**changes):
    base = replace(
        load_settings(),
        payment_link_url=LINK,
        site_url="https://headlock-hq.ca",
        contact_email="hello@headlock-hq.ca",
        registration_override="",
        legal_draft=True,
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
    assert (tmp_path / "dist" / "static" / "js" / "state.js").exists()


def test_homepage(site):
    page = site()("index.html")
    assert "Get noticed." in page
    assert "interview round" not in page
    assert 'data-opens="2027-01-04T09:00:00-05:00"' in page
    assert 'data-closes="2027-02-17T23:59:59-05:00"' in page
    assert re.search(r'/static/css/site\.css\?v=[0-9a-f]{10}', page)
    assert '<meta property="og:url" content="https://headlock-hq.ca/">' in page


def test_register_page_links_to_payment_link(site):
    page = site()("register.html")
    assert f'href="{LINK}"' in page
    assert "data-pay-link" in page
    assert "referral.js" in page
    for state in ("when-not-open", "when-open", "when-closed"):
        assert f'class="{state}"' in page


def test_register_page_without_payment_link(site):
    page = site(payment_link_url="")("register.html")
    assert "aren't available right now" in page
    assert "Continue to payment" not in page


def test_override_is_passed_to_the_browser(site):
    assert 'data-override="open"' in site(registration_override="open")("index.html")
    assert "data-override" not in site(registration_override="maybe")("index.html")


def test_success_and_404(site):
    get = site()
    assert "You're in." in get("register/success.html")
    assert "calendar.google.com" in get("register/success.html")
    assert "Dead end." in get("404.html")


def test_legal_draft_banner(site):
    assert "Draft for legal review" in site()("rules.html")
    assert "Draft for legal review" not in site(legal_draft=False)("rules.html")


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
