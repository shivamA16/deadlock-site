"""Site settings (from environment variables) and the current Open."""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime
from zoneinfo import ZoneInfo

ET = ZoneInfo("America/Toronto")


@dataclass(frozen=True)
class Event:
    slug: str
    name: str
    year: int
    dates_label: str
    starts_at: datetime  # brief drops
    ends_at: datetime  # submissions close
    registration_opens: datetime
    registration_closes: datetime
    refund_deadline: datetime
    price_cents: int
    currency: str
    prize_floor: int  # guaranteed cash pool in dollars

    @property
    def price_label(self) -> str:
        dollars = self.price_cents / 100
        return f"${dollars:,.0f}" if dollars.is_integer() else f"${dollars:,.2f}"

    @property
    def full_name(self) -> str:
        return f"{self.name} {self.year}"


WINTER_OPEN_2027 = Event(
    slug="winter-2027",
    name="Winter Open",
    year=2027,
    dates_label="February 19 to 21, 2027",
    starts_at=datetime(2027, 2, 19, 20, 0, tzinfo=ET),
    ends_at=datetime(2027, 2, 21, 23, 0, tzinfo=ET),
    registration_opens=datetime(2027, 1, 4, 9, 0, tzinfo=ET),
    registration_closes=datetime(2027, 2, 17, 23, 59, 59, tzinfo=ET),
    refund_deadline=datetime(2027, 2, 12, 23, 59, 59, tzinfo=ET),
    price_cents=1500,
    currency="cad",
    prize_floor=500,
)

# Change this when the next Open's registration starts, and create a new payment link for it.
CURRENT_EVENT = WINTER_OPEN_2027

SEASON = [
    {"name": "Winter Open", "dates": "Feb 19 to 21", "note": "Winter term"},
    {"name": "Summer Open", "dates": "Jun 18 to 20", "note": "Built for co-op and summer terms"},
    {"name": "Fall Open", "dates": "Sep 24 to 26", "note": "Start of the school year"},
    {"name": "Late Fall Open", "dates": "Nov 12 to 14", "note": "Before December exams"},
    {"name": "The Deadlock 10", "dates": "December", "note": "Season standings decide the list"},
]


@dataclass(frozen=True)
class Settings:
    payment_link_url: str  # the Stripe payment link for the current Open, e.g. https://buy.stripe.com/...
    site_url: str
    contact_email: str
    discord_url: str
    registration_override: str  # "", "open" or "closed"
    legal_draft: bool


def load_settings() -> Settings:
    return Settings(
        payment_link_url=os.environ.get("PAYMENT_LINK_URL", "").strip(),
        # Netlify sets URL to the site's main address during builds.
        site_url=(os.environ.get("SITE_URL") or os.environ.get("URL") or "http://localhost:8080").rstrip("/"),
        contact_email=os.environ.get("CONTACT_EMAIL", "hello@example.com"),
        discord_url=os.environ.get("DISCORD_URL", ""),
        registration_override=os.environ.get("REGISTRATION_OVERRIDE", "").strip().lower(),
        legal_draft=os.environ.get("LEGAL_DRAFT", "true").strip().lower() != "false",
    )

