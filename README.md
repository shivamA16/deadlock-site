# Deadlock website

The Deadlock site: landing page, a registration page that sends students to a Stripe payment link, a "You're in" page, and the rules, privacy and conduct pages.

- **Stack:** `build.py` renders Jinja templates into plain HTML, CSS and a little JavaScript in `dist/`. There is no server and no database.
- **Payments:** one Stripe payment link per Open. Stripe collects the student's details and the payment; the site only links to it.
- **Hosting:** Netlify builds the site from GitHub on every push (`netlify.toml`).

```
build.py                    renders the site into dist/ (python build.py --serve to preview)
netlify.toml                Netlify build command, publish folder, security headers
app/
  config.py                 settings from environment variables + the current Open (dates, price)
  options.py                province and year choices shown on the payment link
  templates/                index, register, success, rules, privacy, conduct, 404
  static/                   site.css, state.js, referral.js, Archivo fonts, favicon
scripts/
  create_payment_link.py    creates the payment link for the current Open (run on your computer)
tests/test_build.py         9 tests
```

## How registration works

1. A student opens `/register`, reads what they'll be asked, and clicks **Continue to payment**.
2. Stripe's payment page collects their name, email, school, the school's province or territory, year of study, agreement to the rules, and the CA$10 payment. Free-entry codes work there too.
3. Stripe sends them back to `/register/success` and emails a receipt.
4. You see every entry in the Stripe Dashboard, with the school, province and year on each payment.

Registration opens and closes on the dates in `app/config.py` (Jan 4 to Feb 17, 2027, Eastern). `static/js/state.js` checks the date in the visitor's browser and shows either the payment button or the "entries open/closed" message, so the site switches over on its own without a rebuild. Set `REGISTRATION_OVERRIDE=open` to test before then.

**Referral links:** `https://yourdomain.ca/register?ref=DAL25` attaches `DAL25` to that student's payment (Stripe calls it the client reference ID). Give each ambassador or club their own code.

## Deploy on Netlify

1. **Put the code on GitHub.**
   ```bash
   cd deadlock-site
   git init && git add . && git commit -m "Deadlock site"
   ```
   Create an empty private repository on github.com, then run the two `git remote add origin ...` and `git push -u origin main` lines GitHub shows you.
2. **Create the Netlify project.** At app.netlify.com, choose Add new project, then Import an existing project, then GitHub, and pick the repository. Netlify reads the build settings from `netlify.toml`, so leave those fields as they are.
3. **Add environment variables.** Under Project configuration, then Environment variables, add `SITE_URL`, `CONTACT_EMAIL` and `LEGAL_DRAFT=true` (table below). Then go to Deploys, choose Trigger deploy, and deploy.
4. **Check it.** Open the `https://<name>.netlify.app` address Netlify gives you. Rename the project under Project configuration if you want a nicer address.

Every `git push` to `main` rebuilds the site. After changing an environment variable, use Trigger deploy so the change is built in.

## Connect a GoDaddy domain

