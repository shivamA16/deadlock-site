# Deadlock website

The Deadlock site: landing page, an interest page that sends students to an interest-list form (Tally) after they confirm they're 18+ and agree to emails, a "You're on the list" page, and the rules, privacy and conduct pages.

**The site is interest-only for now.** Every button says "Register your interest". The Stripe payment flow (`scripts/create_payment_link.py`) is kept for when paid entries reopen. Read `docs/LEGAL_CHECKLIST.md` before launching.

- **Stack:** `build.py` renders Jinja templates into plain HTML, CSS and a little JavaScript in `dist/`. There is no server and no database.
- **Interest list:** `/register` shows the age and email-consent checkboxes, then sends people to the Tally form set in `interest_url` (`app/config.py`). Set the form's redirect to `/register/success`.
- **Payments (dormant):** one Stripe payment link per Open. Stripe collects the student's details and the payment.
- **No third parties on the site:** no cookies, analytics, session replay or external fonts. A test fails the build if a page loads anything from another domain.
- **Hosting:** Netlify builds the site from GitHub on every push (`netlify.toml`).

```
build.py                    renders the site into dist/ (python build.py --serve to preview)
netlify.toml                Netlify build command, publish folder, security headers
app/
  config.py                 settings from environment variables + the current Open (dates, price)
  options.py                province and year choices shown on the payment link
  templates/                index, register (interest page), success, rules, privacy, conduct, 404
  static/                   site.css, interest.js, Archivo fonts, favicon
docs/LEGAL_CHECKLIST.md     what the code handles and what you must still do
scripts/
  create_payment_link.py    creates the payment link for the current Open (run on your computer)
tests/test_build.py         build, content and legal-guard tests
```

## How registering interest works

1. A student clicks **Register your interest** anywhere on the site and lands on `/register`.
2. They tick two unticked boxes: "I'm 18 or older and enrolled at a Canadian university or college" and "Deadlock can email me about the Winter Open and future Opens". The page names the sender, mailing address and contact email.
3. **Continue to the interest form** unlocks and opens the Tally form. The form must repeat both checkboxes so the submission is your record of consent (see `docs/LEGAL_CHECKLIST.md`).
4. Tally redirects them to `/register/success` ("You're on the list").

**Referral links:** `https://yourdomain.ca/register?ref=DAL25` passes `ref=DAL25` on to the Tally form. Add a hidden field called `ref` to the form to record it.

## Deploy on Netlify

1. **Put the code on GitHub.**
   ```bash
   cd deadlock-site
   git init && git add . && git commit -m "Deadlock site"
   ```
   Create an empty private repository on github.com, then run the two `git remote add origin ...` and `git push -u origin main` lines GitHub shows you.
2. **Create the Netlify project.** At app.netlify.com, choose Add new project, then Import an existing project, then GitHub, and pick the repository. Netlify reads the build settings from `netlify.toml`, so leave those fields as they are.
3. **Add environment variables.** Under Project configuration, then Environment variables, add `SITE_URL`, `CONTACT_EMAIL`, `LEGAL_DRAFT=true`, `LEGAL_ENTITY` and `MAILING_ADDRESS` (table below). Then go to Deploys, choose Trigger deploy, and deploy.
4. **Check it.** Open the `https://<name>.netlify.app` address Netlify gives you. Rename the project under Project configuration if you want a nicer address.

Every `git push` to `main` rebuilds the site. After changing an environment variable, use Trigger deploy so the change is built in.

## Connect a GoDaddy domain

