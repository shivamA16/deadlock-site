"""Create the Stripe payment link for the current Open. Run it once per Open, on your own computer.

    pip install stripe
    STRIPE_SECRET_KEY=sk_test_... SITE_URL=https://deadlockopen.ca python scripts/create_payment_link.py

It prints a https://buy.stripe.com/... address. Put that in the site's PAYMENT_LINK_URL setting.
Your secret key is only used here; the website itself never needs it.

Before running: in the Stripe Dashboard, open Settings > Business > Public details and set
"Terms of service" to SITE_URL/rules and "Privacy policy" to SITE_URL/privacy.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import stripe  # noqa: E402

from app.config import CURRENT_EVENT  # noqa: E402
from app.options import PROVINCES, YEARS  # noqa: E402


def link_params(price_id: str, site_url: str) -> dict:
    ev = CURRENT_EVENT
    return {
        "line_items": [{"price": price_id, "quantity": 1}],
        "name_collection": {"individual": {"enabled": True}},
        "custom_fields": [
            {
                "key": "school",
                "label": {"type": "custom", "custom": "School"},
                "type": "text",
                "text": {"minimum_length": 2, "maximum_length": 120},
            },
            {
                "key": "province",
                "label": {"type": "custom", "custom": "School's province or territory"},
                "type": "dropdown",
                "dropdown": {"options": [{"value": code, "label": name} for code, name in PROVINCES]},
            },
            {
                "key": "year",
                "label": {"type": "custom", "custom": "Year of study"},
                "type": "dropdown",
                "dropdown": {"options": [{"value": value, "label": label} for value, label in YEARS]},
            },
        ],
        "consent_collection": {"terms_of_service": "required"},
        "custom_text": {
            "terms_of_service_acceptance": {
                "message": (
                    "I'm enrolled at a Canadian university or college, I'll build my entry on my own, "
                    f"and I agree to the [Official Rules]({site_url}/rules) "
                    f"and [Code of Conduct]({site_url}/conduct)."
                )
            },
            "submit": {
                "message": (
                    "Use your school email above: we use it to check that you're enrolled. "
                    "Deadlock is a contest of skill. Winners are chosen by judges, never by chance."
                )
            },
        },
        "allow_promotion_codes": True,
        "after_completion": {
            "type": "redirect",
            "redirect": {"url": f"{site_url}/register/success?session_id={{CHECKOUT_SESSION_ID}}"},
        },
        "inactive_message": f"Entries for the Deadlock {ev.name} are closed. See {site_url} for the next Open.",
        "metadata": {"event": ev.slug},
        "payment_intent_data": {
            "description": f"Deadlock {ev.full_name} entry",
            "metadata": {"event": ev.slug},
        },
    }


def main() -> None:
    key = os.environ.get("STRIPE_SECRET_KEY", "")
    site_url = os.environ.get("SITE_URL", "").rstrip("/")
    if not key or not site_url:
        sys.exit("Set STRIPE_SECRET_KEY and SITE_URL first. See the top of this file.")

    stripe.api_key = key
    ev = CURRENT_EVENT
    product = stripe.Product.create(
        name=f"Deadlock {ev.full_name} entry",
        description=f"{ev.dates_label}. One solo entry, online.",
        metadata={"event": ev.slug},
    )
    price = stripe.Price.create(product=product.id, currency=ev.currency, unit_amount=ev.price_cents)
    link = stripe.PaymentLink.create(**link_params(price.id, site_url))

    mode = "TEST" if key.startswith(("sk_test_", "rk_test_")) else "LIVE"
    print(f"{mode} payment link for the {ev.full_name}:")
    print(link.url)
    print("\nSet PAYMENT_LINK_URL to that address and redeploy the site.")


if __name__ == "__main__":
    main()