1. In Netlify, open Domain management and choose Add a domain. Enter your domain (e.g. `headlock-hq.ca`) and choose to keep your DNS at GoDaddy, not to use Netlify DNS.
2. In GoDaddy, open My Products, then your domain, then DNS:
   - Edit the **A** record with name `@` (GoDaddy's "Parked" record) so it points to `75.2.60.5`. Delete any other A or AAAA records named `@`.
   - Edit the **CNAME** record with name `www` so it points to `<name>.netlify.app` (your Netlify project's address, without `https://`).
   - Make sure GoDaddy's domain forwarding is off.
3. Back in Netlify, under Domain management then HTTPS, wait for the certificate. It's issued automatically once GoDaddy's changes spread, usually within an hour (up to 48).

## Set up Stripe (one time per Open)

1. **Public details:** in Stripe, go to Settings, then Business, then Public details. Set website `https://yourdomain.ca`, support email, terms of service `https://yourdomain.ca/rules` and privacy policy `https://yourdomain.ca/privacy`.
2. **Receipts:** under Settings, then Customer emails, turn on **Successful payments**.
3. **Create the payment link** on your computer, with Test mode on in Stripe:
   ```bash
   python3 -m venv .venv && source .venv/bin/activate
   pip install -r requirements-dev.txt
   STRIPE_SECRET_KEY=sk_test_... SITE_URL=https://yourdomain.ca python scripts/create_payment_link.py
   ```
   It prints a `https://buy.stripe.com/...` address. The secret key is only used by this script, never by the site.
4. **Connect it:** in Netlify, add `PAYMENT_LINK_URL` with that address and `REGISTRATION_OVERRIDE=open`, then trigger a deploy.
5. **Test:** open `/register` and pay with card `4242 4242 4242 4242`, any future date and any CVC. Check that you land on "You're in" and that the payment appears in Stripe with the school, province and year.
6. **Go live:** activate your Stripe account, run the script again with your live key (`sk_live_...`), and set `PAYMENT_LINK_URL` to the new link. Then delete `REGISTRATION_OVERRIDE`, set `LEGAL_DRAFT=false` once a lawyer has reviewed the legal pages, and trigger a deploy.

The script sets three custom fields on the payment page: school, province or territory, and year of study. Three is Stripe's limit.

## Environment variables (set in Netlify)

| Variable | Required | What it does |
| --- | --- | --- |
| `PAYMENT_LINK_URL` | Yes | The payment link for the current Open. Without it, the register page says entries aren't available. |
| `SITE_URL` | Yes | Public address, no trailing slash, e.g. `https://headlock-hq.ca` |
| `CONTACT_EMAIL` | Yes | Contact, partner and refund links |
| `DISCORD_URL` | No | Shown on the success page |
| `REGISTRATION_OVERRIDE` | No | `open` or `closed` to ignore the dates; delete it for normal behaviour |
| `LEGAL_DRAFT` | No | Shows the "draft for legal review" banner on legal pages until set to `false` |

## Everyday tasks

- **See who registered:** in Stripe, open Payment links, pick the link, then Payments. For a spreadsheet, go to Transactions, click Export, and include the custom field columns.
- **Free entries for ambassadors:** create a 100%-off coupon under Product catalog, then Coupons, and give out promotion codes from it.
- **Duplicates and refunds:** the payment link can't stop someone paying twice. Refund the extra payment from the Dashboard.
- **Close registration:** the site hides the button after the closing date. Also deactivate the payment link in Stripe, since anyone holding the direct link could still pay.
- **Next Open:** add a new `Event` in `app/config.py`, point `CURRENT_EVENT` at it, run the script again, update `PAYMENT_LINK_URL`, and push.
- **Change copy:** edit `app/templates/index.html` (styles in `app/static/css/site.css`) and push.

## Preview locally

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
PAYMENT_LINK_URL=https://buy.stripe.com/test_... python build.py --serve
```

Open http://localhost:8080. Run the tests with `pytest`.

## Before registration opens (Jan 4, 2027)

- [ ] Fill in the bracketed placeholders in `rules.html` and `privacy.html` (legal entity, address, prize split, retention period, governing province).
- [ ] Have a lawyer review the rules, privacy policy and code of conduct, then set `LEGAL_DRAFT=false`.
- [ ] Activate your Stripe account and create the live payment link.
- [ ] Turn on successful-payment receipts.
- [ ] Set `PAYMENT_LINK_URL`, `SITE_URL`, `CONTACT_EMAIL` and `DISCORD_URL`, and delete `REGISTRATION_OVERRIDE`.
- [ ] Replace the shortlist on the homepage with your real briefs and problem owners.
- [ ] Make one real CA$10 payment and refund it.

## What the payment link doesn't collect

Stripe allows only three custom fields, so GitHub username, university or college, hackathon experience, how they heard about you, and opt-ins for marketing emails and partner sharing aren't collected at checkout. Ask for them in your enrolment check email or a short follow-up form. Don't send marketing emails without that opt-in (Canada's anti-spam law, CASL).

## Notes

- The homepage standings table and Builder Card use example names, labelled as examples.
- `netlify.toml` sends a strict Content Security Policy (no inline scripts or styles). If you add analytics, add its domain there.
- Archivo is self-hosted from `@fontsource-variable/archivo` under the SIL Open Font License (`app/static/fonts/OFL.txt`).