1. In Netlify, open Domain management and choose Add a domain. Enter your domain (e.g. `headlock-hq.ca`) and choose to keep your DNS at GoDaddy, not to use Netlify DNS.
2. In GoDaddy, open My Products, then your domain, then DNS:
   - Edit the **A** record with name `@` (GoDaddy's "Parked" record) so it points to `75.2.60.5`. Delete any other A or AAAA records named `@`.
   - Edit the **CNAME** record with name `www` so it points to `<name>.netlify.app` (your Netlify project's address, without `https://`).
   - Make sure GoDaddy's domain forwarding is off.
3. Back in Netlify, under Domain management then HTTPS, wait for the certificate. It's issued automatically once GoDaddy's changes spread, usually within an hour (up to 48).

## Set up Stripe (only when paid entries reopen)

1. **Public details:** in Stripe, go to Settings, then Business, then Public details. Set website `https://yourdomain.ca`, support email, terms of service `https://yourdomain.ca/rules` and privacy policy `https://yourdomain.ca/privacy`.
2. **Receipts:** under Settings, then Customer emails, turn on **Successful payments**.
3. **Create the payment link** on your computer, with Test mode on in Stripe:
   ```bash
   python3 -m venv .venv && source .venv/bin/activate
   pip install -r requirements-dev.txt
   STRIPE_SECRET_KEY=sk_test_... SITE_URL=https://yourdomain.ca python scripts/create_payment_link.py
   ```
   It prints a `https://buy.stripe.com/...` address. The secret key is only used by this script, never by the site.
4. **Connect it:** in Netlify, add `PAYMENT_LINK_URL` with that address. The templates don't use it while the site is interest-only, so reopening paid entries also means bringing back an Enter button that links to it.
5. **Test:** open `/register` and pay with card `4242 4242 4242 4242`, any future date and any CVC. Check that you land on "You're in" and that the payment appears in Stripe with the school, province and year.
6. **Go live:** activate your Stripe account, run the script again with your live key (`sk_live_...`), and set `PAYMENT_LINK_URL` to the new link. Then set `LEGAL_DRAFT=false` once a lawyer has reviewed the legal pages, and trigger a deploy.

The script sets three custom fields on the payment page: school, province or territory, and year of study. Three is Stripe's limit.

## Environment variables (set in Netlify)

| Variable | Required | What it does |
| --- | --- | --- |
| `SITE_URL` | Yes | Public address, no trailing slash, e.g. `https://headlock-hq.ca` |
| `CONTACT_EMAIL` | Yes | Contact, privacy and refund links |
| `LEGAL_ENTITY` | Before launch | Organizer's registered name, shown on the interest page, rules and privacy policy |
| `MAILING_ADDRESS` | Before launch | Postal address (required in marketing emails) |
| `GOVERNING_PROVINCE` | Before launch | Province whose laws govern the rules |
| `RETENTION_PERIOD` | Before launch | How long records are kept, e.g. `24 months` |
| `LEGAL_DRAFT` | No | `true` shows the "draft for legal review" banner. Setting `false` makes the build refuse to publish while any `[placeholder]` remains in the legal pages. |
| `DISCORD_URL` | No | Shown on the success page |
| `PAYMENT_LINK_URL` | Only for paid entries | The Stripe payment link. Not used while the site is interest-only. |

## Everyday tasks

- **See who registered interest:** open the form's Submissions in Tally. Export them and keep the export: it's your proof of email consent.
- **Unsubscribes:** remove the person from your list the same day and keep a log.
- **Next Open:** add a new `Event` in `app/config.py` (with its `interest_url`), point `CURRENT_EVENT` at it, and push.
- **Change copy:** edit `app/templates/index.html` (styles in `app/static/css/site.css`) and push.

## Preview locally

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
python build.py --serve
```

Open http://localhost:8080. Run the tests with `pytest`.

## Before you launch

- [ ] Add the two consent checkboxes to the Tally form and set its redirect (see `docs/LEGAL_CHECKLIST.md`).
- [ ] Set `LEGAL_ENTITY`, `MAILING_ADDRESS`, `GOVERNING_PROVINCE`, `RETENTION_PERIOD` and `CONTACT_EMAIL`.
- [ ] Resolve the bracketed notes in `rules.html`.
- [ ] Have a lawyer review the rules, privacy policy and code of conduct, then set `LEGAL_DRAFT=false`.
- [ ] Confirm the mentor, hiring-partner and "verified" claims on the homepage are true.
- [ ] Replace the example briefs with real ones once problem owners are confirmed.

## Notes

- The homepage standings table, Builder Card and briefs are examples, labelled as examples.
- `netlify.toml` sends a strict Content Security Policy (no inline scripts or styles). If you add analytics, add its domain there.
- Archivo is self-hosted from `@fontsource-variable/archivo` under the SIL Open Font License (`app/static/fonts/OFL.txt`).
