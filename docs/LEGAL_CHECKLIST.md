# Legal checklist

What the site now does, and what still has to be done outside the code. None of this is legal advice;
a Canadian lawyer should review the rules, privacy policy and code of conduct before launch.

## What the code now handles

| Risk | What the site does |
| --- | --- |
| **Age (COPPA and age of majority)** | Deadlock is 18+ and says so on the homepage, the interest page, the rules and the privacy policy. The interest page makes people tick "I'm 18 or older and enrolled" before the form link works. The parental-consent route was removed from the rules. The Stripe checkout text also says 18+. The site never asks for a date of birth. |
| **Google Fonts and other third-party requests (GDPR)** | Archivo is self-hosted. The Content Security Policy blocks every third-party script, font, image and frame. A test fails the build if any page or stylesheet loads something from another domain. |
| **Session replay and trackers (wiretapping laws)** | None are installed and the CSP would block them. The privacy policy and footer say so. Do not add analytics or replay tools without updating the CSP, the policy and the footer first. |
| **Marketing email (CASL and CAN-SPAM)** | Consent is separate, unticked and specific (box 2 on `/register`). The page names the sender, postal address and contact email. The privacy policy explains withdrawal. See "Email rules" below for what every email needs. |
| **Subscriptions and auto-renewal** | There are none. The homepage, rules and Stripe checkout text say each Open is a one-time fee and nothing renews. Keep it that way, or add clear renewal terms next to the button before selling anything recurring. |
| **User uploads and DMCA** | The site hosts no uploads. Submissions are links to material people host themselves, and the rules say so. The rules have a copyright-complaints contact. |
| **Featured builders (The Deadlock 10 and LinkedIn posts)** | The homepage, rules and privacy policy say profiles are published only with the builder's separate permission. |
| **Placeholders reaching production** | Set `LEGAL_DRAFT=false` and the build refuses to publish while any `[bracketed]` placeholder is left in the legal pages. |

## You must do these (the code can't)

1. **Add the same two required checkboxes to your Tally form**, unticked, with the same wording as `/register`: "I'm 18 or older and enrolled at a Canadian university or college" and "Deadlock can email me about the Winter Open 2027 and future Opens. I can unsubscribe at any time." The tick on our page isn't recorded anywhere; the Tally submission, with its timestamp, is your proof of consent. Keep it. Also:
   - Ask only for what you need (name, email, school). No date of birth, phone number or government ID.
   - Put a link to `/privacy` in the form's intro text.
   - Turn off any Tally analytics or tracking options you don't need.
   - Set the form's redirect after submission to `/register/success`.
   - Add a hidden field named `ref` if you want referral codes (`/register?ref=DAL25`) recorded.
2. **Fill in the details**, in Netlify environment variables: `LEGAL_ENTITY`, `MAILING_ADDRESS` (a real postal address, a PO box or registered mail address is fine), `GOVERNING_PROVINCE` and `RETENTION_PERIOD`. Resolve the bracketed notes in `rules.html` (prize split, exclusion list, Quebec wording, skill-testing question). Then set `LEGAL_DRAFT=false`.
3. **Get a lawyer's review** of the rules, privacy policy and code of conduct. Points worth asking about: contest rules for entry-fee contests and Quebec; prize disclosure when the pool varies with entries; and the Competition Act's rules on advertising claims.
4. **Only publish claims you can back up.** Before launch, confirm each of these is true or soften it:
   - Mentors from "top companies in different industries": have them confirmed, and don't name a company without its permission.
   - "Verified credential", "hiring partners" and "companies join Deadlock" statements.
   - "Hundreds of builders work on it" in the For companies section.
   - Anything saying real organizations will provide briefs. The briefs on the site are labelled as examples.
5. **Get permission in writing** before profiling a builder in The Deadlock 10 or posting about them on LinkedIn. A short consent form that says where and how long, and lets them withdraw, is enough.

## Email rules (every email you send)

- Only send to people who ticked the consent box on your Tally form. Don't import other lists.
- Say who it's from: your legal name, your postal address and a working contact email or website.
- Include a working unsubscribe link in each message, and honour it within 10 business days (do it the same day if you can).
- Use an honest subject line and "from" name.
- Keep the consent record (the Tally export) and an unsubscribe log for at least three years.
- Footer to paste into every email:

  > You're getting this because you registered your interest in Deadlock and agreed to hear from us. Deadlock, [legal entity], [mailing address], [contact email]. [Unsubscribe]({{unsubscribe_url}})

## If you add these later

- **User uploads or comments on the site:** register a DMCA designated agent with the US Copyright Office (a small fee, renewed every three years), publish the agent's details on the site, and add a takedown process. Canada's notice-and-notice rules also apply.
- **Analytics:** choose a cookieless tool, add its domain to the CSP in `netlify.toml`, and update the privacy policy and footer. Never add session recording on pages with forms.
- **Paid entries again:** set `PAYMENT_LINK_URL`, create the payment link with `scripts/create_payment_link.py`, and bring the Enter buttons back deliberately. The Stripe terms and refund text already match the rules.
- **Web fonts from a CDN:** don't. Keep fonts in `app/static/fonts`.
